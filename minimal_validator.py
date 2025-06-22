from typing import Dict, Any, List

class MinimalValidator:
    """Lightweight validator that adapts to different languages."""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
    
    def validate_and_improve(self, code: str, task: Dict[str, Any], language: str = 'python') -> Dict[str, Any]:
        """Language-aware validation with minimal overhead."""
        
        print(f"[VALIDATOR] Validating {language} code")
        
        # Language-specific validation
        if language == 'javascript':
            return self._validate_javascript(code, task)
        elif language == 'python':
            return self._validate_python(code, task)
        elif language == 'java':
            return self._validate_java(code, task)
        else:
            # For unsupported languages, just accept the code
            return self._no_validation(code, language)
    
    def _validate_javascript(self, code: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight JavaScript validation."""
        
        issues = []
        
        # Basic syntax checks
        if code.count('{') != code.count('}'):
            issues.append("Mismatched curly braces")
        
        if code.count('(') != code.count(')'):
            issues.append("Mismatched parentheses")
        
        # Check if it looks like JavaScript
        js_keywords = ['function', 'const', 'let', 'var', 'document', 'canvas', '=>']
        has_js = any(keyword in code for keyword in js_keywords)
        
        if not has_js and len(code) > 50:
            issues.append("Does not appear to be JavaScript code")
        
        return {
            'original_code': code,
            'final_code': code,
            'validation_passed': len(issues) == 0,
            'issues_found': len(issues),
            'issues_fixed': False,
            'validation_details': {'issues': issues, 'language': 'javascript'}
        }
    
    def _validate_python(self, code: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight Python validation."""
        
        issues = []
        
        # Basic syntax check
        try:
            import ast
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {str(e)}")
        except:
            pass  # Ignore other parsing errors
        
        # Check for potential infinite loops
        if 'while True:' in code and 'break' not in code:
            issues.append("Potential infinite loop")
        
        return {
            'original_code': code,
            'final_code': code,
            'validation_passed': len(issues) == 0,
            'issues_found': len(issues),
            'issues_fixed': False,
            'validation_details': {'issues': issues, 'language': 'python'}
        }
    
    def _validate_java(self, code: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight Java validation."""
        
        issues = []
        
        # Basic checks
        if code.count('{') != code.count('}'):
            issues.append("Mismatched curly braces")
        
        if 'class' in code and 'public class' not in code:
            issues.append("Classes should typically be public")
        
        return {
            'original_code': code,
            'final_code': code,
            'validation_passed': len(issues) == 0,
            'issues_found': len(issues),
            'issues_fixed': False,
            'validation_details': {'issues': issues, 'language': 'java'}
        }
    
    def _no_validation(self, code: str, language: str) -> Dict[str, Any]:
        """Accept code without validation."""
        
        print(f"[VALIDATOR] No validation rules for {language} - accepting as-is")
        
        return {
            'original_code': code,
            'final_code': code,
            'validation_passed': True,
            'issues_found': 0,
            'issues_fixed': False,
            'validation_details': {'language': language, 'validated': False}
        }