import os
import json
from llm_client import LLMClient
from config import get_llm_config
from typing import Dict, Any, List, Optional
from datetime import datetime
from task_queue import TaskQueue
from project_folder_manager import ProjectFolderManager

class ProjectCompletenessAgent:
    """Agent that performs final validation and completeness checks on generated projects."""
    
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
        self.task_queue = TaskQueue()
        self.project_manager = ProjectFolderManager()
    
    def perform_final_validation(self, project_id: str, objective: str) -> Dict[str, Any]:
        """Perform comprehensive final validation of the project."""
        
        print("\n" + "="*60)
        print("🔍 FINAL PROJECT VALIDATION")
        print("="*60)
        
        validation_report = {
            'project_id': project_id,
            'objective': objective,
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'PENDING',
            'score': 0,
            'checks': {},
            'artifacts': [],
            'recommendations': [],
            'issues': [],
            'user_satisfaction': {}
        }
        
        # 1. Check task completion status
        task_check = self._check_task_completion(project_id)
        validation_report['checks']['task_completion'] = task_check
        
        # 2. Verify artifacts exist
        artifacts_check = self._check_artifacts_exist(project_id, objective)
        validation_report['checks']['artifacts_existence'] = artifacts_check
        validation_report['artifacts'] = artifacts_check.get('found_artifacts', [])
        
        # 3. Validate file structure
        structure_check = self._check_project_structure(project_id, objective)
        validation_report['checks']['project_structure'] = structure_check
        
        # 4. Check feature completeness
        features_check = self._check_feature_completeness(objective, artifacts_check)
        validation_report['checks']['feature_completeness'] = features_check
        
        # 5. Validate technical integrity
        technical_check = self._check_technical_integrity(artifacts_check)
        validation_report['checks']['technical_integrity'] = technical_check
        
        # 6. NEW: User Perspective Validation - The Reality Check
        user_perspective = self._perform_user_perspective_validation(objective, validation_report)
        validation_report['checks']['user_perspective'] = user_perspective
        validation_report['user_satisfaction'] = user_perspective
        
        # 7. Generate overall assessment (now includes user perspective)
        overall_assessment = self._generate_overall_assessment(validation_report)
        validation_report.update(overall_assessment)
        
        # 8. Print comprehensive report
        self._print_validation_report(validation_report)
        
        return validation_report
    
    def _perform_user_perspective_validation(self, objective: str, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """NEW: Ask LLM to evaluate from the user's perspective - the reality check."""
        
        print("👤 Performing user perspective validation...")
        
        artifacts = validation_report.get('artifacts', [])
        
        # Build context about what was generated
        file_list = []
        file_contents_summary = []
        
        for artifact in artifacts:
            file_list.append(f"- {artifact['name']} ({artifact['size']} bytes, {artifact['type']})")
            
            # Get a sample of the file content for context
            try:
                with open(artifact['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Take first 300 chars as sample
                    sample = content[:300] + "..." if len(content) > 300 else content
                    file_contents_summary.append(f"**{artifact['name']}:**\n```\n{sample}\n```")
            except:
                file_contents_summary.append(f"**{artifact['name']}:** (Could not read)")
        
        files_context = "\n".join(file_list)
        contents_preview = "\n\n".join(file_contents_summary[:3])  # Show max 3 file previews
        
        # Create the user perspective prompt
        prompt = f"""You are evaluating a project from the perspective of someone who made a request and is now checking if their needs were met.

ORIGINAL REQUEST: "{objective}"

GENERATED PROJECT FILES:
{files_context}

SAMPLE FILE CONTENTS:
{contents_preview}

Now put yourself in the shoes of the person who requested: "{objective}"

They open the project folder expecting a working solution. Evaluate honestly:

1. **USABILITY**: Is there a clear way to run/start this? (index.html to open, main.py to run, etc.)
2. **COMPLETENESS**: Does it actually DO what was requested? Is it a working solution or just code pieces?
3. **MISSING PIECES**: Are there obvious gaps that would confuse or frustrate the user?
4. **FIRST IMPRESSION**: When they try to use it, will it work immediately or require additional setup?
5. **SATISFACTION**: Would they feel their request was fulfilled or would they think "this isn't what I asked for"?

Be brutally honest. Consider:
- If they asked for a "game", can they actually play it?
- If they asked for an "app", can they actually use it?
- If they asked for a "calculator", can they actually calculate with it?
- Are files connected properly or just isolated pieces?

Respond in JSON format:
{{
    "user_would_be_satisfied": true/false,
    "satisfaction_score": 1-10,
    "clear_entry_point": true/false,
    "actually_works": true/false,
    "major_gaps": ["list", "of", "missing", "pieces"],
    "first_impression": "What happens when they first try to use it",
    "the_one_biggest_problem": "The single most important issue",
    "quick_fix_suggestion": "One specific action to make this much better",
    "honest_assessment": "Blunt truth about whether this delivers on the request"
}}

Remember: You're not evaluating code quality - you're asking "Did this solve the user's actual problem?"
"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response['message']['content']
            
            # Parse the JSON response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                user_perspective = json.loads(json_content)
                
                # Add metadata
                user_perspective['validation_method'] = 'llm_user_perspective'
                user_perspective['applicable'] = True
                
                # Calculate score based on user satisfaction
                satisfaction_score = user_perspective.get('satisfaction_score', 5)
                user_perspective['score'] = satisfaction_score * 10  # Convert to 100-point scale
                
                # Determine status
                if satisfaction_score >= 8:
                    user_perspective['status'] = 'EXCELLENT'
                elif satisfaction_score >= 6:
                    user_perspective['status'] = 'GOOD'
                elif satisfaction_score >= 4:
                    user_perspective['status'] = 'FAIR'
                else:
                    user_perspective['status'] = 'POOR'
                
                return user_perspective
                
            else:
                raise ValueError("Could not parse JSON response")
                
        except Exception as e:
            print(f"[USER_PERSPECTIVE] LLM validation failed: {e}")
            # Fallback assessment
            return {
                'applicable': False,
                'error': f'User perspective validation failed: {str(e)}',
                'user_would_be_satisfied': False,
                'satisfaction_score': 3,
                'score': 30,
                'status': 'POOR',
                'honest_assessment': 'Could not perform user perspective validation',
                'validation_method': 'error_fallback'
            }
    
    def _check_task_completion(self, project_id: str) -> Dict[str, Any]:
        """Check task completion statistics."""
        
        print("📋 Checking task completion...")
        
        task_counts = self.task_queue.get_task_count_by_status()
        completed = task_counts.get('completed', 0)
        failed = task_counts.get('failed', 0)
        total = completed + failed
        
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        status = "EXCELLENT" if completion_rate >= 80 else \
                "GOOD" if completion_rate >= 60 else \
                "FAIR" if completion_rate >= 40 else "POOR"
        
        return {
            'status': status,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'total_tasks': total,
            'completion_rate': completion_rate,
            'score': min(100, completion_rate * 1.25)  # Bonus for high completion
        }
    
    def _check_artifacts_exist(self, project_id: str, objective: str) -> Dict[str, Any]:
        """Check if project artifacts actually exist and are non-empty."""
        
        print("📁 Checking artifact existence...")
        
        # Find project folders
        artifacts_dir = "artifacts"
        found_artifacts = []
        project_folders = []
        
        if os.path.exists(artifacts_dir):
            # Look for project folders related to this objective
            for item in os.listdir(artifacts_dir):
                item_path = os.path.join(artifacts_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    project_folders.append(item_path)
        
        # Analyze each project folder
        for folder_path in project_folders:
            for file in os.listdir(folder_path):
                if not file.startswith('.') and file != 'README.md':
                    file_path = os.path.join(folder_path, file)
                    if os.path.isfile(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            found_artifacts.append({
                                'name': file,
                                'path': file_path,
                                'size': len(content),
                                'type': self._classify_file_type(file),
                                'non_empty': len(content.strip()) > 100,  # Meaningful content
                                'folder': os.path.basename(folder_path)
                            })
                        except:
                            pass
        
        # Calculate score
        meaningful_artifacts = [a for a in found_artifacts if a['non_empty']]
        score = min(100, len(meaningful_artifacts) * 25)  # Up to 4 files = 100%
        
        status = "EXCELLENT" if len(meaningful_artifacts) >= 3 else \
                "GOOD" if len(meaningful_artifacts) >= 2 else \
                "FAIR" if len(meaningful_artifacts) >= 1 else "POOR"
        
        return {
            'status': status,
            'found_artifacts': found_artifacts,
            'meaningful_artifacts': len(meaningful_artifacts),
            'total_artifacts': len(found_artifacts),
            'score': score,
            'project_folders': [os.path.basename(f) for f in project_folders]
        }
    
    def _check_project_structure(self, project_id: str, objective: str) -> Dict[str, Any]:
        """Check if project has proper structure and entry points."""
        
        print("🏗️ Checking project structure...")
        
        # Get all project artifacts
        artifacts_dir = "artifacts"
        structure_score = 0
        issues = []
        strengths = []
        
        # Look for entry points
        has_html_entry = False
        has_python_main = False
        has_readme = False
        has_organized_structure = False
        
        if os.path.exists(artifacts_dir):
            for folder in os.listdir(artifacts_dir):
                folder_path = os.path.join(artifacts_dir, folder)
                if os.path.isdir(folder_path) and not folder.startswith('.'):
                    has_organized_structure = True
                    
                    files = os.listdir(folder_path)
                    
                    # Check for entry points
                    if 'index.html' in files:
                        has_html_entry = True
                        strengths.append("HTML entry point (index.html) present")
                        structure_score += 25
                    
                    if 'main.py' in files:
                        has_python_main = True
                        strengths.append("Python main entry point present")
                        structure_score += 25
                    
                    if 'README.md' in files:
                        has_readme = True
                        strengths.append("Documentation (README.md) present")
                        structure_score += 15
                    
                    # Check for multiple related files
                    code_files = [f for f in files if f.endswith(('.js', '.py', '.java', '.cpp'))]
                    if len(code_files) >= 2:
                        strengths.append(f"Multiple code files ({len(code_files)}) - good modularity")
                        structure_score += 20
                    
                    # Bonus for organized folder structure
                    if has_organized_structure:
                        strengths.append("Organized project folder structure")
                        structure_score += 15
        
        # Identify missing elements
        if not has_html_entry and 'javascript' in objective.lower():
            issues.append("Missing HTML entry point for JavaScript project")
        
        if not has_python_main and 'python' in objective.lower():
            issues.append("Missing Python main.py entry point")
        
        if not has_readme:
            issues.append("Missing project documentation (README.md)")
        
        if not has_organized_structure:
            issues.append("No organized project structure found")
        
        status = "EXCELLENT" if structure_score >= 80 else \
                "GOOD" if structure_score >= 60 else \
                "FAIR" if structure_score >= 40 else "POOR"
        
        return {
            'status': status,
            'score': min(100, structure_score),
            'has_entry_points': has_html_entry or has_python_main,
            'has_documentation': has_readme,
            'has_organized_structure': has_organized_structure,
            'strengths': strengths,
            'issues': issues
        }
    
    def _check_feature_completeness(self, objective: str, artifacts_check: Dict[str, Any]) -> Dict[str, Any]:
        """Check if generated project includes all requested features."""
        
        print("🎯 Checking feature completeness...")
        
        # Extract expected features from objective
        objective_lower = objective.lower()
        expected_features = []
        found_features = []
        
        # Parse common project types and their features
        if 'doom' in objective_lower or 'game' in objective_lower:
            expected_features = ['raycasting', 'player movement', 'enemies', 'rendering']
        elif 'calculator' in objective_lower:
            expected_features = ['addition', 'subtraction', 'multiplication', 'division']
        elif 'todo' in objective_lower or 'task' in objective_lower:
            expected_features = ['add task', 'remove task', 'list tasks', 'storage']
        elif 'web' in objective_lower:
            expected_features = ['html', 'css', 'javascript', 'user interface']
        else:
            # Generic feature extraction from objective
            feature_keywords = ['engine', 'movement', 'ai', 'interface', 'system', 'manager']
            expected_features = [word for word in objective_lower.split() 
                               if any(keyword in word for keyword in feature_keywords)]
        
        # Check artifacts for feature implementation
        artifacts = artifacts_check.get('found_artifacts', [])
        all_content = ""
        
        for artifact in artifacts:
            try:
                with open(artifact['path'], 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    all_content += content + " "
            except:
                pass
        
        # Check which features are implemented
        for feature in expected_features:
            if feature in all_content or feature.replace(' ', '') in all_content:
                found_features.append(feature)
        
        completion_rate = (len(found_features) / len(expected_features) * 100) if expected_features else 100
        
        status = "EXCELLENT" if completion_rate >= 90 else \
                "GOOD" if completion_rate >= 70 else \
                "FAIR" if completion_rate >= 50 else "POOR"
        
        missing_features = [f for f in expected_features if f not in found_features]
        
        return {
            'status': status,
            'score': completion_rate,
            'expected_features': expected_features,
            'found_features': found_features,
            'missing_features': missing_features,
            'completion_rate': completion_rate
        }
    
    def _check_technical_integrity(self, artifacts_check: Dict[str, Any]) -> Dict[str, Any]:
        """Check technical quality of generated code."""
        
        print("🔧 Checking technical integrity...")
        
        artifacts = artifacts_check.get('found_artifacts', [])
        
        # Technical quality metrics
        total_score = 0
        checks_performed = 0
        issues = []
        strengths = []
        
        for artifact in artifacts:
            if artifact['type'] in ['javascript', 'python', 'java']:
                checks_performed += 1
                
                try:
                    with open(artifact['path'], 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check code quality indicators
                    if len(content) > 200:  # Substantial code
                        total_score += 20
                        strengths.append(f"{artifact['name']}: Substantial implementation")
                    
                    # Check for functions/classes
                    if 'function ' in content or 'def ' in content or 'class ' in content:
                        total_score += 15
                        strengths.append(f"{artifact['name']}: Well-structured with functions/classes")
                    
                    # Check for comments
                    if '//' in content or '#' in content or '/*' in content:
                        total_score += 10
                        strengths.append(f"{artifact['name']}: Includes code comments")
                    
                    # Check for error handling
                    if 'try' in content or 'catch' in content or 'except' in content:
                        total_score += 10
                        strengths.append(f"{artifact['name']}: Includes error handling")
                    
                except Exception as e:
                    issues.append(f"Could not analyze {artifact['name']}: {str(e)}")
        
        # Calculate average score
        avg_score = (total_score / max(checks_performed, 1)) if checks_performed > 0 else 0
        
        status = "EXCELLENT" if avg_score >= 50 else \
                "GOOD" if avg_score >= 35 else \
                "FAIR" if avg_score >= 20 else "POOR"
        
        return {
            'status': status,
            'score': min(100, avg_score * 2),  # Scale to 100
            'files_analyzed': checks_performed,
            'strengths': strengths,
            'issues': issues
        }
    
    def _generate_overall_assessment(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall project assessment - now includes user perspective."""
        
        checks = validation_report['checks']
        
        # Updated weights to include user perspective as the most important factor
        weights = {
            'user_perspective': 0.40,      # NEW: Most important - does it actually work for the user?
            'task_completion': 0.20,       # Reduced from 0.25
            'artifacts_existence': 0.15,   # Reduced from 0.25
            'project_structure': 0.15,     # Reduced from 0.20
            'feature_completeness': 0.10,  # Reduced from 0.20
            'technical_integrity': 0.10    # Unchanged
        }
        
        overall_score = 0
        for check_name, weight in weights.items():
            if check_name in checks:
                check_score = checks[check_name].get('score', 0)
                overall_score += check_score * weight
        
        # Determine overall status - be more strict since we now check user satisfaction
        if overall_score >= 85:
            status = "EXCELLENT"
            emoji = "🎉"
        elif overall_score >= 70:
            status = "GOOD"
            emoji = "✅"
        elif overall_score >= 50:
            status = "FAIR"
            emoji = "⚠️"
        else:
            status = "NEEDS_IMPROVEMENT"
            emoji = "❌"
        
        # Generate recommendations based on user perspective
        recommendations = []
        all_issues = []
        
        # Prioritize user perspective issues
        user_perspective = checks.get('user_perspective', {})
        if not user_perspective.get('user_would_be_satisfied', True):
            if user_perspective.get('quick_fix_suggestion'):
                recommendations.insert(0, f"Priority fix: {user_perspective['quick_fix_suggestion']}")
            if user_perspective.get('the_one_biggest_problem'):
                recommendations.insert(0, f"Main issue: {user_perspective['the_one_biggest_problem']}")
        
        # Add other recommendations
        for check in checks.values():
            if 'issues' in check:
                all_issues.extend(check['issues'])
        
        if overall_score < 70:
            recommendations.append("Consider regenerating failed tasks to improve completeness")
        
        if not validation_report['artifacts']:
            recommendations.append("Verify that artifact generation is working properly")
        
        if all_issues:
            recommendations.append("Address structural and technical issues identified")
        
        return {
            'overall_status': status,
            'score': round(overall_score, 1),
            'emoji': emoji,
            'recommendations': recommendations,
            'issues': all_issues
        }
    
    def _print_validation_report(self, report: Dict[str, Any]):
        """Print a comprehensive validation report - now includes user perspective."""
        
        print(f"\n{report['emoji']} PROJECT VALIDATION COMPLETE")
        print("="*60)
        print(f"📊 Overall Score: {report['score']}/100 ({report['overall_status']})")
        print(f"🎯 Objective: {report['objective']}")
        
        # NEW: Highlight user satisfaction prominently
        user_satisfaction = report.get('user_satisfaction', {})
        if user_satisfaction.get('applicable', True):
            satisfaction = user_satisfaction.get('satisfaction_score', 5)
            satisfied = user_satisfaction.get('user_would_be_satisfied', False)
            status_emoji = "😊" if satisfied else "😞"
            print(f"{status_emoji} User Satisfaction: {satisfaction}/10 ({'Satisfied' if satisfied else 'Not Satisfied'})")
            
            if user_satisfaction.get('honest_assessment'):
                print(f"💭 Reality Check: {user_satisfaction['honest_assessment']}")
        
        print()
        
        # Print individual check results
        checks = report['checks']
        
        print("📋 DETAILED RESULTS:")
        for check_name, check_data in checks.items():
            status_emoji = "✅" if check_data['status'] in ['EXCELLENT', 'GOOD'] else \
                          "⚠️" if check_data['status'] == 'FAIR' else "❌"
            
            check_title = check_name.replace('_', ' ').title()
            score = check_data.get('score', 0)
            print(f"  {status_emoji} {check_title}: {score:.0f}/100 ({check_data['status']})")
        
        print()
        
        # NEW: Show key user perspective insights
        if user_satisfaction.get('applicable', True):
            print("👤 USER PERSPECTIVE INSIGHTS:")
            if user_satisfaction.get('clear_entry_point') is not None:
                entry_emoji = "✅" if user_satisfaction['clear_entry_point'] else "❌"
                print(f"  {entry_emoji} Clear entry point: {user_satisfaction['clear_entry_point']}")
            
            if user_satisfaction.get('actually_works') is not None:
                works_emoji = "✅" if user_satisfaction['actually_works'] else "❌"
                print(f"  {works_emoji} Actually works: {user_satisfaction['actually_works']}")
            
            if user_satisfaction.get('first_impression'):
                print(f"  🎭 First impression: {user_satisfaction['first_impression']}")
            
            if user_satisfaction.get('major_gaps'):
                gaps = user_satisfaction['major_gaps']
                if gaps:
                    print(f"  🕳️ Major gaps: {', '.join(gaps[:3])}")
            
            print()
        
        # Print artifacts found
        if report['artifacts']:
            print("📁 GENERATED ARTIFACTS:")
            for artifact in report['artifacts']:
                size_kb = artifact['size'] / 1024
                print(f"  📄 {artifact['name']} ({size_kb:.1f}KB) - {artifact['type']}")
        else:
            print("❌ NO ARTIFACTS FOUND")
        
        print()
        
        # Print recommendations (now prioritized by user perspective)
        if report['recommendations']:
            print("💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
            print()
        
        # Print issues
        if report['issues']:
            print("⚠️ ISSUES IDENTIFIED:")
            for issue in report['issues'][:5]:  # Limit to 5 issues
                print(f"  • {issue}")
            if len(report['issues']) > 5:
                print(f"  • ... and {len(report['issues']) - 5} more issues")
            print()
    
    def _classify_file_type(self, filename: str) -> str:
        """Classify file type for analysis."""
        
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        type_map = {
            'js': 'javascript',
            'py': 'python',
            'java': 'java',
            'cpp': 'cpp',
            'cs': 'csharp',
            'html': 'html',
            'css': 'css',
            'md': 'documentation',
            'txt': 'text'
        }
        
        return type_map.get(ext, 'unknown')