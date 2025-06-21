import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from task_queue import TaskQueue

class ProjectManager:
    """Manages project persistence and iterative development."""
    
    def __init__(self, artifacts_dir: str = "artifacts"):
        self.artifacts_dir = artifacts_dir
        self.projects_dir = os.path.join(artifacts_dir, ".projects")
        self.task_queue = TaskQueue()
        
        # Create projects metadata directory
        os.makedirs(self.projects_dir, exist_ok=True)
    
    def get_or_create_project(self, project_name: str, objective: str) -> Dict[str, Any]:
        """Get existing project or create new one."""
        
        # Sanitize project name
        safe_project_name = self._sanitize_project_name(project_name)
        project_metadata_file = os.path.join(self.projects_dir, f"{safe_project_name}.json")
        project_dir = os.path.join(self.artifacts_dir, safe_project_name)
        
        # Check if project exists
        if os.path.exists(project_metadata_file):
            return self._load_existing_project(safe_project_name, objective)
        else:
            return self._create_new_project(safe_project_name, objective)
    
    def _load_existing_project(self, project_name: str, new_objective: str) -> Dict[str, Any]:
        """Load existing project and prepare for continuation."""
        
        project_metadata_file = os.path.join(self.projects_dir, f"{project_name}.json")
        
        with open(project_metadata_file, 'r') as f:
            metadata = json.load(f)
        
        project_id = metadata['project_id']
        original_objective = metadata['original_objective']
        
        print(f"📁 Loading existing project: {project_name}")
        print(f"🎯 Original objective: {original_objective}")
        print(f"🔄 New objective: {new_objective}")
        
        # Check if this is a refinement or major change
        is_refinement = self._is_refinement(original_objective, new_objective)
        
        if is_refinement:
            print(f"✨ Detected refinement - extending existing project")
            return self._extend_project(metadata, new_objective)
        else:
            print(f"🔀 Detected major change - creating new iteration")
            return self._create_project_iteration(metadata, new_objective)
    
    def _create_new_project(self, project_name: str, objective: str) -> Dict[str, Any]:
        """Create a brand new project."""
        
        print(f"🆕 Creating new project: {project_name}")
        
        # Create project in task queue
        project_id = self.task_queue.create_project(project_name, objective)
        
        # Create project metadata
        metadata = {
            'project_id': project_id,
            'project_name': project_name,
            'original_objective': objective,
            'created_at': datetime.now().isoformat(),
            'iterations': [
                {
                    'iteration': 1,
                    'objective': objective,
                    'created_at': datetime.now().isoformat(),
                    'project_id': project_id
                }
            ],
            'current_iteration': 1,
            'total_tasks_completed': 0
        }
        
        # Save metadata
        self._save_project_metadata(project_name, metadata)
        
        return {
            'project_id': project_id,
            'project_name': project_name,
            'is_new': True,
            'is_continuation': False,
            'metadata': metadata
        }
    
    def _extend_project(self, metadata: Dict[str, Any], new_objective: str) -> Dict[str, Any]:
        """Extend existing project with new features."""
        
        project_id = metadata['project_id']
        project_name = metadata['project_name']
        
        # Update project in task queue with extended objective
        combined_objective = f"{metadata['original_objective']} + {new_objective}"
        self.task_queue.update_project_phase(project_id, "extending", {'extension_objective': new_objective})
        
        # Add to iterations
        current_iteration = metadata['current_iteration']
        metadata['iterations'].append({
            'iteration': current_iteration + 1,
            'objective': new_objective,
            'created_at': datetime.now().isoformat(),
            'type': 'extension',
            'base_project_id': project_id
        })
        metadata['current_iteration'] = current_iteration + 1
        metadata['last_updated'] = datetime.now().isoformat()
        
        # Save updated metadata
        self._save_project_metadata(project_name, metadata)
        
        return {
            'project_id': project_id,
            'project_name': project_name,
            'is_new': False,
            'is_continuation': True,
            'extension_objective': new_objective,
            'metadata': metadata
        }
    
    def _create_project_iteration(self, metadata: Dict[str, Any], new_objective: str) -> Dict[str, Any]:
        """Create a new iteration of the project with major changes."""
        
        original_project_id = metadata['project_id']
        project_name = metadata['project_name']
        
        # Create new project ID for this iteration
        new_project_id = self.task_queue.create_project(f"{project_name}_v{metadata['current_iteration'] + 1}", new_objective)
        
        # Add to iterations
        current_iteration = metadata['current_iteration']
        metadata['iterations'].append({
            'iteration': current_iteration + 1,
            'objective': new_objective,
            'created_at': datetime.now().isoformat(),
            'type': 'major_iteration',
            'project_id': new_project_id,
            'previous_project_id': original_project_id
        })
        metadata['current_iteration'] = current_iteration + 1
        metadata['last_updated'] = datetime.now().isoformat()
        
        # Save updated metadata
        self._save_project_metadata(project_name, metadata)
        
        return {
            'project_id': new_project_id,
            'project_name': project_name,
            'is_new': False,
            'is_continuation': True,
            'is_major_iteration': True,
            'previous_project_id': original_project_id,
            'metadata': metadata
        }
    
    def _is_refinement(self, original: str, new: str) -> bool:
        """Determine if new objective is a refinement/extension vs major change."""
        
        # Simple heuristics for refinement detection
        refinement_keywords = [
            'add', 'improve', 'enhance', 'extend', 'implement', 'include',
            'create', 'build', 'make', 'integrate', 'optimize', 'refactor'
        ]
        
        major_change_keywords = [
            'rewrite', 'recreate', 'rebuild', 'redesign', 'replace', 'change to',
            'convert to', 'port to', 'migrate to'
        ]
        
        new_lower = new.lower()
        
        # Check for major change indicators
        if any(keyword in new_lower for keyword in major_change_keywords):
            return False
        
        # Check for refinement indicators
        if any(keyword in new_lower for keyword in refinement_keywords):
            return True
        
        # Default: treat as refinement if in doubt
        return True
    
    def _sanitize_project_name(self, name: str) -> str:
        """Create a safe project name for filesystem."""
        
        # Remove invalid characters and convert to lowercase
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_').lower()
        
        # Ensure name is not empty
        if not safe_name:
            safe_name = f"project_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        
        return safe_name
    
    def _save_project_metadata(self, project_name: str, metadata: Dict[str, Any]):
        """Save project metadata to disk."""
        
        project_metadata_file = os.path.join(self.projects_dir, f"{project_name}.json")
        
        with open(project_metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all existing projects."""
        
        projects = []
        
        if not os.path.exists(self.projects_dir):
            return projects
        
        for filename in os.listdir(self.projects_dir):
            if filename.endswith('.json'):
                project_name = filename[:-5]  # Remove .json
                metadata_file = os.path.join(self.projects_dir, filename)
                
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    projects.append({
                        'name': project_name,
                        'original_objective': metadata.get('original_objective', 'Unknown'),
                        'current_iteration': metadata.get('current_iteration', 1),
                        'total_iterations': len(metadata.get('iterations', [])),
                        'created_at': metadata.get('created_at', 'Unknown'),
                        'last_updated': metadata.get('last_updated', metadata.get('created_at', 'Unknown'))
                    })
                except Exception as e:
                    print(f"Warning: Could not load project metadata for {project_name}: {e}")
        
        return sorted(projects, key=lambda x: x['last_updated'], reverse=True)
    
    def get_project_context(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive context for an existing project."""
        
        safe_project_name = self._sanitize_project_name(project_name)
        project_metadata_file = os.path.join(self.projects_dir, f"{safe_project_name}.json")
        
        if not os.path.exists(project_metadata_file):
            return None
        
        with open(project_metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Get project directory contents
        project_dir = os.path.join(self.artifacts_dir, safe_project_name)
        artifacts = []
        
        if os.path.exists(project_dir):
            for item in os.listdir(project_dir):
                item_path = os.path.join(project_dir, item)
                if os.path.isfile(item_path):
                    artifacts.append({
                        'name': item,
                        'size': os.path.getsize(item_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
                    })
        
        # Get task completion stats
        project_id = metadata['project_id']
        task_counts = self.task_queue.get_task_count_by_status()
        
        return {
            'metadata': metadata,
            'artifacts': artifacts,
            'task_counts': task_counts,
            'project_directory': project_dir
        }
    
    def get_continuation_prompt(self, project_context: Dict[str, Any], new_objective: str) -> str:
        """Generate context prompt for continuing an existing project."""
        
        metadata = project_context['metadata']
        artifacts = project_context['artifacts']
        
        context_prompt = f"""
CONTINUING EXISTING PROJECT: {metadata['project_name']}

ORIGINAL OBJECTIVE: {metadata['original_objective']}
NEW EXTENSION: {new_objective}

PROJECT HISTORY:
"""
        
        for iteration in metadata['iterations']:
            context_prompt += f"- Iteration {iteration['iteration']}: {iteration['objective']}\n"
        
        context_prompt += f"""
EXISTING ARTIFACTS ({len(artifacts)} files):
"""
        
        for artifact in artifacts[:10]:  # Show up to 10 files
            context_prompt += f"- {artifact['name']} ({artifact['size']} bytes)\n"
        
        if len(artifacts) > 10:
            context_prompt += f"- ... and {len(artifacts) - 10} more files\n"
        
        context_prompt += f"""
TASK: Build upon the existing project to implement: {new_objective}

IMPORTANT: 
- This is an EXTENSION of existing work, not a complete rewrite
- Analyze existing code structure and build upon it
- Maintain compatibility with existing functionality
- Focus on incremental improvements and additions
- Reuse existing components where possible
"""
        
        return context_prompt