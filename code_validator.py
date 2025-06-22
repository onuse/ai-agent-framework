import ast
import subprocess
import tempfile
import os
import ollama
from typing import Dict, Any, List

class CodeValidator:
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
    
    def validate_code(self, code: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive code validation including syntax, common issues, and dry run."""
        
        validation_results = {
            'syntax_valid': False,
            'common_issues': [],
            'dry_run_success': False,
            'improved_code': None,
            'validation_errors': []
        }
        
        # 1. Syntax validation
        syntax_result = self._check_syntax(code)
        validation_results['syntax_valid'] = syntax_result['valid']
        if not syntax_result['valid']:
            validation_results['validation_errors'].append(f"Syntax error: {syntax_result['error']}")
        
        # 2. Common issue detection
        common_issues = self._detect_common_issues(code)
        validation_results['common_issues'] = common_issues
        
        # 3. Dry run test (syntax check only, no actual execution)
        dry_run_result = self._dry_run_test(code)
        validation_results['dry_run_success'] = dry_run_result['success']
        if not dry_run_result['success']:
            validation_results['validation_errors'].append(f"Dry run failed: {dry_run_result['error']}")
        
        # 4. If there are issues, attempt to fix them
        if not validation_results['syntax_valid'] or validation_results['common_issues'] or not validation_results['dry_run_success']:
            print(f"[VALIDATOR] Found issues in code, attempting to fix...")
            improved_code = self._fix_code_issues(code, task, validation_results)
            if improved_code:
                validation_results['improved_code'] = improved_code
                # Re-validate the improved code
                improved_syntax = self._check_syntax(improved_code)
                if improved_syntax['valid']:
                    print(f"[VALIDATOR] Code fixed successfully!")
                else:
                    print(f"[VALIDATOR] Could not fix all issues")
        
        return validation_results
    
    def _check_syntax(self, code: str) -> Dict[str, Any]:
        """Check if code has valid Python syntax."""
        try:
            ast.parse(code)
            return {'valid': True, 'error': None}
        except SyntaxError as e:
            return {'valid': False, 'error': str(e)}
        except Exception as e:
            return {'valid': False, 'error': f"Parsing error: {str(e)}"}
    
    def _detect_common_issues(self, code: str) -> List[str]:
        """Detect common coding issues that might cause runtime errors."""
        issues = []
        
        # Check for tkinter geometry manager mixing
        if 'tkinter' in code.lower() or 'tk.' in code:
            has_pack = '.pack(' in code
            has_grid = '.grid(' in code
            has_place = '.place(' in code
            
            managers_used = sum([has_pack, has_grid, has_place])
            if managers_used > 1:
                issues.append("Mixing tkinter geometry managers (pack/grid/place) in same container")
        
        # Check for common import issues
        if 'import tkinter' in code and 'from tkinter import' in code:
            issues.append("Mixing different tkinter import styles may cause conflicts")
        
        # Check for potential infinite loops in simple patterns
        if 'while True:' in code and 'break' not in code and 'return' not in code:
            issues.append("Potential infinite loop detected")
        
        # Check for file operations without error handling
        if ('open(' in code and 'try:' not in code) or ('with open(' not in code and 'open(' in code):
            if 'try:' not in code:
                issues.append("File operations should include error handling")
        
        # Check for missing main execution pattern
        if 'def main(' in code and '__name__' not in code:
            issues.append("Main function defined but not called")
        
        return issues
    
    def _dry_run_test(self, code: str) -> Dict[str, Any]:
        """Perform a dry run test - compile but don't fully execute."""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Try to compile the code
            result = subprocess.run(
                ['python', '-m', 'py_compile', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Clean up
            os.unlink(temp_file)
            if os.path.exists(temp_file + 'c'):  # Remove .pyc file
                os.unlink(temp_file + 'c')
            
            if result.returncode == 0:
                return {'success': True, 'error': None}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _fix_code_issues(self, code: str, task: Dict[str, Any], validation_results: Dict[str, Any]) -> str:
        """Use LLM to fix identified code issues."""
        
        issues_description = []
        
        if not validation_results['syntax_valid']:
            issues_description.append("- Syntax errors present")
        
        for issue in validation_results['common_issues']:
            issues_description.append(f"- {issue}")
        
        for error in validation_results['validation_errors']:
            issues_description.append(f"- {error}")
        
        prompt = f"""You are a code reviewer tasked with fixing issues in Python code.

ORIGINAL TASK: {task['title']}
TASK DESCRIPTION: {task['description']}

ISSUES FOUND:
{chr(10).join(issues_description)}

PROBLEMATIC CODE:
```python
{code}
```

Fix these issues while maintaining the original functionality. Pay special attention to:
1. If this is a tkinter GUI, use ONLY ONE geometry manager (preferably grid) throughout
2. Ensure proper error handling
3. Fix any syntax errors
4. Maintain the same functionality as the original code

Provide the corrected code:

```python
[Your fixed code here]
```

Make sure the fixed code is complete and addresses all identified issues."""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            
            # Extract code from response
            if "```python" in content:
                code_start = content.find("```python") + 9
                code_end = content.find("```", code_start)
                if code_end != -1:
                    fixed_code = content[code_start:code_end].strip()
                    return fixed_code
            elif "```" in content:
                code_start = content.find("```") + 3
                code_end = content.find("```", code_start)
                if code_end != -1:
                    fixed_code = content[code_start:code_end].strip()
                    return fixed_code
            
            return None
            
        except Exception as e:
            print(f"Error fixing code: {e}")
            return None
    
    def validate_and_improve(self, code: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Main validation entry point - returns validation results and improved code if available."""
        
        print(f"[VALIDATOR] Validating code for task: {task['title']}")
        
        # Check if this is JavaScript code - if so, skip Python validation
        if self._is_javascript_code(code):
            print(f"[VALIDATOR] JavaScript code detected - skipping Python validation")
            return {
                'original_code': code,
                'final_code': code,
                'validation_passed': True,
                'issues_found': 0,
                'issues_fixed': False,
                'validation_details': {'language': 'javascript', 'skipped': True}
            }
        
        validation_results = self.validate_code(code, task)
        
        # Determine the best code to use
        final_code = code
        if validation_results['improved_code']:
            final_code = validation_results['improved_code']
        
        # Final validation of the chosen code
        final_syntax_check = self._check_syntax(final_code)
        
        return {
            'original_code': code,
            'final_code': final_code,
            'validation_passed': final_syntax_check['valid'],
            'issues_found': len(validation_results['common_issues']) + len(validation_results['validation_errors']),
            'issues_fixed': validation_results['improved_code'] is not None,
            'validation_details': validation_results
        }
    
    def _is_javascript_code(self, code: str) -> bool:
        """Check if code is JavaScript."""
        js_indicators = [
            'function ', 'const ', 'let ', 'var ', '=>', 'document.',
            'window.', 'console.log', 'addEventListener', 'getElementById',
            'canvas.getContext', 'requestAnimationFrame'
        ]
        return any(indicator in code for indicator in js_indicators)