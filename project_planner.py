import ollama
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class ProjectPlanner:
    """Autonomous project planner that creates comprehensive project plans before execution."""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
    
    def create_project_plan(self, objective: str) -> Dict[str, Any]:
        """Create a comprehensive project plan for the given objective."""
        
        print(f"[PLANNER] Creating project plan for: {objective}")
        
        # Assess complexity first
        complexity_assessment = self._assess_objective_complexity(objective)
        print(f"[PLANNER] Complexity: {complexity_assessment.get('complexity_level', 'unknown')} ({complexity_assessment.get('complexity_score', 0)}/10)")
        
        # Generate detailed project plan
        plan_prompt = self._create_planning_prompt(objective, complexity_assessment)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": plan_prompt}]
            )
            
            content = response['message']['content']
            project_plan = self._parse_plan_response(content, objective, complexity_assessment)
            
            # Validate and enhance the plan
            validated_plan = self._validate_and_enhance_plan(project_plan, objective)
            
            print(f"[PLANNER] Generated plan with {validated_plan['estimated_tasks']} tasks")
            return validated_plan
            
        except Exception as e:
            print(f"[PLANNER] Plan generation failed: {e}")
            return self._create_fallback_plan(objective, complexity_assessment)
    
    def _assess_objective_complexity(self, objective: str) -> Dict[str, Any]:
        """Assess the complexity of the objective to guide planning."""
        
        complexity_prompt = f"""You are a project manager assessing the complexity of a software development objective.

OBJECTIVE: "{objective}"

Analyze this objective and rate its complexity on a scale of 1-10, considering:

1. **Technical Complexity**: How many different technologies/domains are involved?
2. **Feature Scope**: How many distinct features or capabilities are needed?
3. **Integration Requirements**: How much coordination between components is needed?
4. **Domain Expertise**: How specialized is the knowledge required?

Respond in JSON format:
{{
    "complexity_score": 1-10,
    "complexity_level": "simple|moderate|complex|very_complex",
    "reasoning": "Brief explanation of complexity factors",
    "key_challenges": ["list", "of", "main", "technical", "challenges"],
    "estimated_duration": "rough time estimate",
    "skill_requirements": ["list", "of", "required", "skills"]
}}

COMPLEXITY GUIDELINES:
- 1-3: Simple scripts, basic tools, single-file programs
- 4-6: Multi-component applications, basic games, data analysis
- 7-8: Complex applications, advanced games, system integrations
- 9-10: Enterprise systems, advanced AI, complex distributed systems"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": complexity_prompt}]
            )
            
            content = response['message']['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                assessment = json.loads(json_content)
                return assessment
            
        except Exception as e:
            print(f"[PLANNER] Complexity assessment failed: {e}")
        
        # Fallback assessment
        return self._fallback_complexity_assessment(objective)
    
    def _create_planning_prompt(self, objective: str, complexity: Dict[str, Any]) -> str:
        """Create comprehensive planning prompt based on complexity."""
        
        complexity_level = complexity.get('complexity_level', 'moderate')
        complexity_score = complexity.get('complexity_score', 5)
        
        prompt = f"""You are a senior technical architect creating a detailed project plan.

OBJECTIVE: "{objective}"
COMPLEXITY: {complexity_level} (score: {complexity_score}/10)
COMPLEXITY FACTORS: {complexity.get('reasoning', 'Standard complexity')}

Create a comprehensive project plan that includes:

1. **TECHNICAL ANALYSIS**
   - Primary domain (code/creative/data/ui/research/game)
   - Programming language(s) needed
   - Key technologies and frameworks
   - Technical architecture overview

2. **TASK BREAKDOWN**
   - Estimated total number of tasks (1-20+ based on complexity)
   - Detailed task list with clear deliverables
   - Task dependencies and execution order
   - Priority levels for each task

3. **PROJECT STRUCTURE**
   - Expected file structure
   - Key components and modules
   - Integration points between components
   - Entry points and user interfaces

4. **SUCCESS CRITERIA**
   - Specific deliverables that define "done"
   - Quality requirements
   - Testing and validation approach

5. **RISK ASSESSMENT**
   - Potential challenges and blockers
   - Mitigation strategies
   - Fallback approaches

Respond in JSON format:
{{
    "project_summary": {{
        "primary_domain": "code|creative|data|ui|research|game",
        "programming_languages": ["list", "of", "languages"],
        "key_technologies": ["list", "of", "technologies"],
        "architecture_overview": "brief technical description"
    }},
    "task_breakdown": {{
        "estimated_tasks": 1-20,
        "tasks": [
            {{
                "id": "task_1",
                "title": "Clear, actionable task title",
                "description": "Detailed description of what to implement",
                "deliverable": "Specific output expected",
                "domain": "task domain",
                "priority": 1-10,
                "dependencies": ["list", "of", "task", "ids"],
                "estimated_effort": "time estimate"
            }}
        ],
        "execution_phases": [
            {{
                "phase": "foundation|development|integration|finalization",
                "tasks": ["task_1", "task_2"],
                "description": "What this phase accomplishes"
            }}
        ]
    }},
    "project_structure": {{
        "expected_files": ["list", "of", "files", "to", "be", "created"],
        "file_organization": "description of folder structure",
        "entry_points": ["main.py", "index.html"],
        "integration_strategy": "how components connect"
    }},
    "success_criteria": {{
        "primary_deliverables": ["list", "of", "main", "outputs"],
        "quality_requirements": ["list", "of", "quality", "standards"],
        "user_experience_goals": ["list", "of", "UX", "objectives"]
    }},
    "risk_assessment": {{
        "potential_challenges": ["list", "of", "risks"],
        "mitigation_strategies": ["list", "of", "solutions"],
        "fallback_plan": "simplified version if needed"
    }}
}}

IMPORTANT GUIDELINES:
- For simple objectives (score 1-3): 1-3 tasks maximum
- For moderate objectives (score 4-6): 3-8 tasks
- For complex objectives (score 7-8): 5-15 tasks  
- For very complex objectives (score 9-10): 10-20 tasks
- Always include clear dependencies between tasks
- Focus on creating WORKING, EXECUTABLE deliverables
- Consider the user's perspective: "Can they actually use this?"

Make the plan specific to THIS objective, not a generic template."""

        return prompt
    
    def _parse_plan_response(self, content: str, objective: str, complexity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the LLM's planning response."""
        
        try:
            # Find JSON in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                plan = json.loads(json_content)
                
                # Add metadata
                plan['metadata'] = {
                    'objective': objective,
                    'complexity_assessment': complexity,
                    'created_at': datetime.now().isoformat(),
                    'planner_version': '1.0'
                }
                
                return plan
            else:
                raise ValueError("No valid JSON found in planning response")
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[PLANNER] Failed to parse plan response: {e}")
            print(f"[PLANNER] Raw response: {content[:500]}...")
            raise
    
    def _validate_and_enhance_plan(self, plan: Dict[str, Any], objective: str) -> Dict[str, Any]:
        """Validate and enhance the project plan."""
        
        # Ensure required fields exist
        if 'task_breakdown' not in plan:
            plan['task_breakdown'] = {'estimated_tasks': 1, 'tasks': []}
        
        tasks = plan['task_breakdown'].get('tasks', [])
        estimated_tasks = plan['task_breakdown'].get('estimated_tasks', len(tasks))
        
        # Validate task count makes sense
        if estimated_tasks != len(tasks):
            print(f"[PLANNER] Task count mismatch: estimated {estimated_tasks}, actual {len(tasks)}")
            plan['task_breakdown']['estimated_tasks'] = len(tasks)
        
        # Ensure tasks have required fields
        for i, task in enumerate(tasks):
            if 'id' not in task:
                task['id'] = f"task_{i+1}"
            if 'priority' not in task:
                task['priority'] = 5
            if 'dependencies' not in task:
                task['dependencies'] = []
            if 'domain' not in task:
                task['domain'] = plan.get('project_summary', {}).get('primary_domain', 'code')
        
        # Add execution metadata
        plan['execution_metadata'] = {
            'next_task_index': 0,
            'completed_tasks': [],
            'current_phase': 'planning_complete',
            'adaptive_planning_enabled': True
        }
        
        return plan
    
    def _fallback_complexity_assessment(self, objective: str) -> Dict[str, Any]:
        """Simple fallback complexity assessment."""
        
        objective_lower = objective.lower()
        
        # Simple heuristics
        if any(word in objective_lower for word in ['simple', 'basic', 'hello', 'calculator']):
            complexity_score = 2
            level = 'simple'
        elif any(word in objective_lower for word in ['game', 'web', 'app', 'system']):
            complexity_score = 6
            level = 'moderate'
        elif any(word in objective_lower for word in ['complex', 'advanced', 'enterprise']):
            complexity_score = 8
            level = 'complex'
        else:
            complexity_score = 4
            level = 'moderate'
        
        return {
            'complexity_score': complexity_score,
            'complexity_level': level,
            'reasoning': 'Fallback heuristic assessment',
            'key_challenges': ['Implementation complexity'],
            'estimated_duration': 'Unknown',
            'skill_requirements': ['Programming']
        }
    
    def _create_fallback_plan(self, objective: str, complexity: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple fallback plan if LLM planning fails."""
        
        complexity_score = complexity.get('complexity_score', 5)
        
        # Determine number of tasks based on complexity
        if complexity_score <= 3:
            num_tasks = 1
        elif complexity_score <= 6:
            num_tasks = 3
        else:
            num_tasks = 5
        
        # Create basic tasks
        tasks = []
        for i in range(num_tasks):
            if i == 0:
                title = f"Implement Core Functionality for {objective}"
                description = f"Create the main implementation for: {objective}"
            elif i == 1:
                title = f"Add User Interface and Interaction"
                description = f"Create user interface and interaction for: {objective}"
            elif i == 2:
                title = f"Integrate and Test Components"
                description = f"Integrate all components and ensure they work together"
            else:
                title = f"Enhance and Polish (Phase {i-2})"
                description = f"Add enhancements and polish to the implementation"
            
            tasks.append({
                'id': f"task_{i+1}",
                'title': title,
                'description': description,
                'deliverable': 'Working implementation',
                'domain': 'code',
                'priority': 10 - i,
                'dependencies': [f"task_{i}"] if i > 0 else [],
                'estimated_effort': 'Medium'
            })
        
        return {
            'project_summary': {
                'primary_domain': 'code',
                'programming_languages': ['python'],
                'key_technologies': ['standard libraries'],
                'architecture_overview': 'Standard implementation approach'
            },
            'task_breakdown': {
                'estimated_tasks': num_tasks,
                'tasks': tasks,
                'execution_phases': [
                    {
                        'phase': 'development',
                        'tasks': [task['id'] for task in tasks],
                        'description': 'Main development phase'
                    }
                ]
            },
            'project_structure': {
                'expected_files': ['main.py'],
                'file_organization': 'Single directory structure',
                'entry_points': ['main.py'],
                'integration_strategy': 'Monolithic approach'
            },
            'success_criteria': {
                'primary_deliverables': ['Working implementation'],
                'quality_requirements': ['Functional', 'Error-free'],
                'user_experience_goals': ['Easy to use']
            },
            'risk_assessment': {
                'potential_challenges': ['Implementation complexity'],
                'mitigation_strategies': ['Iterative development'],
                'fallback_plan': 'Simplified version'
            },
            'metadata': {
                'objective': objective,
                'complexity_assessment': complexity,
                'created_at': datetime.now().isoformat(),
                'planner_version': '1.0',
                'fallback_plan': True
            },
            'execution_metadata': {
                'next_task_index': 0,
                'completed_tasks': [],
                'current_phase': 'planning_complete',
                'adaptive_planning_enabled': True
            }
        }
    
    def get_next_tasks_from_plan(self, project_plan: Dict[str, Any], max_tasks: int = 3) -> List[Dict[str, Any]]:
        """Get the next batch of tasks from the project plan based on dependencies."""
        
        if not project_plan or 'task_breakdown' not in project_plan:
            return []
        
        all_tasks = project_plan['task_breakdown'].get('tasks', [])
        execution_meta = project_plan.get('execution_metadata', {})
        completed_task_ids = set(execution_meta.get('completed_tasks', []))
        
        # Find tasks that are ready to execute (dependencies completed)
        ready_tasks = []
        
        for task in all_tasks:
            task_id = task.get('id')
            
            # Skip if already completed
            if task_id in completed_task_ids:
                continue
            
            # Check if dependencies are satisfied
            dependencies = task.get('dependencies', [])
            dependencies_satisfied = all(dep_id in completed_task_ids for dep_id in dependencies)
            
            if dependencies_satisfied:
                ready_tasks.append(task)
        
        # Sort by priority (higher priority first)
        ready_tasks.sort(key=lambda t: t.get('priority', 5), reverse=True)
        
        # Return up to max_tasks
        return ready_tasks[:max_tasks]
    
    def mark_task_completed(self, project_plan: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Mark a task as completed in the project plan."""
        
        if 'execution_metadata' not in project_plan:
            project_plan['execution_metadata'] = {
                'completed_tasks': [],
                'current_phase': 'execution'
            }
        
        completed_tasks = project_plan['execution_metadata'].get('completed_tasks', [])
        if task_id not in completed_tasks:
            completed_tasks.append(task_id)
            project_plan['execution_metadata']['completed_tasks'] = completed_tasks
        
        # Update current phase if needed
        total_tasks = project_plan['task_breakdown'].get('estimated_tasks', 0)
        completed_count = len(completed_tasks)
        
        if completed_count >= total_tasks:
            project_plan['execution_metadata']['current_phase'] = 'completed'
        elif completed_count >= total_tasks * 0.8:
            project_plan['execution_metadata']['current_phase'] = 'finalization'
        elif completed_count >= total_tasks * 0.5:
            project_plan['execution_metadata']['current_phase'] = 'integration'
        else:
            project_plan['execution_metadata']['current_phase'] = 'development'
        
        return project_plan
    
    def is_plan_complete(self, project_plan: Dict[str, Any]) -> bool:
        """Check if all tasks in the plan are completed."""
        
        if not project_plan or 'task_breakdown' not in project_plan:
            return True
        
        all_tasks = project_plan['task_breakdown'].get('tasks', [])
        execution_meta = project_plan.get('execution_metadata', {})
        completed_tasks = execution_meta.get('completed_tasks', [])
        
        return len(completed_tasks) >= len(all_tasks)
    
    def adapt_plan_based_on_progress(self, project_plan: Dict[str, Any], completed_task_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Adapt the project plan based on actual progress and discoveries."""
        
        # This would analyze completed task results and potentially:
        # 1. Add new tasks if gaps are discovered
        # 2. Remove tasks if they're no longer needed
        # 3. Modify remaining tasks based on what was actually built
        # 4. Update dependencies based on new understanding
        
        # For now, return the plan unchanged
        # In a future version, this could use LLM to analyze progress and adapt
        
        return project_plan