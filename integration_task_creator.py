"""
Integration Task Creator for AI Agent Framework
Adds integration validation and glue code generation to ensure multi-file projects work together
"""

class IntegrationTaskCreator:
    """Creates integration tasks for multi-component projects."""
    
    def __init__(self):
        self.integration_patterns = {
            'javascript_game': {
                'file_patterns': ['.js', '.html'],
                'required_components': ['canvas', 'game loop', 'initialization'],
                'integration_type': 'web_game'
            },
            'python_gui': {
                'file_patterns': ['.py'],
                'required_components': ['tkinter', 'main window', 'event handlers'],
                'integration_type': 'desktop_app'
            },
            'web_app': {
                'file_patterns': ['.js', '.html', '.css'],
                'required_components': ['html structure', 'javascript', 'styling'],
                'integration_type': 'web_application'
            }
        }
    
    def should_create_integration_task(self, objective: str, completed_tasks: list) -> bool:
        """Determine if an integration task is needed."""
        
        # Check if this is a multi-component project
        is_multi_component = len(completed_tasks) >= 2
        
        # Check if it's a type that needs integration
        needs_integration = any([
            'game' in objective.lower() and 'javascript' in objective.lower(),
            'web' in objective.lower() and len(completed_tasks) >= 2,
            'gui' in objective.lower() and len(completed_tasks) >= 2,
            'app' in objective.lower() and len(completed_tasks) >= 2
        ])
        
        return is_multi_component and needs_integration
    
    def create_integration_task(self, objective: str, completed_tasks: list, project_id: str) -> dict:
        """Create an integration task definition."""
        
        # Determine integration type
        integration_type = self._classify_integration_type(objective)
        
        if integration_type == 'javascript_game':
            return {
                'title': 'Integrate Game Components and Create Main Game Loop',
                'description': f'''Analyze all generated JavaScript files and create integration code that:
1. Connects the raycasting engine, player movement, and map components
2. Creates a main game loop that renders frames continuously
3. Ensures the game displays properly in the HTML canvas
4. Adds proper initialization code that starts the game automatically
5. Handles integration between all components to create a working game

The integration should examine existing files: {[task.get('title', 'Unknown') for task in completed_tasks]}
and create the necessary glue code to make them work together as a cohesive game.''',
                'deliverable': 'Working integrated game that displays and runs in browser with all components functioning together',
                'integration_type': 'javascript_game',
                'project_id': project_id,
                'requires_analysis': True
            }
        
        elif integration_type == 'web_app':
            return {
                'title': 'Integrate Web Application Components',
                'description': f'''Create integration code that connects all web components:
1. Ensure HTML properly loads all JavaScript and CSS files
2. Create proper initialization sequence for web application
3. Add error handling and user feedback
4. Verify all components work together seamlessly

Analyze existing components: {[task.get('title', 'Unknown') for task in completed_tasks]}''',
                'deliverable': 'Fully functional web application with integrated components',
                'integration_type': 'web_app',
                'project_id': project_id,
                'requires_analysis': True
            }
        
        elif integration_type == 'python_gui':
            return {
                'title': 'Integrate GUI Application Components',
                'description': f'''Create main application file that integrates all GUI components:
1. Import and initialize all created modules
2. Create main window that combines all functionality
3. Ensure proper event handling between components
4. Add error handling and user feedback

Integrate components: {[task.get('title', 'Unknown') for task in completed_tasks]}''',
                'deliverable': 'Working GUI application with all components integrated',
                'integration_type': 'python_gui',
                'project_id': project_id,
                'requires_analysis': True
            }
        
        else:
            return {
                'title': 'Integrate and Test All Components',
                'description': f'''Analyze all generated components and create integration code:
1. Examine all created files for functions, classes, and entry points
2. Create main integration file that connects all components
3. Add initialization code that starts the application
4. Ensure all parts work together as intended

Components to integrate: {[task.get('title', 'Unknown') for task in completed_tasks]}''',
                'deliverable': 'Working integrated application with all components functioning together',
                'integration_type': 'generic',
                'project_id': project_id,
                'requires_analysis': True
            }
    
    def _classify_integration_type(self, objective: str) -> str:
        """Classify what type of integration is needed."""
        
        objective_lower = objective.lower()
        
        if 'javascript' in objective_lower and ('game' in objective_lower or 'doom' in objective_lower):
            return 'javascript_game'
        elif 'web' in objective_lower or 'html' in objective_lower:
            return 'web_app'
        elif 'gui' in objective_lower or 'tkinter' in objective_lower:
            return 'python_gui'
        else:
            return 'generic'


def add_integration_to_manager_agent():
    """
    Instructions for modifying manager_agent.py to include integration tasks.
    
    Add this to the end of _generate_focused_task_breakdown method:
    """
    integration_code = '''
    # Add integration task for multi-component projects
    from integration_task_creator import IntegrationTaskCreator
    
    integration_creator = IntegrationTaskCreator()
    
    # Check if we need integration (after creating main tasks)
    if len(task_data['subtasks']) >= 2:
        if integration_creator.should_create_integration_task(objective, task_data['subtasks']):
            integration_task = integration_creator.create_integration_task(
                objective, 
                task_data['subtasks'], 
                project_id
            )
            
            # Add integration task with highest priority (runs last)
            self.task_queue.add_task(
                title=integration_task['title'],
                description=integration_task['description'],
                subtask_data={
                    'deliverable': integration_task['deliverable'],
                    'project_id': project_id,
                    'domain': 'integration',
                    'integration_type': integration_task['integration_type'],
                    'requires_analysis': True,
                    'objective': objective
                },
                priority=0  # Lowest priority = runs last
            )
            
            print(f"Added integration task for {integration_task['integration_type']} project")
    '''
    
    return integration_code


def create_integration_solution_creator():
    """Create specialized solution creator for integration tasks."""
    
    integration_solution_code = '''
class IntegrationSolutionCreator(BaseSolutionCreator):
    """Specialized solution creator for integration tasks."""
    
    def create_solution_prompt(self, task: Dict[str, Any], context: str = "") -> str:
        task_data = task['subtask_data']
        integration_type = task_data.get('integration_type', 'generic')
        
        if integration_type == 'javascript_game':
            return self._create_js_game_integration_prompt(task, context)
        elif integration_type == 'web_app':
            return self._create_web_app_integration_prompt(task, context)
        elif integration_type == 'python_gui':
            return self._create_python_gui_integration_prompt(task, context)
        else:
            return self._create_generic_integration_prompt(task, context)
    
    def _create_js_game_integration_prompt(self, task: Dict[str, Any], context: str) -> str:
        return f"""You are a senior game developer creating integration code for a JavaScript game.

TASK: {task['title']}
DESCRIPTION: {task['description']}

{context}

CRITICAL REQUIREMENTS:
1. Analyze the existing JavaScript files in the project folder
2. Create a main.js file that integrates all components
3. Ensure the game renders something visible on the canvas immediately
4. Create a proper game loop with requestAnimationFrame
5. Initialize all components in the correct order

Your integration code must:
- Import/use functions from the raycasting engine
- Connect player movement to the raycasting system
- Render the map and player view simultaneously
- Handle user input (WASD/arrow keys)
- Display something visible on screen immediately when loaded

Generate JavaScript code that creates a working, integrated game:

```javascript
// Main game integration file
// This file connects all components and starts the game

class Game {{
    constructor(canvas) {{
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.running = false;
        
        // Initialize all components
        this.initializeComponents();
        
        // Start the game
        this.start();
    }}
    
    initializeComponents() {{
        // Initialize raycasting engine, player, map, etc.
        // Use the existing component files
    }}
    
    start() {{
        this.running = true;
        this.gameLoop();
    }}
    
    gameLoop() {{
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update game state
        this.update();
        
        // Render everything
        this.render();
        
        // Continue loop
        if (this.running) {{
            requestAnimationFrame(() => this.gameLoop());
        }}
    }}
    
    update() {{
        // Update player, handle input, etc.
    }}
    
    render() {{
        // Render raycasted view, map, UI, etc.
        // Make sure SOMETHING is visible
    }}
}}

// Auto-start when DOM is ready
document.addEventListener('DOMContentLoaded', function() {{
    const canvas = document.getElementById('gameCanvas');
    if (canvas) {{
        window.game = new Game(canvas);
    }}
}});
```

The code must create a visually working game that displays immediately when the HTML loads."""
        
    def get_execution_type(self) -> str:
        return "integration_execution"
    '''
    
    return integration_solution_code


# Example usage for your framework
def modify_manager_agent_file():
    """
    Instructions to modify your manager_agent.py:
    
    1. Add this import at the top:
       from integration_task_creator import IntegrationTaskCreator
    
    2. Add this code at the end of _generate_focused_task_breakdown method:
    """
    
    modification_instructions = '''
    # At the end of _generate_focused_task_breakdown method, add:
    
    # Check if we need an integration task
    integration_creator = IntegrationTaskCreator()
    
    if len(task_data['subtasks']) >= 2:
        if integration_creator.should_create_integration_task(objective, task_data['subtasks']):
            integration_task = integration_creator.create_integration_task(
                objective, 
                task_data['subtasks'], 
                project_id
            )
            
            # Add integration task with lowest priority (runs last)
            self.task_queue.add_task(
                title=integration_task['title'],
                description=integration_task['description'],
                subtask_data={
                    'deliverable': integration_task['deliverable'],
                    'project_id': project_id,
                    'domain': 'integration',
                    'integration_type': integration_task['integration_type'],
                    'requires_analysis': True,
                    'objective': objective
                },
                priority=0  # Runs last
            )
            
            print(f"Added integration task for {integration_task['integration_type']} project")
    '''
    
    return modification_instructions


if __name__ == "__main__":
    # Test the integration task creator
    creator = IntegrationTaskCreator()
    
    # Example usage
    objective = "Create a JavaScript doom clone with raycasting engine, player movement, and a basic visible map"
    completed_tasks = [
        {'title': 'Implement Ray Casting Engine'},
        {'title': 'Implement Basic Player Movement'},
        {'title': 'Create Basic Visible Map'}
    ]
    
    if creator.should_create_integration_task(objective, completed_tasks):
        integration_task = creator.create_integration_task(objective, completed_tasks, "test_project")
        print("Integration Task Created:")
        print(f"Title: {integration_task['title']}")
        print(f"Description: {integration_task['description'][:200]}...")
        print(f"Type: {integration_task['integration_type']}")