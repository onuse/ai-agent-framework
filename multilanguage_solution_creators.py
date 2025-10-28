from llm_client import LLMClient
from config import get_llm_config
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class MultiLanguageCodeSolutionCreator:
    """Code solution creator that adapts to different programming languages."""
    
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
        self.language_templates = {
            'javascript': {
                'expert_role': 'senior JavaScript/Node.js developer',
                'language_name': 'JavaScript/Node.js',
                'best_practices': [
                    'Use modern ES6+ syntax with const/let',
                    'Implement proper async/await patterns',
                    'Include comprehensive error handling with try/catch',
                    'Use meaningful variable and function names',
                    'Add JSDoc comments for functions',
                    'Handle edge cases and input validation'
                ],
                'common_patterns': [
                    'Use npm packages when appropriate',
                    'Implement RESTful API patterns for servers',
                    'Use Express.js for web applications',
                    'Prefer functional programming patterns',
                    'Use proper module imports/exports'
                ],
                'code_block': 'javascript'
            },
            'java': {
                'expert_role': 'senior Java developer',
                'language_name': 'Java',
                'best_practices': [
                    'Follow Java naming conventions (PascalCase for classes, camelCase for methods)',
                    'Use proper OOP principles and design patterns',
                    'Implement comprehensive exception handling',
                    'Include Javadoc comments for public methods',
                    'Use appropriate data structures from Collections framework',
                    'Follow SOLID principles'
                ],
                'common_patterns': [
                    'Use Spring Boot for web applications',
                    'Implement proper class hierarchies',
                    'Use interfaces for abstraction',
                    'Handle resources with try-with-resources',
                    'Use Stream API for data processing'
                ],
                'code_block': 'java'
            },
            'cpp': {
                'expert_role': 'senior C++ developer',
                'language_name': 'C++',
                'best_practices': [
                    'Use RAII (Resource Acquisition Is Initialization) pattern',
                    'Prefer smart pointers over raw pointers',
                    'Use const correctness throughout',
                    'Implement proper copy/move semantics',
                    'Use STL containers and algorithms',
                    'Include comprehensive error handling'
                ],
                'common_patterns': [
                    'Use standard library containers (vector, map, etc.)',
                    'Implement proper header guards or #pragma once',
                    'Use namespace std judiciously',
                    'Prefer stack allocation over heap when possible',
                    'Use template programming for generic code'
                ],
                'code_block': 'cpp'
            },
            'csharp': {
                'expert_role': 'senior C# developer',
                'language_name': 'C#',
                'best_practices': [
                    'Follow C# naming conventions (PascalCase for public members)',
                    'Use proper exception handling with try/catch/finally',
                    'Implement IDisposable pattern for resource management',
                    'Use LINQ for data querying and manipulation',
                    'Include XML documentation comments',
                    'Use async/await for asynchronous operations'
                ],
                'common_patterns': [
                    'Use ASP.NET Core for web applications',
                    'Implement dependency injection patterns',
                    'Use Entity Framework for data access',
                    'Prefer properties over public fields',
                    'Use using statements for resource management'
                ],
                'code_block': 'csharp'
            },
            'go': {
                'expert_role': 'senior Go developer',
                'language_name': 'Go',
                'best_practices': [
                    'Follow Go naming conventions (exported names start with capital)',
                    'Use explicit error handling with error return values',
                    'Keep functions and interfaces small and focused',
                    'Use goroutines and channels for concurrency',
                    'Include package-level documentation',
                    'Use gofmt for consistent formatting'
                ],
                'common_patterns': [
                    'Use Gin or Echo for web applications',
                    'Implement proper error handling patterns',
                    'Use struct composition over inheritance',
                    'Prefer interfaces for abstraction',
                    'Use defer for cleanup operations'
                ],
                'code_block': 'go'
            },
            'rust': {
                'expert_role': 'senior Rust developer',
                'language_name': 'Rust',
                'best_practices': [
                    'Embrace the ownership system and borrowing rules',
                    'Use Result<T, E> for error handling',
                    'Prefer pattern matching with match expressions',
                    'Use traits for shared behavior',
                    'Include comprehensive documentation with ///',
                    'Use clippy for code quality checks'
                ],
                'common_patterns': [
                    'Use Tokio for async programming',
                    'Implement proper error propagation with ?',
                    'Use iterators and functional programming patterns',
                    'Prefer enums for state representation',
                    'Use cargo for dependency management'
                ],
                'code_block': 'rust'
            },
            'python': {
                'expert_role': 'senior Python developer',
                'language_name': 'Python',
                'best_practices': [
                    'Follow PEP 8 style guidelines',
                    'Use type hints for better code documentation',
                    'Include comprehensive docstrings',
                    'Use list/dict comprehensions appropriately',
                    'Implement proper exception handling',
                    'Use context managers for resource management'
                ],
                'common_patterns': [
                    'Use Flask/Django/FastAPI for web applications',
                    'Prefer duck typing and EAFP (Easier to Ask Forgiveness than Permission)',
                    'Use virtual environments for dependency management',
                    'Use f-strings for string formatting',
                    'Leverage standard library modules'
                ],
                'code_block': 'python'
            }
        }
    
    def create_solution_prompt(self, task: Dict[str, Any], language: str, context: str = "") -> str:
        """Create a language-specific solution prompt."""
        
        task_data = task['subtask_data']
        template = self.language_templates.get(language, self.language_templates['python'])
        
        # Build best practices string
        best_practices = '\n'.join(f'- {practice}' for practice in template['best_practices'])
        common_patterns = '\n'.join(f'- {pattern}' for pattern in template['common_patterns'])
        
        prompt = f"""You are a {template['expert_role']} with expertise in production-quality code.

TASK: {task['title']}
DESCRIPTION: {task['description']}
DELIVERABLE: {task_data.get('deliverable', 'Working code')}
LANGUAGE: {template['language_name']}

{context}

Generate production-ready {template['language_name']} code that follows these best practices:
{best_practices}

Common patterns for {template['language_name']}:
{common_patterns}

Your code should:
1. Be immediately executable and fully functional
2. Include comprehensive error handling
3. Have clear, meaningful comments
4. Follow language-specific conventions and idioms
5. Be modular and maintainable
6. Handle edge cases appropriately
7. Include input validation where needed

Format your response as:
EXPLANATION:
[Brief explanation of your approach and key design decisions]

CODE:
```{template['code_block']}
[Your complete, production-ready {template['language_name']} code]
```

Focus on creating robust, idiomatic {template['language_name']} code that demonstrates expert-level understanding."""

        return prompt
    
    def generate_solution(self, task: Dict[str, Any], language: str, context: str = "") -> Dict[str, Any]:
        """Generate solution for the specified programming language."""
        
        prompt = self.create_solution_prompt(task, language, context)
        
        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            return self._extract_solution(content, language)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating {language} solution: {str(e)}'
            }
    
    def _extract_solution(self, content: str, language: str) -> Dict[str, Any]:
        """Extract solution from LLM response."""
        
        explanation = ""
        solution = ""
        
        if "EXPLANATION:" in content:
            parts = content.split("EXPLANATION:", 1)
            if len(parts) > 1:
                remaining = parts[1]
                if "CODE:" in remaining:
                    exp_code = remaining.split("CODE:", 1)
                    explanation = exp_code[0].strip()
                    code_section = exp_code[1].strip()
                else:
                    explanation = remaining.strip()
                    code_section = ""
            else:
                code_section = content
        else:
            code_section = content
        
        # Extract code from markdown blocks - try language-specific first
        template = self.language_templates.get(language, self.language_templates['python'])
        code_block_name = template['code_block']
        
        patterns_to_try = [
            f"```{code_block_name}",
            f"```{language}",
            "```"
        ]
        
        for pattern in patterns_to_try:
            if pattern in code_section:
                code_start = code_section.find(pattern) + len(pattern)
                code_end = code_section.find("```", code_start)
                if code_end != -1:
                    solution = code_section[code_start:code_end].strip()
                    break
                else:
                    solution = code_section[code_start:].strip()
                    break
        
        if not solution:
            solution = code_section.strip()
        
        if not solution:
            return {
                'success': False,
                'error': f'No {language} code generated by LLM'
            }
        
        return {
            'success': True,
            'solution': solution,
            'explanation': explanation,
            'language': language
        }

class MultiLanguageExecutor:
    """Executor that can run code in different programming languages."""
    
    def __init__(self):
        self.execution_configs = {
            'javascript': {
                'compile_command': None,
                'run_command': ['node'],
                'file_extension': '.js',
                'temp_filename': 'temp_script.js'
            },
            'java': {
                'compile_command': ['javac'],
                'run_command': ['java'],
                'file_extension': '.java',
                'temp_filename': 'TempClass.java',
                'needs_compilation': True
            },
            'cpp': {
                'compile_command': ['g++', '-o'],
                'run_command': [],  # Will be set dynamically
                'file_extension': '.cpp',
                'temp_filename': 'temp_program.cpp',
                'needs_compilation': True
            },
            'csharp': {
                'compile_command': None,
                'run_command': ['dotnet', 'run'],
                'file_extension': '.cs',
                'temp_filename': 'Program.cs',
                'needs_project': True
            },
            'go': {
                'compile_command': None,
                'run_command': ['go', 'run'],
                'file_extension': '.go',
                'temp_filename': 'main.go'
            },
            'rust': {
                'compile_command': None,
                'run_command': ['cargo', 'run'],
                'file_extension': '.rs',
                'temp_filename': 'main.rs',
                'needs_project': True
            },
            'python': {
                'compile_command': None,
                'run_command': ['python'],
                'file_extension': '.py',
                'temp_filename': 'temp_script.py'
            }
        }
    
    def can_execute(self, language: str) -> bool:
        """Check if the language can be executed on this system."""
        
        config = self.execution_configs.get(language)
        if not config:
            return False
        
        # For now, assume all languages can be executed
        # In production, this would check for installed compilers/runtimes
        return True
    
    def get_execution_approach(self, language: str) -> str:
        """Get the execution approach for a language."""
        
        config = self.execution_configs.get(language)
        if not config:
            return 'unsupported'
        
        if config.get('needs_compilation'):
            return 'compile_and_run'
        elif config.get('needs_project'):
            return 'project_based'
        else:
            return 'direct_execution'
    
    def get_file_extension(self, language: str) -> str:
        """Get the appropriate file extension for a language."""
        
        config = self.execution_configs.get(language, self.execution_configs['python'])
        return config['file_extension']