from typing import Dict, Any, List, Optional
import re

class TaskClassifier:
    """Classifies tasks into different domains for specialized processing."""
    
    def __init__(self):
        self.domain_patterns = {
            'code': {
                'keywords': [
                    'implement', 'code', 'function', 'class', 'api', 'algorithm',
                    'program', 'script', 'application', 'software', 'system',
                    'framework', 'library', 'module', 'backend', 'frontend',
                    'database', 'server', 'client', 'build', 'develop'
                ],
                'technologies': [
                    'python', 'javascript', 'java', 'c++', 'html', 'css',
                    'react', 'django', 'flask', 'node', 'sql', 'git',
                    'docker', 'kubernetes', 'aws', 'rest', 'graphql'
                ],
                'patterns': [
                    r'\b(def|class|import|function)\b',
                    r'\b(\.py|\.js|\.html|\.css)\b',
                    r'\b(git|github|repository)\b'
                ]
            },
            'creative': {
                'keywords': [
                    'write', 'story', 'novel', 'chapter', 'character', 'plot',
                    'narrative', 'dialogue', 'scene', 'poem', 'script',
                    'screenplay', 'book', 'fiction', 'creative', 'literature',
                    'author', 'compose', 'draft', 'manuscript'
                ],
                'genres': [
                    'science fiction', 'fantasy', 'mystery', 'romance',
                    'thriller', 'horror', 'drama', 'comedy', 'adventure'
                ],
                'patterns': [
                    r'\b(chapter|page|word count)\b',
                    r'\b(protagonist|antagonist|character)\b',
                    r'\b(first person|third person)\b'
                ]
            },
            'data': {
                'keywords': [
                    'analyze', 'data', 'statistics', 'chart', 'graph', 'plot',
                    'visualization', 'dataset', 'csv', 'excel', 'database',
                    'query', 'report', 'metrics', 'analytics', 'insights',
                    'correlation', 'regression', 'machine learning', 'ai',
                    'pandas', 'numpy', 'matplotlib', 'seaborn'
                ],
                'file_types': [
                    'csv', 'xlsx', 'json', 'xml', 'sql', 'parquet'
                ],
                'patterns': [
                    r'\b(pandas|numpy|matplotlib|seaborn|plotly)\b',
                    r'\b(\.csv|\.xlsx|\.json)\b',
                    r'\b(mean|median|std|correlation)\b'
                ]
            },
            'ui': {
                'keywords': [
                    'interface', 'ui', 'ux', 'design', 'layout', 'user',
                    'screen', 'page', 'form', 'button', 'menu', 'navigation',
                    'responsive', 'mobile', 'desktop', 'web', 'gui',
                    'tkinter', 'qt', 'gtk', 'javafx', 'swing'
                ],
                'ui_elements': [
                    'button', 'textbox', 'dropdown', 'checkbox', 'radio',
                    'slider', 'menu', 'toolbar', 'dialog', 'window'
                ],
                'patterns': [
                    r'\b(tkinter|gui|window|dialog)\b',
                    r'\b(css|html|bootstrap|react)\b',
                    r'\b(responsive|mobile|desktop)\b'
                ]
            },
            'research': {
                'keywords': [
                    'research', 'investigate', 'study', 'analyze', 'gather',
                    'information', 'facts', 'sources', 'references', 'review',
                    'survey', 'examine', 'explore', 'documentation', 'report',
                    'summary', 'overview', 'background', 'literature'
                ],
                'academic': [
                    'paper', 'journal', 'article', 'citation', 'bibliography',
                    'methodology', 'hypothesis', 'conclusion', 'abstract'
                ],
                'patterns': [
                    r'\b(research|investigate|study)\b',
                    r'\b(sources|references|citations)\b',
                    r'\b(academic|scholarly|peer-reviewed)\b'
                ]
            },
            'game': {
                'keywords': [
                    'game', 'gaming', 'player', 'level', 'score', 'character',
                    'enemy', 'weapon', 'physics', 'graphics', 'engine',
                    'raycast', 'collision', 'animation', 'sprite', 'texture',
                    'doom', 'mario', 'platformer', 'puzzle', 'arcade'
                ],
                'game_types': [
                    'fps', 'rpg', 'rts', 'platformer', 'puzzle', 'arcade',
                    'shooter', 'adventure', 'simulation', 'strategy'
                ],
                'patterns': [
                    r'\b(pygame|unity|unreal|godot)\b',
                    r'\b(fps|rpg|mmo|rts)\b',
                    r'\b(raycast|collision|physics)\b'
                ]
            }
        }
    
    def classify_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a task into domain categories with confidence scores and fallback handling."""
        
        # Extract text for analysis
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()
        deliverable = task.get('subtask_data', {}).get('deliverable', '').lower()
        
        combined_text = f"{title} {description} {deliverable}"
        
        # Calculate confidence scores for each domain
        domain_scores = {}
        
        for domain, patterns in self.domain_patterns.items():
            score = self._calculate_domain_score(combined_text, patterns)
            domain_scores[domain] = score
        
        # Determine primary and secondary domains
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        primary_domain = sorted_domains[0][0]
        primary_confidence = sorted_domains[0][1]
        
        secondary_domain = sorted_domains[1][0] if len(sorted_domains) > 1 else None
        secondary_confidence = sorted_domains[1][1] if len(sorted_domains) > 1 else 0.0
        
        # Detect hybrid tasks (multiple high-confidence domains)
        is_hybrid = self._is_hybrid_task(domain_scores)
        
        # Apply confidence thresholds and fallback logic
        if primary_confidence < 0.15:
            # Very low confidence - fall back to generic code approach
            primary_domain = 'code'
            primary_confidence = 0.5
            approach = 'generic_fallback'
        elif primary_confidence < 0.35:
            # Low confidence - use cautious specialized approach
            approach = 'specialized_cautious'
        elif is_hybrid:
            # Multiple domains detected - use hybrid approach
            approach = 'hybrid'
        else:
            # High confidence - use full specialized approach
            approach = 'specialized'
        
        return {
            'primary_domain': primary_domain,
            'secondary_domain': secondary_domain,
            'confidence': primary_confidence,
            'secondary_confidence': secondary_confidence,
            'all_scores': domain_scores,
            'is_confident': primary_confidence > 0.35,
            'is_hybrid': is_hybrid,
            'approach': approach,
            'fallback_reason': self._get_fallback_reason(primary_confidence, is_hybrid)
        }
    
    def _is_hybrid_task(self, domain_scores: Dict[str, float]) -> bool:
        """Detect if task spans multiple domains."""
        
        # Sort scores in descending order
        sorted_scores = sorted(domain_scores.values(), reverse=True)
        
        if len(sorted_scores) < 2:
            return False
        
        # If top 2 scores are both high and close together, it's hybrid
        top_score = sorted_scores[0]
        second_score = sorted_scores[1]
        
        # Hybrid criteria:
        # 1. Both scores are reasonably high (> 0.25)
        # 2. The difference between them is small (< 0.3)
        if top_score > 0.25 and second_score > 0.25 and (top_score - second_score) < 0.3:
            return True
        
        return False
    
    def _get_fallback_reason(self, confidence: float, is_hybrid: bool) -> Optional[str]:
        """Get explanation for why fallback was triggered."""
        
        if confidence < 0.15:
            return "Very low classification confidence - using generic approach"
        elif confidence < 0.35:
            return "Low classification confidence - using cautious specialized approach"
        elif is_hybrid:
            return "Multiple domains detected - using hybrid approach"
        else:
            return None
    
    def _calculate_domain_score(self, text: str, patterns: Dict[str, List]) -> float:
        """Calculate confidence score for a specific domain."""
        
        total_score = 0.0
        total_weight = 0.0
        
        # Check keywords (weight: 1.0)
        keyword_matches = sum(1 for keyword in patterns.get('keywords', []) if keyword in text)
        if patterns.get('keywords'):
            total_score += (keyword_matches / len(patterns['keywords'])) * 1.0
            total_weight += 1.0
        
        # Check secondary terms (weight: 0.7)
        for category in ['technologies', 'genres', 'file_types', 'ui_elements', 'academic', 'game_types']:
            if category in patterns:
                matches = sum(1 for term in patterns[category] if term in text)
                if patterns[category]:
                    total_score += (matches / len(patterns[category])) * 0.7
                    total_weight += 0.7
        
        # Check regex patterns (weight: 0.5)
        if 'patterns' in patterns:
            pattern_matches = sum(1 for pattern in patterns['patterns'] 
                                if re.search(pattern, text, re.IGNORECASE))
            if patterns['patterns']:
                total_score += (pattern_matches / len(patterns['patterns'])) * 0.5
                total_weight += 0.5
        
        # Return normalized score
        return total_score / total_weight if total_weight > 0 else 0.0
    
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
    
    def suggest_specialized_approach(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest specialized processing approach based on classification."""
        
        domain = classification['primary_domain']
        confidence = classification['confidence']
        domain_info = self.get_domain_info(domain)
        
        suggestions = {
            'domain': domain,
            'confidence': confidence,
            'execution_strategy': domain_info['execution_type'],
            'validation_priorities': domain_info['validation_focus'],
            'recommended_file_ext': domain_info['file_extensions'][0],
            'specialized_prompting': True if confidence > 0.3 else False
        }
        
        return suggestions