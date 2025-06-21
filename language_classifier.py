import re
from typing import Dict, Any, List, Optional

class LanguageClassifier:
    """Detects programming language from task description."""
    
    def __init__(self):
        self.language_patterns = {
            'javascript': {
                'keywords': [
                    'javascript', 'js', 'node.js', 'nodejs', 'npm', 'react', 'vue',
                    'angular', 'express', 'web app', 'frontend', 'backend api',
                    'json', 'ajax', 'dom', 'browser', 'typescript', 'ts'
                ],
                'frameworks': [
                    'react', 'vue.js', 'angular', 'express.js', 'next.js', 'svelte',
                    'nuxt', 'ember', 'backbone', 'jquery', 'lodash', 'webpack'
                ],
                'patterns': [
                    r'\b(node\.?js|npm|yarn)\b',
                    r'\b(react|vue|angular)\b',
                    r'\b(\.js|\.jsx|\.ts|\.tsx)\b',
                    r'\b(express|fastify|koa)\b'
                ],
                'file_extensions': ['.js', '.jsx', '.ts', '.tsx', '.mjs'],
                'execution_command': 'node'
            },
            'java': {
                'keywords': [
                    'java', 'jvm', 'spring', 'maven', 'gradle', 'android',
                    'swing', 'javafx', 'hibernate', 'junit', 'servlet',
                    'jsp', 'enterprise', 'microservice'
                ],
                'frameworks': [
                    'spring boot', 'spring mvc', 'hibernate', 'struts',
                    'junit', 'mockito', 'maven', 'gradle', 'tomcat'
                ],
                'patterns': [
                    r'\b(spring|hibernate|maven|gradle)\b',
                    r'\b(swing|javafx|android)\b',
                    r'\b(\.java|\.jar|\.war)\b',
                    r'\b(jvm|jdk|jre)\b'
                ],
                'file_extensions': ['.java'],
                'execution_command': 'java'
            },
            'cpp': {
                'keywords': [
                    'c++', 'cpp', 'cxx', 'c plus plus', 'stl', 'boost',
                    'cmake', 'make', 'gcc', 'g++', 'clang', 'visual studio',
                    'qt', 'opencv', 'opengl'
                ],
                'frameworks': [
                    'qt', 'boost', 'opencv', 'opengl', 'sfml', 'allegro',
                    'cmake', 'conan', 'vcpkg'
                ],
                'patterns': [
                    r'\b(c\+\+|cpp|cxx)\b',
                    r'\b(\.cpp|\.cxx|\.cc|\.h|\.hpp)\b',
                    r'\b(cmake|make|gcc|g\+\+)\b',
                    r'\b(std::|iostream|vector)\b'
                ],
                'file_extensions': ['.cpp', '.cxx', '.cc', '.h', '.hpp'],
                'execution_command': 'g++'
            },
            'csharp': {
                'keywords': [
                    'c#', 'csharp', 'dotnet', '.net', 'visual studio',
                    'wpf', 'winforms', 'asp.net', 'mvc', 'blazor',
                    'entity framework', 'nuget', 'xamarin'
                ],
                'frameworks': [
                    'asp.net', 'blazor', 'xamarin', 'unity', 'wpf',
                    'winforms', 'entity framework', 'mvc', 'web api'
                ],
                'patterns': [
                    r'\b(c#|\.net|dotnet)\b',
                    r'\b(\.cs|\.csproj|\.sln)\b',
                    r'\b(asp\.net|blazor|wpf)\b',
                    r'\b(using\s+System|namespace)\b'
                ],
                'file_extensions': ['.cs'],
                'execution_command': 'dotnet run'
            },
            'go': {
                'keywords': [
                    'go', 'golang', 'goroutine', 'channel', 'gin', 'echo',
                    'fiber', 'gorm', 'cobra', 'viper', 'testify'
                ],
                'frameworks': [
                    'gin', 'echo', 'fiber', 'beego', 'revel', 'gorm',
                    'cobra', 'viper', 'logrus', 'testify'
                ],
                'patterns': [
                    r'\b(golang?|goroutine)\b',
                    r'\b(\.go|go\.mod)\b',
                    r'\b(fmt\.|package\s+main)\b',
                    r'\b(gin|echo|fiber)\b'
                ],
                'file_extensions': ['.go'],
                'execution_command': 'go run'
            },
            'rust': {
                'keywords': [
                    'rust', 'cargo', 'rustc', 'crate', 'trait', 'impl',
                    'tokio', 'serde', 'clap', 'reqwest', 'actix'
                ],
                'frameworks': [
                    'tokio', 'serde', 'clap', 'reqwest', 'actix-web',
                    'rocket', 'diesel', 'sqlx', 'warp'
                ],
                'patterns': [
                    r'\b(rust|cargo|rustc)\b',
                    r'\b(\.rs|Cargo\.toml)\b',
                    r'\b(fn\s+main|use\s+std::)\b',
                    r'\b(tokio|serde|actix)\b'
                ],
                'file_extensions': ['.rs'],
                'execution_command': 'cargo run'
            },
            'python': {
                'keywords': [
                    'python', 'pip', 'conda', 'virtualenv', 'django', 'flask',
                    'fastapi', 'pandas', 'numpy', 'matplotlib', 'tensorflow',
                    'pytorch', 'scikit-learn', 'jupyter', 'notebook'
                ],
                'frameworks': [
                    'django', 'flask', 'fastapi', 'tornado', 'pyramid',
                    'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly',
                    'tensorflow', 'pytorch', 'scikit-learn', 'opencv'
                ],
                'patterns': [
                    r'\b(python|pip|conda)\b',
                    r'\b(\.py|\.ipynb|requirements\.txt)\b',
                    r'\b(import\s+|from\s+\w+\s+import)\b',
                    r'\b(django|flask|pandas)\b'
                ],
                'file_extensions': ['.py', '.ipynb'],
                'execution_command': 'python'
            }
        }
    
    def classify_language(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the programming language for a task."""
        
        # Extract text for analysis
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()
        deliverable = task.get('subtask_data', {}).get('deliverable', '').lower()
        
        combined_text = f"{title} {description} {deliverable}"
        
        # Skip language detection for non-code tasks
        if not self._is_programming_task(combined_text):
            return {
                'language': 'none',
                'confidence': 1.0,
                'is_programming_task': False,
                'reason': 'Not a programming task'
            }
        
        # Calculate confidence scores for each language
        language_scores = {}
        
        for language, patterns in self.language_patterns.items():
            score = self._calculate_language_score(combined_text, patterns)
            language_scores[language] = score
        
        # Determine primary language
        primary_language = max(language_scores, key=language_scores.get)
        primary_confidence = language_scores[primary_language]
        
        # Apply confidence threshold - default to Python if unclear
        if primary_confidence < 0.2:
            primary_language = 'python'
            primary_confidence = 0.6
            reason = 'Low confidence - defaulting to Python'
        else:
            reason = f'Detected based on keywords and patterns'
        
        return {
            'language': primary_language,
            'confidence': primary_confidence,
            'all_scores': language_scores,
            'is_programming_task': True,
            'reason': reason,
            'file_extension': self.language_patterns[primary_language]['file_extensions'][0],
            'execution_command': self.language_patterns[primary_language]['execution_command']
        }
    
    def _is_programming_task(self, text: str) -> bool:
        """Determine if this is a programming/development task."""
        
        programming_indicators = [
            'code', 'program', 'script', 'function', 'class', 'api',
            'application', 'software', 'system', 'algorithm', 'implement',
            'build', 'create', 'develop', 'framework', 'library',
            'database', 'server', 'client', 'web', 'app', 'gui'
        ]
        
        # Check for explicit non-programming indicators
        non_programming_indicators = [
            'write story', 'creative writing', 'poem', 'novel', 'essay',
            'research', 'analysis', 'report', 'document', 'summary'
        ]
        
        # If explicitly non-programming, return False
        if any(indicator in text for indicator in non_programming_indicators):
            return False
        
        # If has programming indicators, return True
        if any(indicator in text for indicator in programming_indicators):
            return True
        
        # Check for technology-specific terms
        for language_patterns in self.language_patterns.values():
            if any(keyword in text for keyword in language_patterns['keywords'][:5]):  # Check top keywords
                return True
        
        return False
    
    def _calculate_language_score(self, text: str, patterns: Dict[str, List]) -> float:
        """Calculate confidence score for a specific language."""
        
        total_score = 0.0
        total_weight = 0.0
        
        # Check keywords (weight: 1.0)
        keyword_matches = sum(1 for keyword in patterns.get('keywords', []) if keyword in text)
        if patterns.get('keywords'):
            total_score += (keyword_matches / len(patterns['keywords'])) * 1.0
            total_weight += 1.0
        
        # Check frameworks (weight: 0.8)
        if 'frameworks' in patterns:
            framework_matches = sum(1 for framework in patterns['frameworks'] if framework in text)
            if patterns['frameworks']:
                total_score += (framework_matches / len(patterns['frameworks'])) * 0.8
                total_weight += 0.8
        
        # Check regex patterns (weight: 0.6)
        if 'patterns' in patterns:
            pattern_matches = sum(1 for pattern in patterns['patterns'] 
                                if re.search(pattern, text, re.IGNORECASE))
            if patterns['patterns']:
                total_score += (pattern_matches / len(patterns['patterns'])) * 0.6
                total_weight += 0.6
        
        # Return normalized score
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def get_language_info(self, language: str) -> Dict[str, Any]:
        """Get information about a specific programming language."""
        
        if language not in self.language_patterns:
            return self.get_language_info('python')  # Default fallback
        
        patterns = self.language_patterns[language]
        
        language_info = {
            'javascript': {
                'name': 'JavaScript/Node.js',
                'description': 'Modern JavaScript for web and server development',
                'common_frameworks': ['Express.js', 'React', 'Vue.js'],
                'best_practices': ['Use modern ES6+ syntax', 'Proper error handling', 'Async/await patterns']
            },
            'java': {
                'name': 'Java',
                'description': 'Enterprise-grade object-oriented programming',
                'common_frameworks': ['Spring Boot', 'Hibernate', 'JUnit'],
                'best_practices': ['Follow naming conventions', 'Use design patterns', 'Proper exception handling']
            },
            'cpp': {
                'name': 'C++',
                'description': 'High-performance systems programming',
                'common_frameworks': ['Qt', 'Boost', 'OpenCV'],
                'best_practices': ['RAII pattern', 'Smart pointers', 'STL usage']
            },
            'csharp': {
                'name': 'C#',
                'description': '.NET ecosystem development',
                'common_frameworks': ['ASP.NET', 'Entity Framework', 'Blazor'],
                'best_practices': ['Follow C# conventions', 'Use LINQ', 'Async/await patterns']
            },
            'go': {
                'name': 'Go',
                'description': 'Simple, efficient systems programming',
                'common_frameworks': ['Gin', 'Echo', 'GORM'],
                'best_practices': ['Keep it simple', 'Use goroutines', 'Proper error handling']
            },
            'rust': {
                'name': 'Rust',
                'description': 'Memory-safe systems programming',
                'common_frameworks': ['Tokio', 'Serde', 'Actix-web'],
                'best_practices': ['Ownership model', 'Error handling with Result', 'Use of traits']
            },
            'python': {
                'name': 'Python',
                'description': 'Versatile, readable programming language',
                'common_frameworks': ['Django', 'Flask', 'FastAPI'],
                'best_practices': ['PEP 8 style', 'Type hints', 'List comprehensions']
            }
        }
        
        info = language_info.get(language, language_info['python'])
        info.update({
            'file_extensions': patterns['file_extensions'],
            'execution_command': patterns['execution_command']
        })
        
        return info