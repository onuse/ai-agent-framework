import ollama
import os
import subprocess
import tempfile
import json
import time
from typing import Dict, Any, Optional, Tuple
from task_queue import TaskQueue, TaskStatus
from code_validator import CodeValidator
from context_manager import ContextManager
from task_classifier import TaskClassifier
from robust_solution_creator import RobustSolutionCreator
from multilanguage_solution_creators import MultiLanguageExecutor

class WorkerAgent:
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.task_queue = TaskQueue()
        self.validator = CodeValidator(model_name)
        self.context_manager = ContextManager()
        self.task_classifier = TaskClassifier()
        self.solution_creator = RobustSolutionCreator(model_name)
        self.multilang_executor = MultiLanguageExecutor()
        self.artifacts_dir = "artifacts"
        
        # Create artifacts directory if it doesn't exist
        os.makedirs(self.artifacts_dir, exist_ok=True)
    
    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a single task and return success status."""
        
        task_id = task['id']
        print(f"Starting task: {task['title']}")
        
        # Classify the task
        classification = self.task_classifier.classify_task(task)
        domain = classification['primary_domain']
        confidence = classification['confidence']
        approach = classification['approach']
        
        print(f"[CLASSIFIER] Domain: {domain} (confidence: {confidence:.2f}) - {approach}")
        if classification.get('fallback_reason'):
            print(f"[CLASSIFIER] {classification['fallback_reason']}")
        if classification.get('is_hybrid'):
            print(f"[CLASSIFIER] Hybrid task: {domain} + {classification.get('secondary_domain')}")
        
        # Update task status to in progress
        self.task_queue.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        
        try:
            # Generate solution using domain-specific approach
            solution_result = self._generate_specialized_solution(task, classification)
            
            if not solution_result['success']:
                self.task_queue.update_task_status(
                    task_id, 
                    TaskStatus.FAILED, 
                    error_message=solution_result['error']
                )
                return False
            
            # Apply domain-appropriate validation
            validation_result = self._validate_solution(solution_result, task, domain)
            
            # Use the validated/improved solution
            final_solution = validation_result['final_solution']
            
            print(f"[WORKER] Validation: {'PASSED' if validation_result['validation_passed'] else 'FAILED'}")
            if validation_result['issues_found'] > 0:
                print(f"[WORKER] Issues found: {validation_result['issues_found']}")
            if validation_result['issues_fixed']:
                print(f"[WORKER] Solution was automatically improved")
            
            # Execute the validated solution
            execution_result = self._execute_solution(final_solution, task, domain)
            
            print(f"[WORKER] Execution: {'SUCCESS' if execution_result['success'] else 'FAILED'}")
            if not execution_result['success']:
                print(f"[WORKER] Execution error: {execution_result['error']}")
                if execution_result.get('stdout'):
                    print(f"[WORKER] Output before error: {execution_result['stdout']}")
            
            if execution_result['success']:
                # Save the artifact
                artifact_path = self._save_specialized_artifact(task, final_solution, domain)
                
                result = {
                    'solution': final_solution,
                    'original_solution': validation_result['original_solution'],
                    'output': execution_result['output'],
                    'artifact_path': artifact_path,
                    'explanation': solution_result.get('explanation', ''),
                    'domain': domain,
                    'language': solution_result.get('language', 'python'),
                    'confidence': confidence,
                    'validation_passed': validation_result['validation_passed'],
                    'issues_fixed': validation_result['issues_fixed'],
                    'approach_used': solution_result.get('approach_used', 'unknown')
                }
                
                self.task_queue.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED, 
                    result=json.dumps(result)
                )
                
                print(f"Task completed: {task['title']}")
                return True
            else:
                self.task_queue.update_task_status(
                    task_id, 
                    TaskStatus.FAILED, 
                    error_message=execution_result['error']
                )
                return False
                
        except Exception as e:
            self.task_queue.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error_message=str(e)
            )
            return False 
        
    def _generate_specialized_solution(self, task: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate solution using robust, domain-aware approach."""
        
        project_id = task['subtask_data'].get('project_id')
        
        # Get project context if available
        context = ""
        if project_id and self.context_manager.should_build_upon_existing(task, project_id):
            context_prompt = self.context_manager.generate_context_prompt(task, project_id)
            integration_guidance = self.context_manager.get_code_integration_guidance(task, project_id)
            context = f"{context_prompt}\n\nINTEGRATION GUIDANCE: {integration_guidance}"
        
        # Use robust solution creator with fallback mechanisms
        return self.solution_creator.create_solution(task, classification, context)
    
    def _execute_code(self, code: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the generated code in a subprocess."""
        
        # Check if this is a GUI application
        is_gui_app = self._is_gui_application(code)
        
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            if is_gui_app:
                # For GUI apps, start the process and check if it starts successfully
                print(f"[WORKER] Detected GUI application, testing startup...")
                
                process = subprocess.Popen(
                    ['python', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=self.artifacts_dir
                )
                
                # Give the GUI a few seconds to start up
                import time
                time.sleep(3)
                
                # Check if process is still running (good sign for GUI)
                if process.poll() is None:
                    # Process is still running - GUI likely started successfully
                    print(f"[WORKER] GUI application started successfully")
                    
                    # Terminate the GUI gracefully
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    
                    # Clean up temporary file
                    os.unlink(temp_file)
                    
                    return {
                        'success': True,
                        'output': 'GUI application started and ran successfully',
                        'stderr': ''
                    }
                else:
                    # Process exited quickly - likely an error
                    stdout, stderr = process.communicate()
                    os.unlink(temp_file)
                    
                    return {
                        'success': False,
                        'error': f'GUI application failed to start: {stderr}',
                        'stdout': stdout
                    }
            else:
                # For non-GUI apps, run normally
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.artifacts_dir
                )
                
                # Clean up temporary file
                os.unlink(temp_file)
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'output': result.stdout,
                        'stderr': result.stderr
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Code execution failed: {result.stderr}',
                        'stdout': result.stdout
                    }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Code execution timed out (30 seconds)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error executing code: {str(e)}'
            }
    
    def _is_gui_application(self, code: str) -> bool:
        """Detect if the code is a GUI application."""
        
        gui_indicators = [
            'tkinter',
            'tk.',
            '.mainloop()',
            'root.mainloop',
            'window.mainloop',
            'app.mainloop',
            'Tk()',
            'tkinter.Tk',
            'from tkinter import'
        ]
        
        code_lower = code.lower()
        return any(indicator.lower() in code_lower for indicator in gui_indicators)
    
    def _save_artifact(self, task: Dict[str, Any], code: str) -> str:
        """Save the generated code as a proper project structure."""
        
        # Get project info
        task_data = task['subtask_data']
        project_id = task_data.get('project_id', 'unknown')
        
        # Create project directory
        project_name = self._get_safe_project_name(task, project_id)
        project_dir = os.path.join(self.artifacts_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Determine if this should be a module or the main file
        is_main_component = self._is_main_component(task, code)
        
        if is_main_component:
            # This is the main application file
            main_file = os.path.join(project_dir, "main.py")
            self._save_main_file(main_file, task, code)
            
            # Also create a simple README
            readme_file = os.path.join(project_dir, "README.md")
            self._save_readme(readme_file, task, project_id)
            
            return main_file
        else:
            # This is a module/component
            module_name = self._get_module_name(task)
            module_file = os.path.join(project_dir, f"{module_name}.py")
            self._save_module_file(module_file, task, code)
            
            # Update or create main.py to import this module
            main_file = os.path.join(project_dir, "main.py")
            self._update_main_file(main_file, task, module_name)
            
            return module_file
    
    def _get_safe_project_name(self, task: Dict[str, Any], project_id: str) -> str:
        """Generate a safe directory name for the project."""
        
        # Try to get project name from task context
        context = self.context_manager.get_project_context(project_id)
        if context and context.get('completed_tasks'):
            # Use the first task's title as project base name
            first_task = context['completed_tasks'][0]['title']
            base_name = "".join(c for c in first_task if c.isalnum() or c in (' ', '-', '_')).strip()
            base_name = base_name.replace(' ', '_').lower()
        else:
            # Fallback to current task
            base_name = "".join(c for c in task['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
            base_name = base_name.replace(' ', '_').lower()
        
        # Ensure we have a valid name
        if not base_name or base_name.startswith('_'):
            base_name = "ai_project"
        
        return base_name
    
    def _is_main_component(self, task: Dict[str, Any], code: str) -> bool:
        """Determine if this code should be the main application file."""
        
        # Check if this is the first task or contains main execution
        task_title = task['title'].lower()
        
        # First task is usually the main framework
        context = self.context_manager.get_project_context(task['subtask_data'].get('project_id'))
        if not context or len(context.get('completed_tasks', [])) == 0:
            return True
        
        # Check if code has main execution pattern
        if 'if __name__ == "__main__"' in code:
            return True
        
        # Check for framework/main keywords in task
        main_keywords = ['framework', 'main', 'basic', 'core', 'foundation', 'structure']
        if any(keyword in task_title for keyword in main_keywords):
            return True
        
        return False
    
    def _get_module_name(self, task: Dict[str, Any]) -> str:
        """Generate a module name from the task title."""
        
        title = task['title'].lower()
        
        # Extract key functionality words
        if 'addition' in title or 'add' in title:
            return 'addition'
        elif 'subtraction' in title or 'subtract' in title:
            return 'subtraction'
        elif 'multiplication' in title or 'multiply' in title:
            return 'multiplication'
        elif 'division' in title or 'divide' in title:
            return 'division'
        elif 'ui' in title or 'interface' in title or 'gui' in title:
            return 'ui'
        elif 'input' in title or 'output' in title:
            return 'io'
        else:
            # Fallback: create safe module name from title
            safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_').lower()
            return safe_name[:20]  # Limit length
    
    def _save_main_file(self, filepath: str, task: Dict[str, Any], code: str):
        """Save the main application file."""
        
        with open(filepath, 'w') as f:
            f.write('#!/usr/bin/env python3\n')
            f.write('"""\n')
            f.write(f'Main Application: {task["title"]}\n')
            f.write(f'Description: {task["description"]}\n')
            f.write(f'Generated: {task.get("created_at", "Unknown")}\n')
            f.write('\nTo run this application:\n')
            f.write('    python main.py\n')
            f.write('"""\n\n')
            f.write(code)
    
    def _save_module_file(self, filepath: str, task: Dict[str, Any], code: str):
        """Save a module file."""
        
        with open(filepath, 'w') as f:
            f.write('"""\n')
            f.write(f'Module: {task["title"]}\n')
            f.write(f'Description: {task["description"]}\n')
            f.write(f'Generated: {task.get("created_at", "Unknown")}\n')
            f.write('"""\n\n')
            f.write(code)
    
    def _update_main_file(self, main_filepath: str, task: Dict[str, Any], module_name: str):
        """Update main.py to integrate a new module."""
        
        if not os.path.exists(main_filepath):
            # Create a basic main.py that imports the module
            with open(main_filepath, 'w') as f:
                f.write('#!/usr/bin/env python3\n')
                f.write('"""\n')
                f.write('Main Application Entry Point\n')
                f.write('"""\n\n')
                f.write(f'from {module_name} import *\n\n')
                f.write('if __name__ == "__main__":\n')
                f.write('    print("Running application...")\n')
                f.write(f'    # TODO: Integrate {module_name} functionality\n')
        else:
            # Read existing main.py and add import if not present
            with open(main_filepath, 'r') as f:
                content = f.read()
            
            import_line = f'from {module_name} import *'
            if import_line not in content:
                # Add import after the docstring
                lines = content.split('\n')
                insert_pos = 0
                
                # Find end of docstring
                in_docstring = False
                for i, line in enumerate(lines):
                    if '"""' in line:
                        if not in_docstring:
                            in_docstring = True
                        else:
                            insert_pos = i + 1
                            break
                
                # Insert the import
                lines.insert(insert_pos, '')
                lines.insert(insert_pos + 1, import_line)
                
                with open(main_filepath, 'w') as f:
                    f.write('\n'.join(lines))
    
    def _save_readme(self, filepath: str, task: Dict[str, Any], project_id: str):
        """Create a README.md for the project."""
        
        context = self.context_manager.get_project_context(project_id)
        project_state = self.task_queue.get_project_state(project_id)
        
        with open(filepath, 'w') as f:
            f.write(f'# {task["title"]}\n\n')
            
            if project_state:
                f.write(f'**Objective:** {project_state["objective"]}\n\n')
            
            f.write(f'**Description:** {task["description"]}\n\n')
            
            f.write('## How to Run\n\n')
            f.write('```bash\n')
            f.write('python main.py\n')
            f.write('```\n\n')
            
            f.write('## Project Structure\n\n')
            f.write('- `main.py` - Main application entry point\n')
            if context and context.get('completed_tasks'):
                for completed_task in context['completed_tasks']:
                    module_name = self._get_module_name({'title': completed_task['title']})
                    if module_name != 'main':
                        f.write(f'- `{module_name}.py` - {completed_task["title"]}\n')
            
            f.write('\n## Generated by AI Agent Framework\n\n')
            f.write('This project was automatically generated using a hierarchical multi-agent system.\n')
    
    def process_next_task(self) -> Optional[Dict[str, Any]]:
        """Get and process the next available task."""
        
        task = self.task_queue.get_next_task()
        if not task:
            return None
        
        success = self.execute_task(task)
        
        return {
            'task_id': task['id'],
            'title': task['title'],
            'success': success
        }