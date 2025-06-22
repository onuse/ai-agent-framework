import ollama
import json
from typing import Dict, Any, Optional

class LanguageClassifier:
    """LLM-powered language classifier for programming tasks."""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.supported_languages = {
            'javascript': {
                'name': 'JavaScript/Node.js',
                'description': 'Web development, browser apps, Node.js servers',
                'file_extensions': ['.js', '.jsx', '.ts', '.tsx', '.html'],
                'execution_command': 'node',
                'common_use_cases': ['web apps', 'browser games', 'SPAs', 'APIs', 'frontend']
            },
            'python': {
                'name': 'Python',
                'description': 'General purpose, data science, automation, web backends',
                'file_extensions': ['.py', '.ipynb'],
                'execution_command': 'python',
                'common_use_cases': ['data analysis', 'automation', 'AI/ML', 'desktop apps', 'web backends']
            },
            'java': {
                'name': 'Java',
                'description': 'Enterprise applications, Android development',
                'file_extensions': ['.java'],
                'execution_command': 'java',
                'common_use_cases': ['enterprise apps', 'Android', 'web services', 'desktop apps']
            },
            'cpp': {
                'name': 'C++',
                'description': 'High-performance applications, games, system programming',
                'file_extensions': ['.cpp', '.cxx', '.cc', '.h', '.hpp'],
                'execution_command': 'g++',
                'common_use_cases': ['games', 'system software', 'high-performance apps']
            },
            'csharp': {
                'name': 'C#',
                'description': 'Microsoft ecosystem, desktop and web applications',
                'file_extensions': ['.cs'],
                'execution_command': 'dotnet run',
                'common_use_cases': ['Windows apps', 'web APIs', 'desktop software', 'games']
            },
            'go': {
                'name': 'Go',
                'description': 'System programming, web services, cloud applications',
                'file_extensions': ['.go'],
                'execution_command': 'go run',
                'common_use_cases': ['web services', 'cloud apps', 'CLI tools', 'microservices']
            },
            'rust': {
                'name': 'Rust',
                'description': 'System programming, performance-critical applications',
                'file_extensions': ['.rs'],
                'execution_command': 'cargo run',
                'common_use_cases': ['system software', 'web assembly', 'performance apps']
            }
        }
    
    def classify_language(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Classify programming language using LLM understanding."""
        
        # Extract task information
        title = task.get('title', '')
        description = task.get('description', '')
        deliverable = task.get('subtask_data', {}).get('deliverable', '')
        
        # Check if this is even a programming task
        if not self._is_programming_task(title, description, deliverable):
            return {
                'language': 'none',
                'confidence': 1.0,
                'is_programming_task': False,
                'reasoning': 'Not a programming task'
            }
        
        # PRIORITY FIX: Check for explicit language mentions first
        explicit_language = self._check_explicit_language_mentions(title, description, deliverable)
        if explicit_language:
            return explicit_language
        
        # Create LLM classification prompt
        prompt = self._create_language_classification_prompt(title, description, deliverable)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            result = self._parse_language_response(content)
            
            # Validate and enhance result
            return self._validate_language_result(result, title, description, deliverable)
            
        except Exception as e:
            print(f"[LANGUAGE] LLM classification failed: {e}")
            # Fallback to simple heuristic
            return self._fallback_language_classification(title, description, deliverable)
    
    def _check_explicit_language_mentions(self, title: str, description: str, deliverable: str) -> Optional[Dict[str, Any]]:
        """Check for explicit language mentions with high priority."""
        
        combined_text = f"{title} {description} {deliverable}".lower()
        
        # Explicit language mentions (case-insensitive)
        explicit_patterns = {
            'javascript': ['javascript', 'js ', ' js', 'node.js', 'html5', 'canvas', 'browser game', 'web game'],
            'java': ['java ', ' java', 'android', 'spring boot'],
            'python': ['python', 'django', 'flask', 'pandas', 'numpy'],
            'cpp': ['c++', 'cpp', 'unreal', 'opengl'],
            'csharp': ['c#', 'csharp', 'c sharp', '.net', 'unity'],
            'go': ['golang', ' go ', 'gin framework'],
            'rust': ['rust ', 'cargo', 'wasm']
        }
        
        for language, patterns in explicit_patterns.items():
            for pattern in patterns:
                if pattern in combined_text:
                    return {
                        'language': language,
                        'confidence': 0.95,
                        'reasoning': f'Explicit mention detected: "{pattern}"',
                        'key_indicators': [pattern],
                        'is_programming_task': True,
                        'classification_method': 'explicit_mention',
                        'file_extension': self.supported_languages[language]['file_extensions'][0],
                        'execution_command': self.supported_languages[language]['execution_command']
                    }
        
        return None
    
    def _create_language_classification_prompt(self, title: str, description: str, deliverable: str) -> str:
        """Create LLM prompt for language classification."""
        
        # Build language options
        language_options = []
        for lang_code, info in self.supported_languages.items():
            use_cases = ", ".join(info['common_use_cases'][:3])
            language_options.append(f"- **{lang_code}** ({info['name']}): {info['description']} | Use cases: {use_cases}")
        
        languages_text = "\n".join(language_options)
        
        prompt = f"""You are an expert developer who determines the best programming language for a given task.

TASK TO ANALYZE:
Title: "{title}"
Description: "{description}"
Expected Deliverable: "{deliverable}"

AVAILABLE LANGUAGES:
{languages_text}

CLASSIFICATION GUIDELINES:
1. **Explicit mentions**: If a language is explicitly mentioned, choose it (high confidence)
2. **Platform context**: 
   - Web/browser → JavaScript
   - Data analysis → Python
   - Mobile (Android) → Java
   - High performance → C++
   - Microsoft ecosystem → C#
3. **Domain patterns**:
   - Web games → JavaScript
   - Desktop apps → Python/C#/Java
   - System tools → Go/Rust/C++
4. **Technology hints**:
   - HTML5/Canvas → JavaScript
   - Machine learning → Python
   - Enterprise → Java/C#

Respond in JSON format:
{{
    "language": "language_code",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your choice",
    "key_indicators": ["list", "of", "key", "words", "that", "influenced", "decision"],
    "alternative": "second_choice_if_uncertain"
}}

IMPORTANT:
- If multiple languages could work, choose the most appropriate for the specific context
- Higher confidence (0.8+) for explicit mentions or clear platform indicators
- Lower confidence (0.3-0.7) for ambiguous cases
- Consider what would be most practical for the stated goal"""
        
        return prompt
    
    def _parse_language_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response for language classification."""
        
        try:
            # Find JSON in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                result = json.loads(json_content)
                return result
            else:
                raise ValueError("No valid JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[LANGUAGE] Failed to parse LLM response: {e}")
            print(f"[LANGUAGE] Raw response: {content[:200]}...")
            raise
    
    def _validate_language_result(self, result: Dict[str, Any], title: str, description: str, deliverable: str) -> Dict[str, Any]:
        """Validate and enhance language classification result."""
        
        # Ensure required fields
        language = result.get('language', 'python')
        confidence = float(result.get('confidence', 0.5))
        
        # Validate language exists
        if language not in self.supported_languages:
            print(f"[LANGUAGE] Invalid language '{language}', defaulting to 'python'")
            language = 'python'
            confidence = 0.4
        
        # Build enhanced result
        enhanced_result = {
            'language': language,
            'confidence': confidence,
            'reasoning': result.get('reasoning', 'LLM-based classification'),
            'key_indicators': result.get('key_indicators', []),
            'alternative': result.get('alternative'),
            'is_programming_task': True,
            'classification_method': 'llm_powered',
            'file_extension': self.supported_languages[language]['file_extensions'][0],
            'execution_command': self.supported_languages[language]['execution_command']
        }
        
        return enhanced_result
    
    def _is_programming_task(self, title: str, description: str, deliverable: str) -> bool:
        """Quick check if this is a programming task."""
        
        combined_text = f"{title} {description} {deliverable}".lower()
        
        programming_indicators = [
            'code', 'program', 'script', 'app', 'application', 'software',
            'build', 'create', 'develop', 'implement', 'api', 'system',
            'web', 'game', 'calculator', 'tool', 'engine', 'framework'
        ]
        
        non_programming_indicators = [
            'write story', 'write poem', 'creative writing', 'essay',
            'research report', 'documentation only', 'analysis report'
        ]
        
        # Check for non-programming first
        if any(indicator in combined_text for indicator in non_programming_indicators):
            return False
        
        # Check for programming indicators
        return any(indicator in combined_text for indicator in programming_indicators)
    
    def _fallback_language_classification(self, title: str, description: str, deliverable: str) -> Dict[str, Any]:
        """Simple fallback classification when LLM fails."""
        
        combined_text = f"{title} {description} {deliverable}".lower()
        
        # IMPROVED fallback with explicit checks
        if any(word in combined_text for word in ['javascript', 'js', 'web', 'browser', 'html', 'canvas', 'html5']):
            return {
                'language': 'javascript',
                'confidence': 0.8,
                'reasoning': 'Fallback: Web/JavaScript keywords detected',
                'is_programming_task': True,
                'classification_method': 'keyword_fallback',
                'file_extension': '.js',
                'execution_command': 'node'
            }
        elif any(word in combined_text for word in ['java ', 'android', 'spring']):
            return {
                'language': 'java',
                'confidence': 0.7,
                'reasoning': 'Fallback: Java keywords detected',
                'is_programming_task': True,
                'classification_method': 'keyword_fallback',
                'file_extension': '.java',
                'execution_command': 'java'
            }
        else:
            return {
                'language': 'python',
                'confidence': 0.5,
                'reasoning': 'Fallback: Default to Python',
                'is_programming_task': True,
                'classification_method': 'default_fallback',
                'file_extension': '.py',
                'execution_command': 'python'
            }
    
    def get_language_info(self, language: str) -> Dict[str, Any]:
        """Get detailed information about a programming language."""
        
        if language not in self.supported_languages:
            language = 'python'  # Default fallback
        
        return self.supported_languages[language]
    
    def explain_classification(self, classification: Dict[str, Any]) -> str:
        """Generate human-readable explanation of language classification."""
        
        language = classification['language']
        confidence = classification['confidence']
        reasoning = classification.get('reasoning', 'No reasoning provided')
        
        explanation = f"🔤 Detected language: {language} ({confidence:.1%} confidence)\n"
        explanation += f"💭 Reasoning: {reasoning}\n"
        
        if classification.get('key_indicators'):
            indicators = ', '.join(classification['key_indicators'][:3])
            explanation += f"🔍 Key indicators: {indicators}\n"
        
        if classification.get('alternative'):
            explanation += f"🔄 Alternative consideration: {classification['alternative']}\n"
        
        method = classification.get('classification_method', 'unknown')
        explanation += f"⚙️ Method: {method}"
        
        return explanation