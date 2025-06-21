import ollama
import json
from typing import List, Dict, Any, Optional
from task_queue import TaskQueue, TaskStatus

class ManagerAgent:
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.task_queue = TaskQueue()
    
    def create_project(self, project_name: str, objective: str) -> str:
        """Create a new project and generate initial task breakdown."""
        project_id = self.task_queue.create_project(project_name, objective)
        
        # Generate initial task breakdown
        self._generate_task_breakdown(project_id, objective)
        
        return project_id
    
    def _generate_task_breakdown(self, project_id: str, objective: str):
        """Use LLM to break down the objective into manageable subtasks."""
        
        prompt = f"""You are a project manager AI tasked with breaking down a software development objective into manageable subtasks.

OBJECTIVE: {objective}

Break this down into 3-5 specific, actionable subtasks. Each subtask should be:
1. Clearly defined and measurable
2. Implementable by a Python developer
3. Building towards the final objective
4. Ordered logically (dependencies considered)

For each subtask, provide:
- title: Brief descriptive title
- description: Detailed description of what needs to be done
- deliverable: What specific output is expected
- dependencies: Which previous subtasks (if any) this depends on

Respond in JSON format:
{{
    "subtasks": [
        {{
            "title": "Task title",
            "description": "Detailed description",
            "deliverable": "Expected output",
            "dependencies": ["previous_task_title"]
        }}
    ]
}}

Focus on creating a working prototype first, then iterating to add features."""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the JSON response
            content = response['message']['content']
            
            # Extract JSON from the response (handle cases where LLM adds extra text)
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                task_data = json.loads(json_content)
                
                # Add tasks to queue
                for i, subtask in enumerate(task_data['subtasks']):
                    self.task_queue.add_task(
                        title=subtask['title'],
                        description=subtask['description'],
                        subtask_data={
                            'deliverable': subtask['deliverable'],
                            'dependencies': subtask.get('dependencies', []),
                            'project_id': project_id
                        },
                        priority=len(task_data['subtasks']) - i  # Higher priority for earlier tasks
                    )
                
                print(f"Created {len(task_data['subtasks'])} subtasks for project {project_id}")
                
        except Exception as e:
            print(f"Error generating task breakdown: {e}")
            # Fallback: create a simple task
            self.task_queue.add_task(
                title="Manual Planning Required",
                description=f"Manually plan and implement: {objective}",
                subtask_data={'deliverable': 'Working implementation', 'project_id': project_id}
            )
    
    def evaluate_progress(self, project_id: str) -> Dict[str, Any]:
        """Evaluate current project progress and determine next actions."""
        
        project_state = self.task_queue.get_project_state(project_id)
        if not project_state:
            return {"error": "Project not found"}
        
        completed_tasks = self.task_queue.get_completed_tasks()
        task_counts = self.task_queue.get_task_count_by_status()
        
        # Get completed task results for evaluation
        completed_results = []
        for task in completed_tasks:
            if task['result']:
                completed_results.append({
                    'title': task['title'],
                    'description': task['description'],
                    'result': task['result']
                })
        
        if not completed_results:
            return {
                "status": "in_progress",
                "message": "No completed tasks to evaluate yet",
                "pending_tasks": task_counts.get('pending', 0)
            }
        
        # Use LLM to evaluate progress
        prompt = f"""You are evaluating the progress of a software development project.

PROJECT OBJECTIVE: {project_state['objective']}
CURRENT PHASE: {project_state['current_phase']}

COMPLETED TASKS:
{json.dumps(completed_results, indent=2)}

TASK STATUS:
- Pending: {task_counts.get('pending', 0)}
- Completed: {task_counts.get('completed', 0)}
- Failed: {task_counts.get('failed', 0)}

Evaluate the current progress and provide:
1. Overall project status (planning/development/testing/complete)
2. Quality assessment of completed work
3. Whether additional tasks are needed
4. Next recommended actions

Respond in JSON format:
{{
    "status": "planning|development|testing|complete",
    "quality_score": 1-10,
    "assessment": "Brief assessment of progress",
    "needs_additional_tasks": true/false,
    "next_actions": ["action1", "action2"],
    "completion_percentage": 0-100
}}"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                evaluation = json.loads(json_content)
                
                # Update project phase if needed
                if evaluation.get('status') != project_state['current_phase']:
                    self.task_queue.update_project_phase(
                        project_id, 
                        evaluation['status'], 
                        evaluation
                    )
                
                return evaluation
                
        except Exception as e:
            print(f"Error evaluating progress: {e}")
            return {
                "status": "error",
                "message": f"Evaluation failed: {e}",
                "pending_tasks": task_counts.get('pending', 0)
            }
    
    def generate_additional_tasks(self, project_id: str, evaluation: Dict[str, Any]):
        """Generate additional tasks based on evaluation results."""
        
        if not evaluation.get('needs_additional_tasks', False):
            return
        
        project_state = self.task_queue.get_project_state(project_id)
        completed_tasks = self.task_queue.get_completed_tasks()
        
        prompt = f"""Based on the project evaluation, generate additional tasks needed to complete the objective.

PROJECT OBJECTIVE: {project_state['objective']}
CURRENT STATUS: {evaluation.get('status', 'unknown')}
ASSESSMENT: {evaluation.get('assessment', '')}
NEXT ACTIONS: {evaluation.get('next_actions', [])}

COMPLETED WORK:
{json.dumps([{'title': t['title'], 'result': t['result']} for t in completed_tasks], indent=2)}

Generate 1-3 additional specific tasks that address the next actions and move the project forward.

Respond in JSON format:
{{
    "additional_tasks": [
        {{
            "title": "Task title",
            "description": "Detailed description",
            "deliverable": "Expected output"
        }}
    ]
}}"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                task_data = json.loads(json_content)
                
                for task in task_data.get('additional_tasks', []):
                    self.task_queue.add_task(
                        title=task['title'],
                        description=task['description'],
                        subtask_data={
                            'deliverable': task['deliverable'],
                            'project_id': project_id
                        }
                    )
                
                print(f"Generated {len(task_data.get('additional_tasks', []))} additional tasks")
                
        except Exception as e:
            print(f"Error generating additional tasks: {e}")
    
    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of project status."""
        project_state = self.task_queue.get_project_state(project_id)
        if not project_state:
            return {"error": "Project not found"}
        
        task_counts = self.task_queue.get_task_count_by_status()
        completed_tasks = self.task_queue.get_completed_tasks()
        
        return {
            "project_name": project_state['project_name'],
            "objective": project_state['objective'],
            "current_phase": project_state['current_phase'],
            "task_counts": task_counts,
            "completed_tasks": len(completed_tasks),
            "latest_metadata": project_state.get('metadata', {})
        }