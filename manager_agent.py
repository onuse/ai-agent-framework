import ollama
import json
from typing import List, Dict, Any, Optional
from task_queue import TaskQueue, TaskStatus
from project_planner import ProjectPlanner

class ManagerAgent:
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.task_queue = TaskQueue()
        self.project_planner = ProjectPlanner(model_name)
        self.active_project_plans = {}  # Store project plans by project_id
    
    def create_project(self, project_name: str, objective: str) -> str:
        """Create a new project with intelligent planning-first approach."""
        
        print(f"[MANAGER] Creating project: {project_name}")
        print(f"[MANAGER] Objective: {objective}")
        
        # Create project in task queue
        project_id = self.task_queue.create_project(project_name, objective)
        
        # Phase 1: Create comprehensive project plan
        print(f"\n[MANAGER] Phase 1: Creating project plan...")
        project_plan = self.project_planner.create_project_plan(objective)
        
        # Store the plan for this project
        self.active_project_plans[project_id] = project_plan
        
        # Phase 2: Generate initial batch of tasks from the plan
        print(f"\n[MANAGER] Phase 2: Generating initial tasks...")
        self._generate_tasks_from_plan(project_id, project_plan)
        
        return project_id
    
    def _generate_tasks_from_plan(self, project_id: str, project_plan: Dict[str, Any], max_tasks: int = 3):
        """Generate the next batch of tasks from the project plan."""
        
        # Get next ready tasks from the plan
        next_tasks = self.project_planner.get_next_tasks_from_plan(project_plan, max_tasks)
        
        if not next_tasks:
            print(f"[MANAGER] No ready tasks found in plan")
            return
        
        print(f"[MANAGER] Adding {len(next_tasks)} tasks to queue")
        
        # Add tasks to queue with proper metadata
        for task_data in next_tasks:
            # Convert plan task to queue task
            queue_task_data = {
                'deliverable': task_data.get('deliverable', 'Implementation'),
                'project_id': project_id,
                'domain': task_data.get('domain', 'code'),
                'objective': project_plan['metadata']['objective'],
                'task_type': 'planned',
                'plan_task_id': task_data.get('id'),
                'estimated_effort': task_data.get('estimated_effort', 'Medium'),
                'dependencies': task_data.get('dependencies', [])
            }
            
            task_id = self.task_queue.add_task(
                title=task_data['title'],
                description=task_data['description'],
                subtask_data=queue_task_data,
                priority=task_data.get('priority', 5)
            )
            
            print(f"[MANAGER] Added task: {task_data['title']}")
    
    def on_task_completed(self, project_id: str, completed_task: Dict[str, Any]) -> bool:
        """Handle task completion and generate next tasks if needed."""
        
        if project_id not in self.active_project_plans:
            print(f"[MANAGER] No active plan found for project {project_id}")
            return False
        
        project_plan = self.active_project_plans[project_id]
        
        # Mark task as completed in the plan
        plan_task_id = completed_task.get('subtask_data', {}).get('plan_task_id')
        if plan_task_id:
            project_plan = self.project_planner.mark_task_completed(project_plan, plan_task_id)
            self.active_project_plans[project_id] = project_plan
            
            print(f"[MANAGER] Marked plan task {plan_task_id} as completed")
        
        # Check if we need to generate more tasks
        current_phase = project_plan.get('execution_metadata', {}).get('current_phase', 'development')
        print(f"[MANAGER] Project phase: {current_phase}")
        
        # Generate next batch of tasks if not complete
        if not self.project_planner.is_plan_complete(project_plan):
            pending_tasks = self.task_queue.get_task_count_by_status().get('pending', 0)
            
            # If we're running low on pending tasks, generate more
            if pending_tasks <= 1:
                print(f"[MANAGER] Generating next batch of tasks...")
                self._generate_tasks_from_plan(project_id, project_plan)
                return True
        else:
            print(f"[MANAGER] Project plan completed!")
            self.task_queue.update_project_phase(project_id, "completed")
        
        return False
    
    def evaluate_progress(self, project_id: str) -> Dict[str, Any]:
        """Evaluate current project progress using the project plan."""
        
        project_state = self.task_queue.get_project_state(project_id)
        if not project_state:
            return {"error": "Project not found"}
        
        # Get task completion statistics
        completed_tasks = self.task_queue.get_completed_tasks()
        task_counts = self.task_queue.get_task_count_by_status()
        
        # Get project plan if available
        project_plan = self.active_project_plans.get(project_id)
        
        if project_plan:
            # Plan-based evaluation
            total_planned_tasks = project_plan['task_breakdown'].get('estimated_tasks', 0)
            completed_planned_tasks = len(project_plan.get('execution_metadata', {}).get('completed_tasks', []))
            
            completion_percentage = (completed_planned_tasks / total_planned_tasks * 100) if total_planned_tasks > 0 else 0
            current_phase = project_plan.get('execution_metadata', {}).get('current_phase', 'planning')
            
            # Determine status based on plan progress
            if self.project_planner.is_plan_complete(project_plan):
                status = "ready_for_validation"
            elif completion_percentage >= 80:
                status = "finalization"
            elif completion_percentage >= 50:
                status = "integration"
            else:
                status = "development"
            
            return {
                "status": status,
                "completion_percentage": completion_percentage,
                "assessment": f"Completed {completed_planned_tasks}/{total_planned_tasks} planned tasks",
                "current_phase": current_phase,
                "plan_available": True,
                "next_actions": self._get_next_actions_from_plan(project_plan),
                "estimated_tasks_remaining": total_planned_tasks - completed_planned_tasks
            }
        else:
            # Fallback to old evaluation method
            pending_tasks = task_counts.get('pending', 0)
            completed_count = task_counts.get('completed', 0)
            failed_count = task_counts.get('failed', 0)
            
            total_tasks = pending_tasks + completed_count + failed_count
            completion_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
            
            if pending_tasks == 0 and completed_count > 0:
                status = "ready_for_validation"
            elif completion_percentage >= 50:
                status = "development"
            else:
                status = "planning"
            
            return {
                "status": status,
                "completion_percentage": completion_percentage,
                "assessment": f"Completed {completed_count} tasks, {pending_tasks} remaining",
                "current_phase": "unknown",
                "plan_available": False,
                "next_actions": ["Continue with pending tasks"]
            }
    
    def _get_next_actions_from_plan(self, project_plan: Dict[str, Any]) -> List[str]:
        """Get next recommended actions based on project plan."""
        
        current_phase = project_plan.get('execution_metadata', {}).get('current_phase', 'planning')
        
        if current_phase == 'completed':
            return ["Perform final validation and user testing"]
        elif current_phase == 'finalization':
            return ["Complete remaining tasks", "Prepare for integration testing"]
        elif current_phase == 'integration':
            return ["Focus on component integration", "Test inter-component communication"]
        elif current_phase == 'development':
            return ["Continue core development tasks", "Monitor dependencies"]
        else:
            return ["Execute planned tasks"]
    
    def get_project_plan(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get the project plan for a given project."""
        return self.active_project_plans.get(project_id)
    
    def adapt_project_plan(self, project_id: str, completed_task_results: List[Dict[str, Any]]) -> bool:
        """Adapt project plan based on actual progress and discoveries."""
        
        if project_id not in self.active_project_plans:
            return False
        
        project_plan = self.active_project_plans[project_id]
        
        # Use project planner to adapt the plan
        adapted_plan = self.project_planner.adapt_plan_based_on_progress(
            project_plan, 
            completed_task_results
        )
        
        # If plan was modified, generate new tasks
        if adapted_plan != project_plan:
            self.active_project_plans[project_id] = adapted_plan
            print(f"[MANAGER] Project plan adapted based on progress")
            
            # Generate any new tasks from the adapted plan
            self._generate_tasks_from_plan(project_id, adapted_plan)
            return True
        
        return False
    
    def generate_improvement_tasks_from_validation(self, project_id: str, objective: str, validation_report: Dict[str, Any]) -> List[str]:
        """Generate specific improvement tasks based on user perspective validation."""
        
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
    
    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of project status including plan information."""
        
        project_state = self.task_queue.get_project_state(project_id)
        if not project_state:
            return {"error": "Project not found"}
        
        task_counts = self.task_queue.get_task_count_by_status()
        completed_tasks = self.task_queue.get_completed_tasks()
        
        # Include project plan information if available
        project_plan = self.active_project_plans.get(project_id)
        plan_info = {}
        
        if project_plan:
            execution_meta = project_plan.get('execution_metadata', {})
            plan_info = {
                'total_planned_tasks': project_plan['task_breakdown'].get('estimated_tasks', 0),
                'completed_planned_tasks': len(execution_meta.get('completed_tasks', [])),
                'current_phase': execution_meta.get('current_phase', 'unknown'),
                'complexity_score': project_plan.get('metadata', {}).get('complexity_assessment', {}).get('complexity_score', 0),
                'primary_domain': project_plan.get('project_summary', {}).get('primary_domain', 'unknown'),
                'programming_languages': project_plan.get('project_summary', {}).get('programming_languages', [])
            }
        
        summary = {
            "project_name": project_state['project_name'],
            "objective": project_state['objective'],
            "current_phase": project_state['current_phase'],
            "task_counts": task_counts,
            "completed_tasks": len(completed_tasks),
            "latest_metadata": project_state.get('metadata', {}),
            "plan_info": plan_info
        }
        
        return summary
    
    def show_project_plan_status(self, project_id: str):
        """Display detailed project plan status."""
        
        project_plan = self.active_project_plans.get(project_id)
        if not project_plan:
            print(f"[MANAGER] No project plan found for project {project_id}")
            return
        
        print(f"\n📋 PROJECT PLAN STATUS")
        print("="*50)
        
        # Plan metadata
        metadata = project_plan.get('metadata', {})
        complexity = metadata.get('complexity_assessment', {})
        
        print(f"🎯 Objective: {metadata.get('objective', 'Unknown')}")
        print(f"📊 Complexity: {complexity.get('complexity_level', 'unknown')} ({complexity.get('complexity_score', 0)}/10)")
        print(f"💻 Primary Domain: {project_plan.get('project_summary', {}).get('primary_domain', 'unknown')}")
        
        # Task progress
        execution_meta = project_plan.get('execution_metadata', {})
        total_tasks = project_plan['task_breakdown'].get('estimated_tasks', 0)
        completed_tasks = len(execution_meta.get('completed_tasks', []))
        current_phase = execution_meta.get('current_phase', 'planning')
        
        print(f"✅ Progress: {completed_tasks}/{total_tasks} tasks completed")
        print(f"🚧 Current Phase: {current_phase}")
        
        # Show next ready tasks
        next_tasks = self.project_planner.get_next_tasks_from_plan(project_plan, 5)
        if next_tasks:
            print(f"\n📝 Next Ready Tasks:")
            for i, task in enumerate(next_tasks, 1):
                print(f"  {i}. {task['title']} (Priority: {task.get('priority', 5)})")
        else:
            print(f"\n✨ All tasks completed or no ready tasks available")
        
        # Show phases
        phases = project_plan['task_breakdown'].get('execution_phases', [])
        if phases:
            print(f"\n🔄 Execution Phases:")
            for phase in phases:
                phase_tasks = phase.get('tasks', [])
                completed_in_phase = sum(1 for task_id in phase_tasks if task_id in execution_meta.get('completed_tasks', []))
                print(f"  📁 {phase['phase']}: {completed_in_phase}/{len(phase_tasks)} tasks")
                print(f"     {phase.get('description', 'No description')}")

# Legacy methods for backward compatibility
    def generate_additional_tasks(self, project_id: str, evaluation: Dict[str, Any]):
        """Legacy method - now uses plan-based task generation."""
        
        if project_id in self.active_project_plans:
            print("[MANAGER] Using plan-based task generation instead of legacy method")
            project_plan = self.active_project_plans[project_id]
            self._generate_tasks_from_plan(project_id, project_plan)
        else:
            print("[MANAGER] No project plan available - cannot generate additional tasks")
    
    def _classify_objective_domain(self, objective: str) -> Dict[str, Any]:
        """Legacy method - now handled by project planner."""
        
        objective_lower = objective.lower()
        
        # Simple classification for backward compatibility
        if any(word in objective_lower for word in ['write', 'story', 'poem', 'creative']):
            return {'domain': 'creative', 'intent': 'Create written content'}
        elif any(word in objective_lower for word in ['game', 'play', 'player']):
            return {'domain': 'game', 'intent': 'Create interactive game'}
        else:
            return {'domain': 'code', 'intent': 'Build software application'}