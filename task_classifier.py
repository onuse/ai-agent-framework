import json
from typing import Dict, Any, List, Optional
from llm_client import LLMClient
from config import get_llm_config

class TaskClassifier:
    """LLM-powered task classifier that understands context and intent."""

    def __init__(self, model_name: str = None):
        # Get LLM configuration
        llm_config = get_llm_config()
        self.model_name = model_name or llm_config["model"]

        # Initialize LLM client
        self.llm_client = LLMClient(
            provider=llm_config["provider"],
            model=self.model_name,
            api_key=llm_config.get("api_key"),
            base_url=llm_config.get("base_url")
        )
        self.domain_definitions = {
            'code': {
                'description': 'Software development, programming, building applications, scripts, APIs, algorithms, or any technical implementation',
                'examples': ['Create a calculator', 'Build a web API', 'Implement sorting algorithm', 'Debug Python code']
            },
            'creative': {
                'description': 'Creative writing, storytelling, content creation, poetry, scripts, or artistic expression',
                'examples': ['Write a short story', 'Create a poem about nature', 'Draft a screenplay', 'Compose song lyrics']
            },
            'data': {
                'description': 'Data analysis, statistics, visualization, machine learning, or processing datasets',
                'examples': ['Analyze sales trends', 'Create data visualization', 'Process CSV files', 'Build ML model']
            },
            'ui': {
                'description': 'User interface design, user experience, creating visual interfaces, or improving usability',
                'examples': ['Design a login form', 'Create mobile app interface', 'Improve website UX', 'Build GUI application']
            },
            'research': {
                'description': 'Information gathering, analysis, documentation, reports, or investigative work',
                'examples': ['Research market trends', 'Write technical documentation', 'Analyze competitors', 'Create project report']
            },
            'game': {
                'description': 'Game development, interactive entertainment, game mechanics, or gaming-related content',
                'examples': ['Create a puzzle game', 'Build physics engine', 'Design game characters', 'Implement collision detection']
            }
        }
    
    def classify_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Classify task using LLM understanding of context and intent."""
        
        # Extract task information
        title = task.get('title', '')
        description = task.get('description', '')
        deliverable = task.get('subtask_data', {}).get('deliverable', '')
        
        # Create classification prompt
        prompt = self._create_classification_prompt(title, description, deliverable)
        
        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            classification_result = self._parse_classification_response(content)
            
            # Validate and enhance the result
            return self._validate_and_enhance_classification(classification_result, task)
            
        except Exception as e:
            print(f"[CLASSIFIER] LLM classification failed: {e}")
            # Fallback to simple heuristic
            return self._fallback_classification(title, description, deliverable)
    
    def _create_classification_prompt(self, title: str, description: str, deliverable: str) -> str:
        """Create a comprehensive classification prompt for the LLM."""
        
        # Build domain descriptions
        domain_descriptions = []
        for domain, info in self.domain_definitions.items():
            examples_str = ", ".join(f'"{ex}"' for ex in info['examples'][:2])
            domain_descriptions.append(f"- **{domain}**: {info['description']}\n  Examples: {examples_str}")
        
        domains_text = "\n".join(domain_descriptions)
        
        prompt = f"""You are an expert task classifier. Analyze the following task and classify it into the most appropriate domain.

TASK TO CLASSIFY:
Title: "{title}"
Description: "{description}"
Expected Deliverable: "{deliverable}"

AVAILABLE DOMAINS:
{domains_text}

CLASSIFICATION INSTRUCTIONS:
1. Read the task carefully and understand the core intent
2. Consider what type of work is actually being requested
3. Think about what skills and tools would be needed
4. Determine if this spans multiple domains (hybrid task)
5. Assign confidence based on how clear the classification is

Respond in JSON format:
{{
    "primary_domain": "domain_name",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why you chose this domain",
    "secondary_domain": "domain_name or null",
    "is_hybrid": true/false,
    "approach": "specialized|specialized_cautious|hybrid|generic_fallback",
    "key_indicators": ["list", "of", "key", "words", "or", "phrases", "that", "influenced", "decision"]
}}

GUIDELINES:
- confidence > 0.8: Very clear classification → approach = "specialized"
- confidence 0.5-0.8: Clear but some ambiguity → approach = "specialized_cautious" 
- Multiple domains with similar confidence → approach = "hybrid"
- confidence < 0.5: Unclear classification → approach = "generic_fallback"
- is_hybrid = true if task clearly spans 2+ domains significantly

Focus on the ACTUAL WORK being requested, not just keywords."""
        
        return prompt
    
    def _parse_classification_response(self, content: str) -> Dict[str, Any]:
        """Parse the LLM's classification response."""
        
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
            print(f"[CLASSIFIER] Failed to parse LLM response: {e}")
            print(f"[CLASSIFIER] Raw response: {content[:200]}...")
            raise
    
    def _validate_and_enhance_classification(self, result: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the classification result."""
        
        # Ensure required fields exist
        primary_domain = result.get('primary_domain', 'code')
        confidence = float(result.get('confidence', 0.5))
        
        # Validate domain exists
        if primary_domain not in self.domain_definitions:
            print(f"[CLASSIFIER] Invalid domain '{primary_domain}', defaulting to 'code'")
            primary_domain = 'code'
            confidence = 0.3
        
        # Determine approach if not provided or invalid
        approach = result.get('approach')
        if not approach or approach not in ['specialized', 'specialized_cautious', 'hybrid', 'generic_fallback']:
            if confidence > 0.8:
                approach = 'specialized'
            elif confidence > 0.5:
                approach = 'specialized_cautious'
            elif result.get('is_hybrid', False):
                approach = 'hybrid'
            else:
                approach = 'generic_fallback'
        
        # Build enhanced result
        enhanced_result = {
            'primary_domain': primary_domain,
            'secondary_domain': result.get('secondary_domain'),
            'confidence': confidence,
            'reasoning': result.get('reasoning', 'LLM-based classification'),
            'is_hybrid': result.get('is_hybrid', False),
            'approach': approach,
            'key_indicators': result.get('key_indicators', []),
            'is_confident': confidence > 0.5,
            'fallback_reason': self._get_fallback_reason(confidence, result.get('is_hybrid', False), approach),
            'classification_method': 'llm_powered'
        }
        
        return enhanced_result
    
    def _get_fallback_reason(self, confidence: float, is_hybrid: bool, approach: str) -> Optional[str]:
        """Generate fallback reason based on classification results."""
        
        if approach == 'generic_fallback':
            return f"Low confidence classification ({confidence:.2f}) - using generic approach"
        elif approach == 'specialized_cautious':
            return f"Moderate confidence ({confidence:.2f}) - using cautious specialized approach"
        elif approach == 'hybrid':
            return "Multiple domains detected - using hybrid approach"
        else:
            return None
    
    def _fallback_classification(self, title: str, description: str, deliverable: str) -> Dict[str, Any]:
        """Simple fallback classification when LLM fails."""
        
        combined_text = f"{title} {description} {deliverable}".lower()
        
        # Simple keyword-based fallback
        if any(word in combined_text for word in ['story', 'write', 'creative', 'poem', 'novel']):
            primary_domain = 'creative'
            confidence = 0.6
        elif any(word in combined_text for word in ['data', 'analyze', 'chart', 'csv', 'statistics']):
            primary_domain = 'data'
            confidence = 0.6
        elif any(word in combined_text for word in ['game', 'player', 'level', 'arcade', 'puzzle']):
            primary_domain = 'game'
            confidence = 0.6
        elif any(word in combined_text for word in ['interface', 'ui', 'design', 'button', 'form']):
            primary_domain = 'ui'
            confidence = 0.6
        elif any(word in combined_text for word in ['research', 'investigate', 'report', 'study']):
            primary_domain = 'research'
            confidence = 0.6
        else:
            primary_domain = 'code'
            confidence = 0.5
        
        return {
            'primary_domain': primary_domain,
            'secondary_domain': None,
            'confidence': confidence,
            'reasoning': 'Fallback keyword-based classification',
            'is_hybrid': False,
            'approach': 'specialized_cautious',
            'key_indicators': ['fallback_classification'],
            'is_confident': confidence > 0.5,
            'fallback_reason': 'LLM classification failed - using keyword fallback',
            'classification_method': 'keyword_fallback'
        }
    
    def get_domain_info(self, domain: str) -> Dict[str, Any]:
        """Get information about a specific domain."""
        
        domain_info = {
            'code': {
                'description': 'Software development and programming tasks',
                'execution_type': 'subprocess',
                'validation_focus': ['syntax', 'runtime_errors', 'best_practices'],
                'file_extensions': ['.py', '.js', '.html', '.css', '.sql']
            },
            'creative': {
                'description': 'Creative writing and content generation',
                'execution_type': 'text_processing',
                'validation_focus': ['coherence', 'style', 'word_count', 'flow'],
                'file_extensions': ['.txt', '.md', '.doc']
            },
            'data': {
                'description': 'Data analysis and visualization tasks',
                'execution_type': 'data_processing',
                'validation_focus': ['data_quality', 'statistical_validity', 'visualization'],
                'file_extensions': ['.py', '.ipynb', '.csv', '.json']
            },
            'ui': {
                'description': 'User interface and user experience design',
                'execution_type': 'gui_application',
                'validation_focus': ['usability', 'responsiveness', 'accessibility'],
                'file_extensions': ['.py', '.html', '.css', '.js']
            },
            'research': {
                'description': 'Information gathering and analysis tasks',
                'execution_type': 'document_generation',
                'validation_focus': ['accuracy', 'completeness', 'citations'],
                'file_extensions': ['.md', '.txt', '.pdf', '.doc']
            },
            'game': {
                'description': 'Game development and interactive entertainment',
                'execution_type': 'game_application',
                'validation_focus': ['gameplay', 'performance', 'graphics'],
                'file_extensions': ['.py', '.js', '.cpp', '.cs']
            }
        }
        
        return domain_info.get(domain, domain_info['code'])
    
    def explain_classification(self, classification: Dict[str, Any]) -> str:
        """Generate human-readable explanation of the classification."""
        
        explanation = f"🏷️ Classified as '{classification['primary_domain']}' domain "
        explanation += f"with {classification['confidence']:.1%} confidence.\n"
        
        if classification.get('reasoning'):
            explanation += f"💭 Reasoning: {classification['reasoning']}\n"
        
        if classification.get('key_indicators'):
            indicators = ', '.join(classification['key_indicators'][:3])
            explanation += f"🔍 Key indicators: {indicators}\n"
        
        if classification.get('is_hybrid'):
            explanation += f"🔄 Hybrid task also involving: {classification.get('secondary_domain')}\n"
        
        explanation += f"⚙️ Approach: {classification['approach']}"
        
        return explanation