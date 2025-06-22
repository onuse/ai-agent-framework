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
        self._generate_focused_task_breakdown(project_id, objective)
        
        return project_id
    
    def _generate_focused_task_breakdown(self, project_id: str, objective: str):
        """Generate focused, executable tasks that match the objective domain."""
        
        # First, classify the objective to understand what domain we're working in
        domain_classification = self._classify_objective_domain(objective)
        
        prompt = f"""You are a project manager creating a focused task breakdown for a specific objective.

OBJECTIVE: {objective}
DOMAIN: {domain_classification['domain']}
INTENT: {domain_classification['intent']}

Create 2-3 FOCUSED, EXECUTABLE tasks that directly achieve this objective. Each task should:
1. Be immediately actionable and specific
2. Use only standard Python libraries (no external dependencies)
3. Build directly toward the stated objective
4. Be completable in isolation
5. Match the domain and intent of the objective

DOMAIN-SPECIFIC GUIDELINES:
- CODE: Create working Python scripts with sample data, no external imports
- CREATIVE: Write actual content (stories, poems, etc.), not code about writing
- DATA: Use built-in Python for analysis, create sample datasets
- GAME: Build simple text-based or console games using only standard libraries
- UI: Create simple text-based interfaces or basic tkinter (if GUI needed)
- RESEARCH: Write actual research documents, not tools for research

For "{objective}", focus on the ACTUAL DELIVERABLE, not supporting infrastructure.

Respond in JSON format:
{{
    "subtasks": [
        {{
            "title": "Direct, actionable task title",
            "description": "Specific description of what to implement/create",
            "deliverable": "Exact output expected"
        }}
    ]
}}

IMPORTANT: 
- For creative writing → tasks should CREATE the writing, not code
- For data analysis → tasks should ANALYZE data, not just prepare tools
- For games → tasks should CREATE playable games, not just engines
- For simple objectives → 1-2 tasks maximum, keep it focused"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the JSON response
            content = response['message']['content']
            
            # Extract JSON from the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                task_data = json.loads(json_content)
                
                # Add tasks to queue with high priority (newest first)
                for i, subtask in enumerate(task_data['subtasks']):
                    self.task_queue.add_task(
                        title=subtask['title'],
                        description=subtask['description'],
                        subtask_data={
                            'deliverable': subtask['deliverable'],
                            'project_id': project_id,
                            'domain': domain_classification['domain'],
                            'objective': objective
                        },
                        priority=len(task_data['subtasks']) - i  # Higher priority for earlier tasks
                    )
                
                print(f"Created {len(task_data['subtasks'])} focused subtasks for {domain_classification['domain']} objective")
                
        except Exception as e:
            print(f"Error generating task breakdown: {e}")
            # Fallback: create a single, direct task
            self.task_queue.add_task(
                title=f"Complete: {objective}",
                description=f"Directly implement or create: {objective}",
                subtask_data={
                    'deliverable': 'Direct implementation of the objective', 
                    'project_id': project_id,
                    'domain': domain_classification['domain'],
                    'objective': objective
                }
            )
    
    def _classify_objective_domain(self, objective: str) -> Dict[str, Any]:
        """Quickly classify the objective to understand the domain and intent."""
        
        objective_lower = objective.lower()
        
        # Simple classification based on key indicators
        if any(word in objective_lower for word in ['write', 'story', 'poem', 'creative', 'novel', 'tale']):
            return {
                'domain': 'creative',
                'intent': 'Create written content/literature'
            }
        elif any(word in objective_lower for word in ['analyze', 'data', 'chart', 'graph', 'statistics', 'csv']):
            return {
                'domain': 'data', 
                'intent': 'Perform data analysis or visualization'
            }
        elif any(word in objective_lower for word in ['game', 'play', 'player', 'level', 'arcade', 'puzzle']):
            return {
                'domain': 'game',
                'intent': 'Create interactive game or entertainment'
            }
        elif any(word in objective_lower for word in ['interface', 'ui', 'form', 'button', 'gui', 'design']):
            return {
                'domain': 'ui',
                'intent': 'Create user interface or interaction design'
            }
        elif any(word in objective_lower for word in ['research', 'investigate', 'study', 'report', 'document']):
            return {
                'domain': 'research',
                'intent': 'Create research content or documentation'
            }
        else:
            return {
                'domain': 'code',
                'intent': 'Build software application or script'
            }
    
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
        
        # Simple evaluation based on task completion
        pending_tasks = task_counts.get('pending', 0)
        completed_count = task_counts.get('completed', 0)
        failed_count = task_counts.get('failed', 0)
        
        total_tasks = pending_tasks + completed_count + failed_count
        completion_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # Determine status
        if pending_tasks == 0 and completed_count > 0:
            status = "complete"
        elif completion_percentage >= 50:
            status = "development"
        else:
            status = "planning"
        
        return {
            "status": status,
            "completion_percentage": completion_percentage,
            "assessment": f"Completed {completed_count} tasks, {pending_tasks} remaining",
            "needs_additional_tasks": False,  # Keep it simple
            "next_actions": ["Continue with pending tasks"] if pending_tasks > 0 else ["Project complete"]
        }
    
    def perform_final_project_validation(self, project_id: str, objective: str) -> Dict[str, Any]:
        """Perform comprehensive final validation when project is complete."""
        
        from project_completeness_agent import ProjectCompletenessAgent
        
        completeness_agent = ProjectCompletenessAgent(self.model_name)
        return completeness_agent.perform_final_validation(project_id, objective)
    
    def generate_additional_tasks(self, project_id: str, evaluation: Dict[str, Any]):
        """Generate additional tasks based on evaluation results."""
        
        # For now, avoid generating additional tasks to keep things simple
        # This was causing the framework to generate too many unnecessary tasks
        print("[MANAGER] Skipping additional task generation to keep project focused")
        pass
    
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