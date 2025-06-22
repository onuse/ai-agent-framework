from typing import Dict, Any, List, Optional
from solution_creators import SolutionCreatorFactory, BaseSolutionCreator
from multilanguage_solution_creators import MultiLanguageCodeSolutionCreator
from language_classifier import LanguageClassifier
import ollama

class RobustSolutionCreator:
    """Robust solution creator with fallback mechanisms, hybrid support, and multi-language capabilities."""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.language_classifier = LanguageClassifier()
        self.multilang_code_creator = MultiLanguageCodeSolutionCreator(model_name)
        self.fallback_attempts = 0
        self.max_fallback_attempts = 2
    
    def create_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Create solution with robust fallback handling and multi-language support."""
        
        approach = classification.get('approach', 'specialized')
        domain = classification.get('primary_domain', 'code')
        
        # For code tasks, detect programming language
        language_info = None
        if domain in ['code', 'ui', 'data', 'game']:
            language_info = self._detect_language_with_context(task)
            print(f"[LANGUAGE] Detected: {language_info['language']} (confidence: {language_info['confidence']:.2f})")
            if language_info.get('reasoning'):
                print(f"[LANGUAGE] {language_info['reasoning']}")
        
        try:
            if approach == 'generic_fallback':
                return self._create_generic_solution(task, context, classification.get('fallback_reason'))
            elif approach == 'specialized_cautious':
                return self._create_cautious_solution(task, classification, context, language_info)
            elif approach == 'hybrid':
                return self._create_hybrid_solution(task, classification, context, language_info)
            else:
                return self._create_specialized_solution(task, classification, context, language_info)
                
        except Exception as e:
            # Fallback to generic approach on any error
            print(f"[ROBUST] Specialized approach failed: {e}")
            return self._create_generic_solution(task, context, f"Specialized approach failed: {e}")
    
    def _detect_language_with_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Detect language using both task and original objective context."""
        
        # Get the original objective from task metadata
        objective = task.get('subtask_data', {}).get('objective', '')
        
        # Create enhanced task context that includes the original objective
        enhanced_task = {
            'title': f"{task['title']} (from project: {objective})",
            'description': f"{task['description']}. Original project objective: {objective}",
            'subtask_data': task.get('subtask_data', {})
        }
        
        # Run language classification on the enhanced context
        return self.language_classifier.classify_language(enhanced_task)
    
    def _create_specialized_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str, language_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create solution using specialized domain approach with language awareness."""
        
        domain = classification['primary_domain']
        
        try:
            # For code domains with language detection, use multi-language creator
            if domain in ['code', 'ui', 'data', 'game'] and language_info and language_info.get('is_programming_task'):
                language = language_info['language']
                print(f"[ROBUST] Using multi-language creator for {language}")
                result = self.multilang_code_creator.generate_solution(task, language, context)
                if result['success']:
                    result['approach_used'] = 'specialized_multilang'
                    result['domain'] = domain
                    result['language'] = language
                    print(f"[ROBUST] Multi-language solution generated successfully")
                return result
            else:
                # Use traditional domain-specific approach with SAFE prompting
                print(f"[ROBUST] Using safe domain solution for {domain}")
                result = self._create_safe_domain_solution(task, domain, context)
                if result['success']:
                    result['approach_used'] = 'specialized'
                    result['domain'] = domain
                    if language_info:
                        result['language'] = language_info.get('language', 'python')
                return result
                
        except Exception as e:
            # Fallback to cautious approach
            print(f"[ROBUST] Specialized creation failed, trying cautious approach: {e}")
            return self._create_cautious_solution(task, classification, context, language_info)
    
    def _create_safe_domain_solution(self, task: Dict[str, Any], domain: str, context: str) -> Dict[str, Any]:
        """Create domain-specific solution with safety guardrails."""
        
        task_data = task['subtask_data']
        
        # Create SAFE, domain-specific prompts
        if domain == 'code':
            prompt = self._create_safe_code_prompt(task, context)
        elif domain == 'creative':
            prompt = self._create_safe_creative_prompt(task, context)
        elif domain == 'data':
            prompt = self._create_safe_data_prompt(task, context)
        elif domain == 'game':
            prompt = self._create_safe_game_prompt(task, context)
        elif domain == 'ui':
            prompt = self._create_safe_ui_prompt(task, context)
        elif domain == 'research':
            prompt = self._create_safe_research_prompt(task, context)
        else:
            prompt = self._create_safe_code_prompt(task, context)  # Default to code
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            return self._extract_solution(content)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating {domain} solution: {str(e)}'
            }
    
    def _create_safe_code_prompt(self, task: Dict[str, Any], context: str) -> str:
        """Create a safe code generation prompt."""
        
        task_data = task['subtask_data']
        
        return f"""You are a senior software engineer creating safe, executable Python code.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Working code')}

{context}

CRITICAL SAFETY REQUIREMENTS:
1. Create ONLY standard Python code using built-in libraries
2. NO external imports beyond: os, sys, json, time, datetime, math, random
3. NO sys.exit() calls - let the program end naturally
4. NO input() calls - use hardcoded sample data instead
5. NO infinite loops or blocking operations
6. Code must run completely and finish execution

Generate Python code that:
- Uses only standard library imports
- Includes sample/demo data instead of requiring user input
- Demonstrates the functionality clearly with print statements
- Runs from start to finish without hanging
- Is well-commented and professional

Format your response as:
EXPLANATION:
[Brief explanation of your approach]

CODE:
```python
# Safe, self-contained Python code
[Your complete code using only standard libraries]
```

EXAMPLE of SAFE approach:
Instead of: import non_existent_module
Use: import json  # standard library

Instead of: name = input("Enter name: ")
Use: name = "Sample User"  # demo data

Instead of: while True: ...
Use: for i in range(5): ...  # bounded loop"""
    
    def _create_safe_creative_prompt(self, task: Dict[str, Any], context: str) -> str:
        """Create a safe creative writing prompt."""
        
        task_data = task['subtask_data']
        
        return f"""You are a professional creative writer.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Creative content')}

{context}

Create engaging creative content that:
- Is complete and self-contained
- Follows proper narrative structure
- Uses vivid, descriptive language
- Is appropriate for general audiences
- Demonstrates professional writing quality

Format your response as:
EXPLANATION:
[Brief explanation of your creative approach]

CONTENT:
```text
[Your complete creative content]
```"""
    
    def _create_safe_data_prompt(self, task: Dict[str, Any], context: str) -> str:
        """Create a safe data analysis prompt."""
        
        task_data = task['subtask_data']
        
        return f"""You are a data scientist creating self-contained analysis code.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Data analysis')}

{context}

SAFETY REQUIREMENTS:
1. Create sample data instead of loading external files
2. Use only: pandas, numpy, matplotlib (if available), or pure Python
3. Code must run without external dependencies
4. No file I/O operations

Generate Python code that:
- Creates sample data using lists/dictionaries
- Performs meaningful analysis
- Shows results with print statements
- Creates simple visualizations if needed
- Runs completely without errors

Format your response as:
EXPLANATION:
[Brief explanation of your analysis approach]

CODE:
```python
# Self-contained data analysis with sample data
[Your complete code with built-in sample data]
```"""
    
    def _create_safe_game_prompt(self, task: Dict[str, Any], context: str) -> str:
        """Create a safe game development prompt."""
        
        task_data = task['subtask_data']
        
        return f"""You are a game developer creating a demonstration game.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Game code')}

{context}

SAFETY REQUIREMENTS:
1. Create a text-based game demonstration
2. Use only standard Python libraries
3. Game should run for a limited time and then end
4. No infinite loops or user input blocking

Generate Python code that:
- Demonstrates game mechanics clearly
- Runs a short demo simulation
- Uses print statements to show gameplay
- Finishes execution after demonstration
- Is engaging but bounded

Format your response as:
EXPLANATION:
[Brief explanation of your game design]

CODE:
```python
# Text-based game demonstration
[Your complete game code with demo mode]
```"""
    
    def _create_safe_ui_prompt(self, task: Dict[str, Any], context: str) -> str:
        """Create a safe UI development prompt."""
        
        task_data = task['subtask_data']
        
        return f"""You are a UI developer creating a simple interface demonstration.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'User interface')}

{context}

Create a simple text-based interface demonstration that:
- Shows the UI structure and flow
- Uses print statements to simulate interface
- Demonstrates user interactions with sample data
- Is clear and well-organized

Format your response as:
EXPLANATION:
[Brief explanation of your UI design]

CODE:
```python
# Text-based UI demonstration
[Your complete interface simulation code]
```"""
    
    def _create_safe_research_prompt(self, task: Dict[str, Any], context: str) -> str:
        """Create a safe research content prompt."""
        
        task_data = task['subtask_data']
        
        return f"""You are a professional researcher creating comprehensive documentation.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Research document')}

{context}

Create well-structured research content that:
- Presents information clearly and objectively
- Uses proper organization and formatting
- Includes relevant examples and insights
- Provides actionable conclusions

Format your response as:
EXPLANATION:
[Brief explanation of your research approach]

CONTENT:
```markdown
[Your complete research document]
```"""
    
    def _extract_solution(self, content: str) -> Dict[str, Any]:
        """Extract solution from LLM response."""
        
        explanation = ""
        solution = ""
        
        if "EXPLANATION:" in content:
            parts = content.split("EXPLANATION:", 1)
            if len(parts) > 1:
                remaining = parts[1]
                if any(marker in remaining for marker in ["CODE:", "CONTENT:", "SOLUTION:"]):
                    for marker in ["CODE:", "CONTENT:", "SOLUTION:"]:
                        if marker in remaining:
                            exp_sol = remaining.split(marker, 1)
                            explanation = exp_sol[0].strip()
                            solution_section = exp_sol[1].strip()
                            break
                else:
                    explanation = remaining.strip()
                    solution_section = ""
            else:
                solution_section = content
        else:
            solution_section = content
        
        # Extract from markdown blocks
        if "```" in solution_section:
            start_idx = solution_section.find("```")
            # Skip the opening ```language
            newline_idx = solution_section.find("\n", start_idx)
            if newline_idx != -1:
                start_idx = newline_idx + 1
            else:
                start_idx = start_idx + 3
                
            end_idx = solution_section.find("```", start_idx)
            if end_idx != -1:
                solution = solution_section[start_idx:end_idx].strip()
            else:
                solution = solution_section[start_idx:].strip()
        else:
            solution = solution_section.strip()
        
        if not solution:
            return {
                'success': False,
                'error': 'No solution content generated'
            }
        
        return {
            'success': True,
            'solution': solution,
            'explanation': explanation
        }
    
    def _create_cautious_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str, language_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create solution using cautious approach."""
        return self._create_specialized_solution(task, classification, context, language_info)
    
    def _create_hybrid_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str, language_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create solution for hybrid tasks."""
        return self._create_specialized_solution(task, classification, context, language_info)
    
    def _create_generic_solution(self, task: Dict[str, Any], context: str, reason: str = None) -> Dict[str, Any]:
        """Create solution using generic, ultra-safe approach."""
        
        task_data = task['subtask_data']
        
        generic_prompt = f"""You are tasked with creating a simple, safe demonstration.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Working solution')}

{context}

{"FALLBACK REASON: " + reason if reason else ""}

Create a minimal Python demonstration that:
1. Uses ONLY built-in Python features (no imports except: os, sys, json, time, math, random)
2. Creates sample data instead of requiring input
3. Demonstrates the concept with print statements
4. Runs quickly and exits cleanly
5. Is completely self-contained

Format your response as:
EXPLANATION:
[Brief explanation]

SOLUTION:
```python
# Ultra-safe demonstration code
print("Demonstrating: {task['title']}")

# Your safe implementation here
# Use only built-in Python features
# Include sample data
# Show results with print()

print("Demonstration complete")
```

Focus on creating a working example that runs without any issues."""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": generic_prompt}]
            )
            
            content = response['message']['content']
            return self._extract_solution(content)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Generic solution creation failed: {str(e)}'
            }