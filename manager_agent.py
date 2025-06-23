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
                            'objective': objective,
                            'task_type': 'initial'
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
                    'objective': objective,
                    'task_type': 'initial'
                }
            )
    
    def generate_improvement_tasks_from_validation(self, project_id: str, objective: str, validation_report: Dict[str, Any]) -> List[str]:
        """NEW: Generate specific improvement tasks based on user perspective validation."""
        
        user_perspective = validation_report.get('user_satisfaction', {})
        
        if not user_perspective.get('applicable', True):
            print("[MANAGER] No user perspective data available for improvement")
            return []
        
        satisfaction_score = user_perspective.get('satisfaction_score', 5)
        
        # Only generate improvement tasks if user satisfaction is low
        if satisfaction_score >= 7:
            print(f"[MANAGER] User satisfaction ({satisfaction_score}/10) is acceptable - no improvement needed")
            return []
        
        print(f"[MANAGER] User satisfaction ({satisfaction_score}/10) is low - generating improvement tasks")
        
        # Create improvement prompt based on validation results
        improvement_prompt = self._create_improvement_prompt(objective, validation_report)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": improvement_prompt}]
            )
            
            content = response['message']['content']
            
            # Parse improvement tasks
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                improvement_data = json.loads(json_content)
                
                # Create improvement tasks with high priority
                improvement_task_ids = []
                for i, task in enumerate(improvement_data.get('improvement_tasks', [])):
                    task_id = self.task_queue.add_task(
                        title=task['title'],
                        description=task['description'],
                        subtask_data={
                            'deliverable': task['deliverable'],
                            'project_id': project_id,
                            'domain': task.get('domain', 'code'),
                            'objective': objective,
                            'task_type': 'improvement',
                            'addresses_issue': task.get('addresses_issue', 'user_satisfaction')
                        },
                        priority=100 + i  # Very high priority for improvement tasks
                    )
                    improvement_task_ids.append(task_id)
                
                print(f"[MANAGER] Generated {len(improvement_task_ids)} improvement tasks")
                return improvement_task_ids
                
        except Exception as e:
            print(f"[MANAGER] Error generating improvement tasks: {e}")
            # Fallback: create a generic integration task
            fallback_task_id = self.task_queue.add_task(
                title="Fix User Experience Issues",
                description=f"Address the issues preventing users from successfully using: {objective}",
                subtask_data={
                    'deliverable': 'Working, user-friendly implementation',
                    'project_id': project_id,
                    'domain': 'code',
                    'objective': objective,
                    'task_type': 'improvement',
                    'addresses_issue': 'general_usability'
                },
                priority=100
            )
            return [fallback_task_id]
        
        return []
    
    def _create_improvement_prompt(self, objective: str, validation_report: Dict[str, Any]) -> str:
        """Create targeted improvement prompt based on validation results."""
        
        user_perspective = validation_report.get('user_satisfaction', {})
        artifacts = validation_report.get('artifacts', [])
        
        # Build context about current state
        current_files = []
        for artifact in artifacts:
            current_files.append(f"- {artifact['name']} ({artifact['type']}, {artifact['size']} bytes)")
        
        files_context = "\n".join(current_files) if current_files else "No files found"
        
        # Extract key issues
        major_gaps = user_perspective.get('major_gaps', [])
        biggest_problem = user_perspective.get('the_one_biggest_problem', 'Unknown issue')
        quick_fix = user_perspective.get('quick_fix_suggestion', 'No suggestion provided')
        first_impression = user_perspective.get('first_impression', 'Unknown')
        clear_entry_point = user_perspective.get('clear_entry_point', False)
        actually_works = user_perspective.get('actually_works', False)
        
        prompt = f"""You are a project manager fixing a deliverable that doesn't meet user expectations.

ORIGINAL OBJECTIVE: {objective}
USER SATISFACTION: {user_perspective.get('satisfaction_score', 5)}/10
USER SATISFIED: {user_perspective.get('user_would_be_satisfied', False)}

CURRENT STATE:
{files_context}

KEY PROBLEMS IDENTIFIED:
- Biggest Problem: {biggest_problem}
- Quick Fix Needed: {quick_fix}
- Clear Entry Point: {clear_entry_point}
- Actually Works: {actually_works}
- First Impression: {first_impression}
- Major Gaps: {', '.join(major_gaps) if major_gaps else 'None specified'}

USER'S HONEST ASSESSMENT: {user_perspective.get('honest_assessment', 'No assessment provided')}

Your job is to create 1-3 specific, targeted improvement tasks that will fix these issues and make the user satisfied.

FOCUS ON:
1. If no clear entry point → Create proper entry point (index.html, main.py, etc.)
2. If files aren't connected → Create integration/initialization code
3. If it doesn't actually work → Fix the core functionality
4. If user can't run it → Add clear run instructions and setup

Create tasks that address the ROOT CAUSE, not symptoms.

Respond in JSON format:
{{
    "improvement_tasks": [
        {{
            "title": "Specific fix task title",
            "description": "Detailed description of what to implement/fix",
            "deliverable": "Exact output that will resolve the issue",
            "addresses_issue": "Which specific problem this solves",
            "domain": "code/creative/data/ui/research/game"
        }}
    ],
    "strategy": "Brief explanation of the improvement approach"
}}

IMPORTANT:
- Focus on making it ACTUALLY WORK for the user
- Address the biggest problem first
- Create working connections between components
- Ensure there's a clear way to run/use the deliverable
- Be specific about what files to create or modify"""

        return prompt
    
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
            status = "ready_for_validation"  # Changed from "complete" to trigger validation
        elif completion_percentage >= 50:
            status = "development"
        else:
            status = "planning"
        
        return {
            "status": status,
            "completion_percentage": completion_percentage,
            "assessment": f"Completed {completed_count} tasks, {pending_tasks} remaining",
            "needs_additional_tasks": False,  # Will be determined by validation
            "next_actions": ["Perform user perspective validation"] if status == "ready_for_validation" else ["Continue with pending tasks"]
        }
    
    def perform_final_project_validation(self, project_id: str, objective: str) -> Dict[str, Any]:
        """Perform comprehensive final validation when project is complete."""
        
        from project_completeness_agent import ProjectCompletenessAgent
        
        completeness_agent = ProjectCompletenessAgent(self.model_name)
        return completeness_agent.perform_final_validation(project_id, objective)
    
    def should_continue_improvement(self, validation_report: Dict[str, Any], improvement_attempt: int, max_attempts: int = 3) -> bool:
        """Determine if we should continue trying to improve the project."""
        
        if improvement_attempt >= max_attempts:
            print(f"[MANAGER] Reached maximum improvement attempts ({max_attempts})")
            return False
        
        user_satisfaction = validation_report.get('user_satisfaction', {})
        satisfaction_score = user_satisfaction.get('satisfaction_score', 5)
        
        # Continue if user satisfaction is below 7/10
        should_continue = satisfaction_score < 7
        
        if should_continue:
            print(f"[MANAGER] User satisfaction ({satisfaction_score}/10) still low - continuing improvement")
        else:
            print(f"[MANAGER] User satisfaction ({satisfaction_score}/10) acceptable - stopping improvement")
        
        return should_continue
    
    def generate_additional_tasks(self, project_id: str, evaluation: Dict[str, Any]):
        """Legacy method - now redirects to improvement task generation."""
        print("[MANAGER] Use generate_improvement_tasks_from_validation() for targeted improvements")
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