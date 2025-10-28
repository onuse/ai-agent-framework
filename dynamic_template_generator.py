from llm_client import LLMClient
from config import get_llm_config
import json
from typing import Dict, Any, List, Optional

class DynamicTemplateGenerator:
    """LLM-powered template generator that creates appropriate project structure and content."""
    
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
    
    def generate_html_template(self, objective: str, js_files: List[str], project_analysis: Dict[str, Any] = None) -> str:
        """Generate HTML template based on project objective and content analysis."""
        
        # Analyze the JavaScript files if available
        code_analysis = self._analyze_javascript_files(js_files) if js_files else {}
        
        prompt = f"""You are a web developer creating an HTML entry point for a JavaScript project.

PROJECT OBJECTIVE: {objective}
JAVASCRIPT FILES: {', '.join(js_files) if js_files else 'None yet'}

CODE ANALYSIS:
{json.dumps(code_analysis, indent=2) if code_analysis else 'No code analysis available'}

Generate a complete HTML file that:
1. Provides appropriate UI elements for THIS SPECIFIC project
2. Includes relevant instructions for the user
3. Has proper styling that matches the project type
4. Contains the right canvas/container elements
5. Shows appropriate controls/instructions for this specific application

Return your response as a JSON object with these fields:
{{
    "html_content": "complete HTML file content",
    "page_title": "appropriate page title",
    "ui_elements": ["list of UI elements included"],
    "instructions": ["list of user instructions"],
    "styling_approach": "description of styling choices"
}}

IMPORTANT: 
- For games: Include game-specific controls (chess = click pieces, puzzle = drag/click, etc.)
- For tools: Include relevant input fields and buttons
- For demos: Include explanation and demonstration controls
- Make it visually appealing and functional for the specific use case"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            return self._parse_template_response(content, objective, js_files)
            
        except Exception as e:
            print(f"[TEMPLATE] LLM generation failed: {e}")
            return self._fallback_html_template(objective, js_files)
    
    def generate_python_main(self, objective: str, py_files: List[str], project_analysis: Dict[str, Any] = None) -> str:
        """Generate Python main.py based on project content."""
        
        # Analyze Python files
        code_analysis = self._analyze_python_files(py_files) if py_files else {}
        
        prompt = f"""You are a Python developer creating a main.py entry point.

PROJECT OBJECTIVE: {objective}
PYTHON FILES: {', '.join(py_files) if py_files else 'None yet'}

CODE ANALYSIS:
{json.dumps(code_analysis, indent=2) if code_analysis else 'No code analysis available'}

Generate a main.py file that:
1. Imports and initializes the appropriate modules
2. Provides a clear entry point for the application
3. Includes proper command-line interface if needed
4. Has error handling and user guidance
5. Demonstrates how to use the created components

Return your response as a JSON object:
{{
    "python_content": "complete main.py content",
    "imports_needed": ["list of imports"],
    "entry_functions": ["list of main functions to call"],
    "cli_options": ["list of command line options if any"],
    "usage_instructions": "how to run the application"
}}

Make it specific to this project type and the actual modules created."""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            return self._parse_python_response(content, objective, py_files)
            
        except Exception as e:
            print(f"[TEMPLATE] Python generation failed: {e}")
            return self._fallback_python_main(objective, py_files)
    
    def generate_readme(self, objective: str, files: List[str], project_type: str) -> str:
        """Generate project-specific README.md."""
        
        prompt = f"""Create a comprehensive README.md for this project.

PROJECT OBJECTIVE: {objective}
PROJECT TYPE: {project_type}
FILES CREATED: {', '.join(files)}

Create a README that includes:
1. Clear project title and description
2. What the project does and its features
3. How to run/use the application
4. File structure explanation
5. Any special requirements or setup
6. Usage examples if applicable

Make it specific to this project, not generic. Focus on what this particular application does and how someone would use it.

Return just the markdown content, no JSON wrapper."""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response['message']['content']
            
        except Exception as e:
            print(f"[TEMPLATE] README generation failed: {e}")
            return self._fallback_readme(objective, files, project_type)
    
    def _analyze_javascript_files(self, js_files: List[str]) -> Dict[str, Any]:
        """Analyze JavaScript files to understand project structure."""
        
        analysis = {
            "detected_patterns": [],
            "ui_elements_found": [],
            "game_mechanics": [],
            "frameworks_used": []
        }
        
        # This would analyze actual file contents
        # For now, infer from filenames
        for filename in js_files:
            filename_lower = filename.lower()
            
            if 'chess' in filename_lower:
                analysis["game_mechanics"].extend(["turn-based", "board-game", "piece-movement"])
                analysis["ui_elements_found"].extend(["game-board", "piece-selection"])
            elif 'doom' in filename_lower or 'raycasting' in filename_lower:
                analysis["game_mechanics"].extend(["first-person", "real-time", "3d-rendering"])
                analysis["ui_elements_found"].extend(["canvas", "crosshair", "movement-controls"])
            elif 'puzzle' in filename_lower:
                analysis["game_mechanics"].extend(["puzzle-solving", "drag-drop", "logic-based"])
            elif 'calculator' in filename_lower:
                analysis["ui_elements_found"].extend(["buttons", "display", "input-fields"])
        
        return analysis
    
    def _analyze_python_files(self, py_files: List[str]) -> Dict[str, Any]:
        """Analyze Python files to understand project structure."""
        
        analysis = {
            "modules_found": [],
            "main_classes": [],
            "frameworks_detected": [],
            "entry_points": []
        }
        
        for filename in py_files:
            module_name = filename.replace('.py', '')
            analysis["modules_found"].append(module_name)
            
            # Infer likely class names
            class_name = ''.join(word.capitalize() for word in module_name.split('_'))
            analysis["main_classes"].append(class_name)
            
            if 'tkinter' in filename.lower() or 'gui' in filename.lower():
                analysis["frameworks_detected"].append("tkinter")
            elif 'flask' in filename.lower():
                analysis["frameworks_detected"].append("flask")
            elif 'game' in filename.lower():
                analysis["frameworks_detected"].append("pygame")
        
        return analysis
    
    def _parse_template_response(self, content: str, objective: str, js_files: List[str]) -> str:
        """Parse LLM response and extract HTML content."""
        
        try:
            # Find JSON in response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                result = json.loads(json_content)
                return result.get('html_content', content)
            
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, try to extract HTML content directly
        if '<!DOCTYPE html>' in content:
            return content
        
        # Fallback
        return self._fallback_html_template(objective, js_files)
    
    def _parse_python_response(self, content: str, objective: str, py_files: List[str]) -> str:
        """Parse LLM response and extract Python content."""
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                result = json.loads(json_content)
                return result.get('python_content', content)
            
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, look for Python code
        if 'def main(' in content or 'if __name__' in content:
            return content
        
        return self._fallback_python_main(objective, py_files)
    
    def _fallback_html_template(self, objective: str, js_files: List[str]) -> str:
        """Simple fallback HTML template."""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{objective}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background-color: #1a1a1a;
            color: #ffffff;
            text-align: center;
        }}
        
        #app-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div id="app-container">
        <h1>{objective}</h1>
        <div id="main-content">
            <!-- Application will initialize here -->
        </div>
        <div id="status">Loading...</div>
    </div>
    
    {chr(10).join(f'    <script src="{js_file}"></script>' for js_file in js_files)}
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            document.getElementById('status').textContent = 'Application loaded!';
        }});
    </script>
</body>
</html>"""
    
    def _fallback_python_main(self, objective: str, py_files: List[str]) -> str:
        """Simple fallback Python main."""
        
        imports = []
        for py_file in py_files:
            if py_file != 'main.py':
                module = py_file.replace('.py', '')
                imports.append(f"# import {module}")
        
        return f'''#!/usr/bin/env python3
"""
{objective}
Generated by AI Agent Framework
"""

import sys
import os

# Project imports
{chr(10).join(imports)}

def main():
    """Main application entry point."""
    print("Starting: {objective}")
    
    # TODO: Initialize and run the application
    print("Application ready!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    
    def _fallback_readme(self, objective: str, files: List[str], project_type: str) -> str:
        """Simple fallback README."""
        
        return f"""# {objective}

A {project_type} project generated by AI Agent Framework.

## Files
{chr(10).join(f'- {file}' for file in files)}

## Usage
See individual files for specific instructions.

---
*Generated automatically by AI Agent Framework*
"""