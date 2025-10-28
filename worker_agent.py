import os
import subprocess
import tempfile
import json
import time
from typing import Dict, Any, Optional, Tuple
from task_queue import TaskQueue, TaskStatus
from code_validator import CodeValidator
from minimal_validator import MinimalValidator
from context_manager import ContextManager
from task_classifier import TaskClassifier
from robust_solution_creator import RobustSolutionCreator
from multilanguage_solution_creators import MultiLanguageExecutor
from project_folder_manager import ProjectFolderManager

class WorkerAgent:
    def __init__(self, model_name: str = None):
        self.model_name = model_name
        self.task_queue = TaskQueue()
        self.validator = MinimalValidator(model_name)
        self.context_manager = ContextManager()
        self.task_classifier = TaskClassifier()
        self.solution_creator = RobustSolutionCreator(model_name)
        self.multilang_executor = MultiLanguageExecutor()
        self.project_manager = ProjectFolderManager()
        self.artifacts_dir = "artifacts"
        
        # Callback for notifying manager of task completion
        self.task_completion_callback = None
        
        # Create artifacts directory if it doesn't exist
        os.makedirs(self.artifacts_dir, exist_ok=True)
    
    def set_task_completion_callback(self, callback):
        """Set callback function to notify manager of task completions."""
        self.task_completion_callback = callback
    
    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a single task and return success status."""
        
        task_id = task['id']
        print(f"[WORKER] Starting task: {task['title']}")
        
        # Check if this is a planned task
        is_planned_task = task.get('subtask_data', {}).get('task_type') == 'planned'
        plan_task_id = task.get('subtask_data', {}).get('plan_task_id')
        
        if is_planned_task:
            print(f"[WORKER] Executing planned task: {plan_task_id}")
            
            # For planned tasks, we might have more context
            dependencies = task.get('subtask_data', {}).get('dependencies', [])
            if dependencies:
                print(f"[WORKER] Task dependencies: {dependencies}")
        
        # Classify the task (unless it's already classified in planning)
        domain = task.get('subtask_data', {}).get('domain', None)
        
        if domain:
            # Use domain from planning
            classification = {
                'primary_domain': domain,
                'confidence': 0.95,
                'approach': 'specialized',
                'reasoning': 'Domain specified by project planner',
                'classification_method': 'plan_specified'
            }
            print(f"[WORKER] Using planned domain: {domain}")
        else:
            # Classify the task
            classification = self.task_classifier.classify_task(task)
            domain = classification['primary_domain']
            confidence = classification['confidence']
            approach = classification['approach']
            
            print(f"[WORKER] Classified domain: {domain} (confidence: {confidence:.2f}) - {approach}")
            if classification.get('fallback_reason'):
                print(f"[WORKER] {classification['fallback_reason']}")
        
        # Update task status to in progress
        self.task_queue.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        
        try:
            # Generate solution using SAFE domain-specific approach
            print(f"[WORKER] Generating solution...")
            solution_result = self._generate_safe_solution(task, classification)
            print(f"[WORKER] Solution generation success: {solution_result.get('success')}")
            
            if not solution_result['success']:
                print(f"[WORKER] Solution generation failed: {solution_result.get('error')}")
                self.task_queue.update_task_status(
                    task_id, 
                    TaskStatus.FAILED, 
                    error_message=solution_result['error']
                )
                return False
            
            # Apply domain-appropriate validation
            print(f"[WORKER] Validating solution...")
            validation_result = self.validator.validate_and_improve(
                solution_result['solution'], 
                task, 
                solution_result.get('language', 'python')
            )
            print(f"[WORKER] Validation passed: {validation_result['validation_passed']}")
            
            # Use the validated/improved solution
            final_solution = validation_result['final_code']
            
            if validation_result['issues_found'] > 0:
                print(f"[WORKER] Issues found: {validation_result['issues_found']}")
            if validation_result['issues_fixed']:
                print(f"[WORKER] Solution was automatically improved")
            
            # Execute the validated solution
            print(f"[WORKER] Executing solution...")
            execution_result = self._execute_solution(final_solution, task, domain)
            print(f"[WORKER] Execution success: {execution_result.get('success')}")
            
            if not execution_result['success']:
                print(f"[WORKER] Execution error: {execution_result.get('error')}")
                if execution_result.get('stdout'):
                    print(f"[WORKER] Output before error: {execution_result['stdout']}")
            
            if execution_result['success']:
                # Get project objective for organized saving
                project_state = self.task_queue.get_project_state(task['subtask_data'].get('project_id'))
                objective = project_state['objective'] if project_state else task['title']
                
                # Save artifact using ProjectFolderManager
                artifact_path = self.project_manager.save_artifact_to_project(
                    task=task,
                    solution=final_solution,
                    domain=domain,
                    language=solution_result.get('language', 'python'),
                    objective=objective
                )
                print(f"[WORKER] Artifact saved to: {artifact_path}")
                
                result = {
                    'solution': final_solution,
                    'original_solution': validation_result['original_code'],
                    'output': execution_result['output'],
                    'artifact_path': artifact_path,
                    'explanation': solution_result.get('explanation', ''),
                    'domain': domain,
                    'language': solution_result.get('language', 'python'),
                    'confidence': classification.get('confidence', 0.8),
                    'validation_passed': validation_result['validation_passed'],
                    'issues_fixed': validation_result['issues_fixed'],
                    'approach_used': solution_result.get('approach_used', 'unknown'),
                    'plan_task_id': plan_task_id  # Include for plan tracking
                }
                
                self.task_queue.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED, 
                    result=json.dumps(result)
                )
                
                # Notify manager of task completion if callback is set
                if self.task_completion_callback and is_planned_task:
                    project_id = task['subtask_data'].get('project_id')
                    if project_id:
                        self.task_completion_callback(project_id, task)
                
                print(f"[SUCCESS] Task completed: {task['title']}")
                return True
            else:
                self.task_queue.update_task_status(
                    task_id, 
                    TaskStatus.FAILED, 
                    error_message=execution_result['error']
                )
                return False
                
        except Exception as e:
            print(f"[ERROR] Task execution failed with exception: {str(e)}")
            self.task_queue.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error_message=str(e)
            )
            return False
    
    def _generate_safe_solution(self, task: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate solution using SAFE, robust approach with plan awareness."""
        
        project_id = task['subtask_data'].get('project_id')
        
        # Enhanced context for planned tasks
        context = ""
        if project_id:
            try:
                # Check if this is part of a larger plan
                is_planned_task = task.get('subtask_data', {}).get('task_type') == 'planned'
                
                if is_planned_task:
                    # For planned tasks, include plan context
                    context = self._generate_plan_aware_context(task, project_id)
                elif self.context_manager.should_build_upon_existing(task, project_id):
                    # For regular tasks, use existing context system
                    context_prompt = self.context_manager.generate_context_prompt(task, project_id)
                    integration_guidance = self.context_manager.get_code_integration_guidance(task, project_id)
                    context = f"{context_prompt}\n\nINTEGRATION GUIDANCE: {integration_guidance}"
            except Exception as e:
                print(f"[WORKER] Context generation failed: {e}")
                context = ""
        
        # Use the SAFE robust solution creator
        return self.solution_creator.create_solution(task, classification, context)
    
    def _generate_plan_aware_context(self, task: Dict[str, Any], project_id: str) -> str:
        """Generate context that's aware of the project plan and dependencies."""
        
        subtask_data = task.get('subtask_data', {})
        objective = subtask_data.get('objective', 'Unknown objective')
        dependencies = subtask_data.get('dependencies', [])
        estimated_effort = subtask_data.get('estimated_effort', 'Medium')
        
        # Get existing project context
        project_context = self.context_manager.get_project_context(project_id)
        
        context = f"""You are working on a planned task as part of a larger project.

PROJECT OBJECTIVE: {objective}
CURRENT TASK: {task['title']}
TASK DESCRIPTION: {task['description']}
ESTIMATED EFFORT: {estimated_effort}

TASK DEPENDENCIES: {', '.join(dependencies) if dependencies else 'None'}

PROJECT CONTEXT:
- Total completed tasks: {project_context['task_count']}
- Existing artifacts: {len(project_context['artifact_files'])}
"""
        
        # Include information about dependency completion
        if dependencies:
            context += f"\nDEPENDENCY STATUS:\n"
            for dep in dependencies:
                context += f"- {dep}: Assumed completed (implement accordingly)\n"
            
            context += f"\nIMPORTANT: Build upon the work done in dependent tasks. "
            context += f"This task should integrate with and extend previous components.\n"
        
        # Include latest code if available
        if project_context['latest_code']:
            context += f"""
EXISTING PROJECT CODE:
```python
{project_context['latest_code'][:1500]}{'...' if len(project_context['latest_code']) > 1500 else ''}
```

BUILD UPON THIS: Extend, modify, or integrate with the existing code above.
"""
        
        context += f"""
PLAN-AWARE REQUIREMENTS:
1. This task is part of a larger planned project - ensure it fits the overall architecture
2. Consider how this component will integrate with other planned components
3. Create modular, reusable code that other tasks can build upon
4. Include clear interfaces and documentation for future integration
5. Focus on the specific deliverable: {subtask_data.get('deliverable', 'Working implementation')}

Generate code that fulfills this specific task while being mindful of the larger project context."""
        
        return context
    
    def _execute_solution(self, solution: str, task: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Execute solution based on domain type."""
        
        print(f"[WORKER] Executing {domain} solution...")
        
        # Route to appropriate execution method based on domain
        if domain in ['code', 'ui', 'game']:
            return self._execute_code(solution, task)
        elif domain == 'data':
            return self._execute_data_code(solution, task)
        elif domain == 'creative':
            return self._execute_creative(solution, task)
        elif domain == 'research':
            return self._execute_research(solution, task)
        else:
            # Default to code execution
            return self._execute_code(solution, task)
    
    def _execute_data_code(self, code: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data analysis code with extra safety checks."""
        
        print(f"[WORKER] Executing data analysis code...")
        
        # Check for unsafe data science imports
        unsafe_imports = ['pandas', 'numpy', 'matplotlib', 'seaborn', 'sklearn', 'tensorflow', 'torch']
        code_lower = code.lower()
        
        for unsafe_import in unsafe_imports:
            if f'import {unsafe_import}' in code_lower:
                print(f"[WORKER] Removing unsafe import: {unsafe_import}")
                # Replace with safe alternative or remove
                if unsafe_import == 'pandas':
                    code = code.replace(f'import {unsafe_import} as pd', '# pandas not available - using pure Python')
                    code = code.replace(f'import {unsafe_import}', '# pandas not available - using pure Python')
                else:
                    code = code.replace(f'import {unsafe_import}', f'# {unsafe_import} not available - using pure Python')
        
        # Execute the cleaned code
        return self._execute_code(code, task)
    
    def _execute_creative(self, content: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute creative content (validate and return)."""
        
        try:
            # Basic validation for creative content
            if len(content.strip()) < 50:
                return {
                    'success': False,
                    'error': 'Creative content too short (less than 50 characters)'
                }
            
            return {
                'success': True,
                'output': f'Creative content generated successfully ({len(content)} characters)',
                'stderr': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Creative content validation failed: {str(e)}'
            }
    
    def _execute_research(self, content: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research content (validate and return)."""
        
        try:
            # Basic validation for research content
            if len(content.strip()) < 100:
                return {
                    'success': False,
                    'error': 'Research content too short (less than 100 characters)'
                }
            
            # Check for basic research structure
            has_structure = any(marker in content.lower() for marker in 
                              ['introduction', 'conclusion', 'summary', '##', '#'])
            
            if not has_structure:
                return {
                    'success': False,
                    'error': 'Research content lacks proper structure'
                }
            
            return {
                'success': True,
                'output': f'Research document generated successfully ({len(content)} characters)',
                'stderr': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Research content validation failed: {str(e)}'
            }
    
    def _execute_code(self, code: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the generated code in a subprocess with EXTRA safety."""
        
        # Detect language from code content
        language = self._detect_code_language(code)
        print(f"[WORKER] Code language detected: {language}")
        
        # For JavaScript, we can't easily execute it safely, so validate and return success
        if language == 'javascript':
            print(f"[WORKER] JavaScript code detected - validating syntax only")
            
            # Basic JavaScript validation
            js_issues = self._check_javascript_safety(code)
            if js_issues:
                print(f"[WORKER] JavaScript issues detected: {js_issues}")
                return {
                    'success': False,
                    'error': f'JavaScript validation failed: {", ".join(js_issues)}'
                }
            
            # If no major issues, consider it successful
            return {
                'success': True,
                'output': f'JavaScript code validated successfully ({len(code)} characters)',
                'stderr': ''
            }
        
        # Continue with Python execution for non-JavaScript code
        # PRE-EXECUTION SAFETY CHECK
        print(f"[WORKER] Pre-execution safety check...")
        safety_issues = self._check_code_safety(code)
        
        if safety_issues:
            print(f"[WORKER] Safety issues detected: {safety_issues}")
            # Try to fix common issues
            code = self._fix_common_safety_issues(code)
            print(f"[WORKER] Applied safety fixes")
        
        # Check if this is a GUI application
        is_gui_app = self._is_gui_application(code)
        print(f"[WORKER] GUI application detected: {is_gui_app}")
        
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            print(f"[WORKER] Created temp file: {temp_file}")
            
            if is_gui_app:
                # For GUI apps, start the process and check if it starts successfully
                print(f"[WORKER] Testing GUI application startup...")
                
                process = subprocess.Popen(
                    ['python', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=self.artifacts_dir
                )
                
                # Give the GUI a few seconds to start up
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
                # For non-GUI apps, run normally with SHORT timeout
                print(f"[WORKER] Running non-GUI application...")
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=15,  # REDUCED timeout to 15 seconds
                    cwd=self.artifacts_dir
                )
                
                # Clean up temporary file
                os.unlink(temp_file)
                
                print(f"[WORKER] Process return code: {result.returncode}")
                print(f"[WORKER] Process stdout: {result.stdout[:200]}...")
                print(f"[WORKER] Process stderr: {result.stderr}")
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'output': result.stdout,
                        'stderr': result.stderr
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Code execution failed (return code {result.returncode}): {result.stderr}',
                        'stdout': result.stdout
                    }
                
        except subprocess.TimeoutExpired:
            print(f"[WORKER] Code execution timed out")
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
            return {
                'success': False,
                'error': 'Code execution timed out (15 seconds) - likely contains input() or infinite loop'
            }
        except Exception as e:
            print(f"[WORKER] Code execution exception: {str(e)}")
            return {
                'success': False,
                'error': f'Error executing code: {str(e)}'
            }
    
    def _detect_code_language(self, code: str) -> str:
        """Detect programming language from code content."""
        
        # JavaScript indicators
        js_indicators = [
            'function ', 'const ', 'let ', 'var ', '=>', 'document.',
            'window.', 'console.log', 'addEventListener', 'getElementById',
            'canvas.getContext', 'requestAnimationFrame'
        ]
        
        if any(indicator in code for indicator in js_indicators):
            return 'javascript'
        
        return 'python'  # Default to Python
    
    def _check_javascript_safety(self, code: str) -> list:
        """Check JavaScript code for basic safety issues."""
        
        issues = []
        code_lower = code.lower()
        
        # Check for potentially dangerous patterns (relaxed for game development)
        dangerous_patterns = [
            ('eval(', 'uses eval() function'),
            ('document.write', 'uses document.write'),
            ('while(true)', 'potential infinite loop'),
            # Removed setInterval check - it's common in games
        ]
        
        for pattern, description in dangerous_patterns:
            if pattern in code_lower:
                issues.append(description)
        
        return issues
    
    def _check_code_safety(self, code: str) -> list:
        """Check code for safety issues."""
        
        issues = []
        code_lower = code.lower()
        
        # Check for dangerous patterns
        dangerous_patterns = [
            ('sys.exit', 'calls sys.exit()'),
            ('input(', 'uses input() - will hang'),
            ('while true', 'potential infinite loop'),
            ('import pandas', 'tries to import pandas'),
            ('import numpy', 'tries to import numpy'),
            ('import matplotlib', 'tries to import matplotlib'),
            ('import seaborn', 'tries to import seaborn'),
            ('subprocess.', 'uses subprocess'),
        ]
        
        for pattern, description in dangerous_patterns:
            if pattern in code_lower:
                issues.append(description)
        
        return issues
    
    def _fix_common_safety_issues(self, code: str) -> str:
        """Fix common safety issues in code."""
        
        # Remove dangerous imports
        dangerous_imports = [
            'import pandas as pd',
            'import pandas',
            'import numpy as np', 
            'import numpy',
            'import matplotlib.pyplot as plt',
            'import matplotlib',
            'import seaborn as sns',
            'import seaborn'
        ]
        
        for dangerous_import in dangerous_imports:
            if dangerous_import in code:
                code = code.replace(dangerous_import, f'# {dangerous_import} # REMOVED FOR SAFETY')
        
        # Replace input() calls with hardcoded values
        if 'input(' in code:
            code = code.replace('input("Enter your name: ")', '"Sample User"')
            code = code.replace('input("Enter a number: ")', '"42"')
            code = code.replace('input(', '"sample_input"  # input(')
        
        # Replace sys.exit() calls
        if 'sys.exit(' in code:
            code = code.replace('sys.exit(', 'print("Program would exit here")  # sys.exit(')
        
        return code
    
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
    
    def show_project_structure(self):
        """Display the organized project structure."""
        
        projects = self.project_manager.list_projects()
        
        if not projects:
            print("📁 No projects found in artifacts directory")
            return
        
        print(f"📁 Found {len(projects)} organized projects:")
        print("="*60)
        
        for project in projects:
            print(f"📂 {project['name']}")
            print(f"   🎯 Objective: {project['objective']}")
            print(f"   📄 Files: {project['file_count']}")
            
            if project['domains']:
                domains_str = ', '.join(project['domains'])
                print(f"   🏷️  Domains: {domains_str}")
                
            if project['languages']:
                languages_str = ', '.join(project['languages'])
                print(f"   💻 Languages: {languages_str}")
                
            print(f"   📅 Updated: {project['last_updated'][:19]}")
            
            # Show folder contents
            if os.path.exists(project['folder_path']):
                try:
                    files = [f for f in os.listdir(project['folder_path']) 
                            if not f.startswith('.')]
                    if files:
                        files_preview = ', '.join(files[:3])
                        if len(files) > 3:
                            files_preview += f", ... (+{len(files)-3} more)"
                        print(f"   📁 Files: {files_preview}")
                except:
                    pass
            
            print()
    
    def process_next_task(self) -> Optional[Dict[str, Any]]:
        """Get and process the next available task."""
        
        task = self.task_queue.get_next_task()
        if not task:
            return None
        
        success = self.execute_task(task)
        
        return {
            'task_id': task['id'],
            'title': task['title'],
            'success': success,
            'subtask_data': task.get('subtask_data', {})
        }
    
    def get_task_execution_stats(self) -> Dict[str, Any]:
        """Get statistics about task execution."""
        
        task_counts = self.task_queue.get_task_count_by_status()
        completed_tasks = self.task_queue.get_completed_tasks()
        
        # Calculate success rate
        total_completed = task_counts.get('completed', 0)
        total_failed = task_counts.get('failed', 0)
        total_attempted = total_completed + total_failed
        
        success_rate = (total_completed / total_attempted * 100) if total_attempted > 0 else 0
        
        # Analyze domain distribution
        domain_counts = {}
        for task in completed_tasks:
            if task['result']:
                try:
                    result_data = json.loads(task['result'])
                    domain = result_data.get('domain', 'unknown')
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                except:
                    pass
        
        return {
            'task_counts': task_counts,
            'success_rate': round(success_rate, 1),
            'total_attempted': total_attempted,
            'domain_distribution': domain_counts,
            'artifacts_created': len([t for t in completed_tasks if t['result']])
        }
    
    def show_execution_summary(self):
        """Display a summary of task execution performance."""
        
        stats = self.get_task_execution_stats()
        
        print("\n⚙️ WORKER EXECUTION SUMMARY")
        print("="*50)
        print(f"📊 Success Rate: {stats['success_rate']}%")
        print(f"✅ Completed: {stats['task_counts'].get('completed', 0)}")
        print(f"❌ Failed: {stats['task_counts'].get('failed', 0)}")
        print(f"⏳ Pending: {stats['task_counts'].get('pending', 0)}")
        print(f"📁 Artifacts: {stats['artifacts_created']}")
        
        if stats['domain_distribution']:
            print(f"\n🏷️ Domain Distribution:")
            for domain, count in stats['domain_distribution'].items():
                print(f"   {domain}: {count} tasks")
    
    # Legacy method for backward compatibility
    def _save_specialized_artifact(self, task: Dict[str, Any], solution: str, domain: str) -> str:
        """Legacy method - now redirects to ProjectFolderManager."""
        
        # Get project objective for organized saving
        project_state = self.task_queue.get_project_state(task['subtask_data'].get('project_id'))
        objective = project_state['objective'] if project_state else task['title']
        
        # Use ProjectFolderManager for organized saving
        return self.project_manager.save_artifact_to_project(
            task=task,
            solution=solution,
            domain=domain,
            language='python',  # Default language for legacy calls
            objective=objective
        )