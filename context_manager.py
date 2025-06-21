import json
import os
from typing import Dict, Any, List, Optional
from task_queue import TaskQueue, TaskStatus

class ContextManager:
    """Manages project context and artifact history for better task coordination."""
    
    def __init__(self, artifacts_dir: str = "artifacts"):
        self.artifacts_dir = artifacts_dir
        self.task_queue = TaskQueue()
    
    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive context for a project including all completed work."""
        
        # Get completed tasks with their results
        completed_tasks = self.task_queue.get_completed_tasks()
        project_tasks = []
        
        for task in completed_tasks:
            if task['result']:
                try:
                    result_data = json.loads(task['result'])
                    if result_data.get('code'):
                        project_tasks.append({
                            'title': task['title'],
                            'description': task['description'],
                            'code': result_data['code'],
                            'artifact_path': result_data.get('artifact_path'),
                            'explanation': result_data.get('explanation', ''),
                            'completed_at': task['updated_at']
                        })
                except (json.JSONDecodeError, KeyError):
                    # Skip tasks with malformed results
                    continue
        
        # Get latest artifact files
        artifact_files = self._get_recent_artifacts()
        
        return {
            'completed_tasks': project_tasks,
            'artifact_files': artifact_files,
            'task_count': len(project_tasks),
            'latest_code': self._get_latest_code(project_tasks)
        }
    
    def _get_recent_artifacts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get information about recent artifact files."""
        
        if not os.path.exists(self.artifacts_dir):
            return []
        
        artifacts = []
        for filename in os.listdir(self.artifacts_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(self.artifacts_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Extract metadata from header comments
                    lines = content.split('\n')
                    metadata = {}
                    for line in lines[:10]:  # Check first 10 lines for metadata
                        if line.startswith('Task:'):
                            metadata['task'] = line[5:].strip()
                        elif line.startswith('Description:'):
                            metadata['description'] = line[12:].strip()
                    
                    artifacts.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': len(content),
                        'metadata': metadata,
                        'modified_time': os.path.getmtime(filepath)
                    })
                except Exception:
                    continue
        
        # Sort by modification time, most recent first
        artifacts.sort(key=lambda x: x['modified_time'], reverse=True)
        return artifacts[:limit]
    
    def _get_latest_code(self, completed_tasks: List[Dict[str, Any]]) -> Optional[str]:
        """Get the most recent complete code artifact."""
        
        if not completed_tasks:
            return None
        
        # Return the code from the most recently completed task
        latest_task = completed_tasks[-1]
        return latest_task.get('code')
    
    def generate_context_prompt(self, current_task: Dict[str, Any], project_id: str) -> str:
        """Generate a context-aware prompt for the current task."""
        
        context = self.get_project_context(project_id)
        
        context_prompt = f"""You are working on a software development project. Here's the context of previous work:

CURRENT TASK: {current_task['title']}
TASK DESCRIPTION: {current_task['description']}
EXPECTED DELIVERABLE: {current_task['subtask_data'].get('deliverable', 'Working code')}

PREVIOUS COMPLETED TASKS ({context['task_count']}):
"""
        
        for i, task in enumerate(context['completed_tasks'], 1):
            context_prompt += f"""
{i}. {task['title']}
   - Description: {task['description']}
   - Completed: {task['completed_at']}
"""
            if task.get('explanation'):
                context_prompt += f"   - Implementation: {task['explanation']}\n"
        
        if context['latest_code']:
            context_prompt += f"""
LATEST WORKING CODE:
```python
{context['latest_code']}
```

IMPORTANT: 
- Build upon or modify the existing code above rather than starting from scratch
- Maintain consistency with the existing implementation
- If this is a GUI application, use the SAME geometry manager throughout (don't mix pack/grid/place)
- Preserve working functionality while adding new features
- If the existing code has issues, fix them while adding your functionality
"""
        else:
            context_prompt += """
No previous code found. Create a new implementation from scratch.
"""
        
        context_prompt += """
Your task is to implement the current functionality while maintaining compatibility with existing code.
Provide complete, working Python code that builds upon what's already been created."""
        
        return context_prompt
    
    def should_build_upon_existing(self, current_task: Dict[str, Any], project_id: str) -> bool:
        """Determine if the current task should build upon existing code."""
        
        context = self.get_project_context(project_id)
        
        # If there's existing code and this isn't the first task, build upon it
        if context['latest_code'] and context['task_count'] > 0:
            # Check if the task description suggests modification/extension
            task_desc = current_task['description'].lower()
            modification_keywords = ['implement', 'add', 'extend', 'modify', 'enhance', 'integrate']
            
            return any(keyword in task_desc for keyword in modification_keywords)
        
        return False
    
    def get_code_integration_guidance(self, current_task: Dict[str, Any], project_id: str) -> str:
        """Provide specific guidance for integrating with existing code."""
        
        context = self.get_project_context(project_id)
        
        if not context['latest_code']:
            return "Create new standalone implementation."
        
        # Analyze the existing code for patterns
        existing_code = context['latest_code']
        guidance = []
        
        # Check GUI framework
        if 'tkinter' in existing_code.lower():
            if '.pack(' in existing_code:
                guidance.append("Use .pack() geometry manager to match existing code")
            elif '.grid(' in existing_code:
                guidance.append("Use .grid() geometry manager to match existing code")
            
            if 'class' in existing_code and 'def __init__' in existing_code:
                guidance.append("Extend the existing class rather than creating a new one")
        
        # Check for main execution pattern
        if 'if __name__ == "__main__"' in existing_code:
            guidance.append("Maintain the same main execution pattern")
        
        if guidance:
            return "Integration guidance: " + "; ".join(guidance)
        else:
            return "Extend or modify the existing code structure."