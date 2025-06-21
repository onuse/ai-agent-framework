from typing import Dict, Any, List, Optional

def create_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Create solution with robust fallback handling and multi-language support."""
        
        approach = classification.get('approach', 'specialized')
        domain = classification.get('primary_domain', 'code')
        
        # For code tasks, detect programming language
        language_info = None
        if domain in ['code', 'ui', 'data', 'game']:
            language_info = self.language_classifier.classify_language(task)
            print(f"[LANGUAGE] Detected: {language_info['language']} (confidence: {language_info['confidence']:.2f})")
            if language_info.get('reason'):
                print(f"[LANGUAGE] {language_info['reason']}")
        
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
    
def _create_specialized_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str, language_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create solution using specialized domain approach with language awareness."""
    
    domain = classification['primary_domain']
    
    try:
        # For code domains with language detection, use multi-language creator
        if domain in ['code', 'ui', 'data', 'game'] and language_info and language_info.get('is_programming_task'):
            language = language_info['language']
            result = self.multilang_code_creator.generate_solution(task, language, context)
            if result['success']:
                result['approach_used'] = 'specialized_multilang'
                result['domain'] = domain
                result['language'] = language
            return result
        else:
            # Use traditional domain-specific approach
            solution_creator = SolutionCreatorFactory.create_solution_creator(domain, self.model_name)
            result = solution_creator.generate_solution(task, context)
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

def _create_cautious_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str, language_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create solution using specialized approach with generic fallback prompting."""
    
    domain = classification['primary_domain']
    confidence = classification['confidence']
    
    # For code tasks with language info, use language-aware cautious approach
    if domain in ['code', 'ui', 'data', 'game'] and language_info and language_info.get('is_programming_task'):
        language = language_info['language']
        cautious_prompt = self._create_cautious_multilang_prompt(task, domain, language, context, confidence)
    else:
        # Use traditional cautious approach
        cautious_prompt = self._create_cautious_prompt(task, domain, context, confidence)
    
    try:
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": cautious_prompt}]
        )
        
        content = response['message']['content']
        
        # Extract solution
        if language_info and language_info.get('is_programming_task'):
            result = self.multilang_code_creator._extract_solution(content, language_info['language'])
        else:
            solution_creator = SolutionCreatorFactory.create_solution_creator(domain, self.model_name)
            result = solution_creator._extract_solution(content)
        
        if result['success']:
            result['approach_used'] = 'specialized_cautious'
            result['domain'] = domain
            result['confidence'] = confidence
            if language_info:
                result['language'] = language_info.get('language', 'python')
        
        return result
        
    except Exception as e:
        # Final fallback to generic
        print(f"[ROBUST] Cautious approach failed, using generic fallback: {e}")
        return self._create_generic_solution(task, context, f"Cautious approach failed: {e}")

def _create_hybrid_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str, language_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create solution for tasks that span multiple domains."""
    
    primary_domain = classification['primary_domain']
    secondary_domain = classification['secondary_domain']
    
    # Create hybrid prompt that acknowledges multiple domains and language
    if language_info and language_info.get('is_programming_task'):
        hybrid_prompt = self._create_hybrid_multilang_prompt(task, primary_domain, secondary_domain, language_info['language'], context)
    else:
        hybrid_prompt = self._create_hybrid_prompt(task, primary_domain, secondary_domain, context)
    
    try:
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": hybrid_prompt}]
        )
        
        content = response['message']['content']
        
        # Use primary domain's solution creator for extraction
        if language_info and language_info.get('is_programming_task'):
            result = self.multilang_code_creator._extract_solution(content, language_info['language'])
        else:
            solution_creator = SolutionCreatorFactory.create_solution_creator(primary_domain, self.model_name)
            result = solution_creator._extract_solution(content)
        
        if result['success']:
            result['approach_used'] = 'hybrid'
            result['primary_domain'] = primary_domain
            result['secondary_domain'] = secondary_domain
            if language_info:
                result['language'] = language_info.get('language', 'python')
        
        return result
        
    except Exception as e:
        # Fallback to primary domain only
        print(f"[ROBUST] Hybrid approach failed, using primary domain: {e}")
        return self._create_specialized_solution(task, {'primary_domain': primary_domain}, context, language_info)

def _create_cautious_multilang_prompt(self, task: Dict[str, Any], domain: str, language: str, context: str, confidence: float) -> str:
    """Create a cautious prompt that's both domain and language aware."""
    
    task_data = task['subtask_data']
    
    domain_guidance = {
        'code': f"Focus on writing clean, working {language} code with good practices.",
        'ui': f"Focus on intuitive, user-friendly {language} interface design.",
        'data': f"Focus on clear data analysis using {language} with appropriate libraries.",
        'game': f"Focus on engaging, playable game mechanics in {language}."
    }
    
    guidance = domain_guidance.get(domain, f"Focus on practical, working {language} solutions.")
    
    # Get language info for better guidance
    lang_info = self.language_classifier.get_language_info(language)
    
    return f"""You are working on a {domain} task using {lang_info['name']} with moderate confidence in classification.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Working solution')}
LANGUAGE: {lang_info['name']}

{context}

{guidance} Keep your approach practical and straightforward.

Key {lang_info['name']} considerations:
- {lang_info['description']}
- Common frameworks: {', '.join(lang_info['common_frameworks'][:3])}
- Follow {lang_info['name']} best practices

Create a solution that:
1. Clearly addresses the stated requirements using {lang_info['name']}
2. Uses appropriate {lang_info['name']} tools and patterns
3. Is well-documented with clear comments
4. Includes proper error handling
5. Is immediately usable

Format your response as:
EXPLANATION:
[Your approach and reasoning for {lang_info['name']} implementation]

CODE:
```{language}
[Your complete {lang_info['name']} solution]
```

Prioritize functionality and clarity over complexity. Use idiomatic {lang_info['name']} patterns."""

def _create_hybrid_multilang_prompt(self, task: Dict[str, Any], primary_domain: str, secondary_domain: str, language: str, context: str) -> str:
    """Create a prompt for tasks that span multiple domains with language awareness."""
    
    task_data = task['subtask_data']
    lang_info = self.language_classifier.get_language_info(language)
    
    return f"""You are working on a complex task that combines {primary_domain} and {secondary_domain} elements using {lang_info['name']}.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Hybrid solution')}
LANGUAGE: {lang_info['name']}

{context}

This task requires expertise in both domains using {lang_info['name']}:
- PRIMARY FOCUS: {primary_domain} - This should be your main approach
- SECONDARY CONSIDERATION: {secondary_domain} - Integrate these aspects as needed
- IMPLEMENTATION: Use {lang_info['name']} best practices and appropriate frameworks

{lang_info['name']} considerations:
- {lang_info['description']}
- Recommended frameworks: {', '.join(lang_info['common_frameworks'][:2])}

Create a solution that:
1. Primarily follows {primary_domain} best practices in {lang_info['name']}
2. Incorporates relevant {secondary_domain} elements
3. Uses idiomatic {lang_info['name']} patterns and conventions
4. Is cohesive and well-integrated
5. Clearly addresses all requirements

Focus on creating a unified {lang_info['name']} solution rather than separate components.

Format your response as:
EXPLANATION:
[Your approach for integrating both domains using {lang_info['name']}]

CODE:
```{language}
[Your complete integrated {lang_info['name']} solution]
```

Ensure the solution works as a cohesive whole while leveraging both domains in idiomatic {lang_info['name']}."""

def _create_generic_solution(self, task: Dict[str, Any], context: str, reason: str = None) -> Dict[str, Any]:
    """Create solution using generic, safe approach."""
    
    task_data = task['subtask_data']
    
    generic_prompt = f"""You are tasked with completing a specific objective. Approach this systematically and practically.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Working solution')}

{context}

{"FALLBACK REASON: " + reason if reason else ""}

Create a practical solution that:
1. Addresses the core requirements clearly
2. Is well-structured and easy to understand
3. Includes appropriate error handling
4. Provides clear output or results
5. Is production-ready and maintainable

If this requires code, use Python. If this requires written content, use clear, professional language.
If this requires data analysis, use standard libraries like pandas and matplotlib.
If this requires a user interface, use tkinter.

Format your response as:
EXPLANATION:
[Brief explanation of your approach]

SOLUTION:
```
[Your complete solution]
```

Focus on creating a working, reliable solution rather than trying to be sophisticated."""

    try:
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": generic_prompt}]
        )
        
        content = response['message']['content']
        
        # Extract solution using generic pattern
        explanation = ""
        solution = ""
        
        if "EXPLANATION:" in content:
            parts = content.split("EXPLANATION:", 1)
            if len(parts) > 1:
                remaining = parts[1]
                if "SOLUTION:" in remaining:
                    exp_sol = remaining.split("SOLUTION:", 1)
                    explanation = exp_sol[0].strip()
                    solution_section = exp_sol[1].strip()
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
                'error': 'No solution content generated',
                'approach_used': 'generic_failed'
            }
        
        return {
            'success': True,
            'solution': solution,
            'explanation': explanation,
            'approach_used': 'generic',
            'fallback_reason': reason
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Generic solution creation failed: {str(e)}',
            'approach_used': 'generic_failed'
        }

def _create_cautious_prompt(self, task: Dict[str, Any], domain: str, context: str, confidence: float) -> str:
    """Create a cautious prompt that's domain-aware but not overly specialized."""
    
    task_data = task['subtask_data']
    
    domain_guidance = {
        'code': "Focus on writing clean, working code with good practices.",
        'creative': "Focus on engaging, well-structured creative content.",
        'data': "Focus on clear data analysis with appropriate visualizations.",
        'ui': "Focus on intuitive, user-friendly interface design.",
        'research': "Focus on well-organized, informative research content.",
        'game': "Focus on engaging, playable game mechanics."
    }
    
    guidance = domain_guidance.get(domain, "Focus on practical, working solutions.")
    
    return f"""You are working on a {domain} task with moderate confidence in classification.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Working solution')}

{context}

{guidance} Keep your approach practical and straightforward.

Create a solution that:
1. Clearly addresses the stated requirements
2. Uses appropriate tools and methods for {domain} tasks
3. Is well-documented and easy to understand
4. Includes proper error handling
5. Is immediately usable

Format your response as:
EXPLANATION:
[Your approach and reasoning]

SOLUTION:
```
[Your complete solution]
```

Prioritize functionality and clarity over complexity."""

def _create_hybrid_prompt(self, task: Dict[str, Any], primary_domain: str, secondary_domain: str, context: str) -> str:
    """Create a prompt for tasks that span multiple domains."""
    
    task_data = task['subtask_data']
    
    return f"""You are working on a complex task that combines {primary_domain} and {secondary_domain} elements.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Hybrid solution')}

{context}

This task requires expertise in both domains:
- PRIMARY FOCUS: {primary_domain} - This should be your main approach
- SECONDARY CONSIDERATION: {secondary_domain} - Integrate these aspects as needed

Create a solution that:
1. Primarily follows {primary_domain} best practices
2. Incorporates relevant {secondary_domain} elements
3. Balances both domains appropriately
4. Is cohesive and well-integrated
5. Clearly addresses all requirements

Focus on creating a unified solution rather than separate components.

Format your response as:
EXPLANATION:
[Your approach for integrating both domains]

SOLUTION:
```
[Your complete integrated solution]
```

Ensure the solution works as a cohesive whole while leveraging both domains."""

from typing import Dict, Any, List
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
        """Create solution with robust fallback handling."""
        
        approach = classification.get('approach', 'specialized')
        
        try:
            if approach == 'generic_fallback':
                return self._create_generic_solution(task, context, classification.get('fallback_reason'))
            elif approach == 'specialized_cautious':
                return self._create_cautious_solution(task, classification, context)
            elif approach == 'hybrid':
                return self._create_hybrid_solution(task, classification, context)
            else:
                return self._create_specialized_solution(task, classification, context)
                
        except Exception as e:
            # Fallback to generic approach on any error
            print(f"[ROBUST] Specialized approach failed: {e}")
            return self._create_generic_solution(task, context, f"Specialized approach failed: {e}")
    
    def _create_specialized_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Create solution using specialized domain approach."""
        
        domain = classification['primary_domain']
        solution_creator = SolutionCreatorFactory.create_solution_creator(domain, self.model_name)
        
        try:
            result = solution_creator.generate_solution(task, context)
            if result['success']:
                result['approach_used'] = 'specialized'
                result['domain'] = domain
            return result
        except Exception as e:
            # Fallback to cautious approach
            print(f"[ROBUST] Specialized creation failed, trying cautious approach: {e}")
            return self._create_cautious_solution(task, classification, context)
    
    def _create_cautious_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Create solution using specialized approach with generic fallback prompting."""
        
        domain = classification['primary_domain']
        confidence = classification['confidence']
        
        # Use specialized creator but with more generic, safer prompting
        solution_creator = SolutionCreatorFactory.create_solution_creator(domain, self.model_name)
        
        # Override the prompt to be more generic while keeping domain focus
        cautious_prompt = self._create_cautious_prompt(task, domain, context, confidence)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": cautious_prompt}]
            )
            
            content = response['message']['content']
            result = solution_creator._extract_solution(content)
            
            if result['success']:
                result['approach_used'] = 'specialized_cautious'
                result['domain'] = domain
                result['confidence'] = confidence
            
            return result
            
        except Exception as e:
            # Final fallback to generic
            print(f"[ROBUST] Cautious approach failed, using generic fallback: {e}")
            return self._create_generic_solution(task, context, f"Cautious approach failed: {e}")
    
    def _create_hybrid_solution(self, task: Dict[str, Any], classification: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Create solution for tasks that span multiple domains."""
        
        primary_domain = classification['primary_domain']
        secondary_domain = classification['secondary_domain']
        
        # Create hybrid prompt that acknowledges multiple domains
        hybrid_prompt = self._create_hybrid_prompt(task, primary_domain, secondary_domain, context)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": hybrid_prompt}]
            )
            
            content = response['message']['content']
            
            # Use primary domain's solution creator for extraction
            solution_creator = SolutionCreatorFactory.create_solution_creator(primary_domain, self.model_name)
            result = solution_creator._extract_solution(content)
            
            if result['success']:
                result['approach_used'] = 'hybrid'
                result['primary_domain'] = primary_domain
                result['secondary_domain'] = secondary_domain
            
            return result
            
        except Exception as e:
            # Fallback to primary domain only
            print(f"[ROBUST] Hybrid approach failed, using primary domain: {e}")
            return self._create_specialized_solution(task, {'primary_domain': primary_domain}, context)
    
    def _create_generic_solution(self, task: Dict[str, Any], context: str, reason: str = None) -> Dict[str, Any]:
        """Create solution using generic, safe approach."""
        
        task_data = task['subtask_data']
        
        generic_prompt = f"""You are tasked with completing a specific objective. Approach this systematically and practically.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Working solution')}

{context}

{"FALLBACK REASON: " + reason if reason else ""}

Create a practical solution that:
1. Addresses the core requirements clearly
2. Is well-structured and easy to understand
3. Includes appropriate error handling
4. Provides clear output or results
5. Is production-ready and maintainable

If this requires code, use Python. If this requires written content, use clear, professional language.
If this requires data analysis, use standard libraries like pandas and matplotlib.
If this requires a user interface, use tkinter.

Format your response as:
EXPLANATION:
[Brief explanation of your approach]

SOLUTION:
```
[Your complete solution]
```

Focus on creating a working, reliable solution rather than trying to be sophisticated."""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": generic_prompt}]
            )
            
            content = response['message']['content']
            
            # Extract solution using generic pattern
            explanation = ""
            solution = ""
            
            if "EXPLANATION:" in content:
                parts = content.split("EXPLANATION:", 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    if "SOLUTION:" in remaining:
                        exp_sol = remaining.split("SOLUTION:", 1)
                        explanation = exp_sol[0].strip()
                        solution_section = exp_sol[1].strip()
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
                    'error': 'No solution content generated',
                    'approach_used': 'generic_failed'
                }
            
            return {
                'success': True,
                'solution': solution,
                'explanation': explanation,
                'approach_used': 'generic',
                'fallback_reason': reason
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Generic solution creation failed: {str(e)}',
                'approach_used': 'generic_failed'
            }
    
    def _create_cautious_prompt(self, task: Dict[str, Any], domain: str, context: str, confidence: float) -> str:
        """Create a cautious prompt that's domain-aware but not overly specialized."""
        
        task_data = task['subtask_data']
        
        domain_guidance = {
            'code': "Focus on writing clean, working code with good practices.",
            'creative': "Focus on engaging, well-structured creative content.",
            'data': "Focus on clear data analysis with appropriate visualizations.",
            'ui': "Focus on intuitive, user-friendly interface design.",
            'research': "Focus on well-organized, informative research content.",
            'game': "Focus on engaging, playable game mechanics."
        }
        
        guidance = domain_guidance.get(domain, "Focus on practical, working solutions.")
        
        return f"""You are working on a {domain} task with moderate confidence in classification.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Working solution')}

{context}

{guidance} Keep your approach practical and straightforward.

Create a solution that:
1. Clearly addresses the stated requirements
2. Uses appropriate tools and methods for {domain} tasks
3. Is well-documented and easy to understand
4. Includes proper error handling
5. Is immediately usable

Format your response as:
EXPLANATION:
[Your approach and reasoning]

SOLUTION:
```
[Your complete solution]
```

Prioritize functionality and clarity over complexity."""
    
    def _create_hybrid_prompt(self, task: Dict[str, Any], primary_domain: str, secondary_domain: str, context: str) -> str:
        """Create a prompt for tasks that span multiple domains."""
        
        task_data = task['subtask_data']
        
        return f"""You are working on a complex task that combines {primary_domain} and {secondary_domain} elements.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Hybrid solution')}

{context}

This task requires expertise in both domains:
- PRIMARY FOCUS: {primary_domain} - This should be your main approach
- SECONDARY CONSIDERATION: {secondary_domain} - Integrate these aspects as needed

Create a solution that:
1. Primarily follows {primary_domain} best practices
2. Incorporates relevant {secondary_domain} elements
3. Balances both domains appropriately
4. Is cohesive and well-integrated
5. Clearly addresses all requirements

Focus on creating a unified solution rather than separate components.

Format your response as:
EXPLANATION:
[Your approach for integrating both domains]

SOLUTION:
```
[Your complete integrated solution]
```

Ensure the solution works as a cohesive whole while leveraging both domains."""