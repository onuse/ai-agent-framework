import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from task_queue import TaskQueue
from project_folder_manager import ProjectFolderManager

class ProjectCompletenessAgent:
    """Agent that performs final validation and completeness checks on generated projects."""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
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
            'issues': []
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
        
        # 6. Generate overall assessment
        overall_assessment = self._generate_overall_assessment(validation_report)
        validation_report.update(overall_assessment)
        
        # 7. Print comprehensive report
        self._print_validation_report(validation_report)
        
        return validation_report
    
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
        """Generate overall project assessment."""
        
        checks = validation_report['checks']
        
        # Calculate weighted overall score
        weights = {
            'task_completion': 0.25,
            'artifacts_existence': 0.25,
            'project_structure': 0.20,
            'feature_completeness': 0.20,
            'technical_integrity': 0.10
        }
        
        overall_score = 0
        for check_name, weight in weights.items():
            if check_name in checks:
                check_score = checks[check_name].get('score', 0)
                overall_score += check_score * weight
        
        # Determine overall status
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
        
        # Generate recommendations
        recommendations = []
        all_issues = []
        
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
        """Print a comprehensive validation report."""
        
        print(f"\n{report['emoji']} PROJECT VALIDATION COMPLETE")
        print("="*60)
        print(f"📊 Overall Score: {report['score']}/100 ({report['overall_status']})")
        print(f"🎯 Objective: {report['objective']}")
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
        
        # Print artifacts found
        if report['artifacts']:
            print("📁 GENERATED ARTIFACTS:")
            for artifact in report['artifacts']:
                size_kb = artifact['size'] / 1024
                print(f"  📄 {artifact['name']} ({size_kb:.1f}KB) - {artifact['type']}")
        else:
            print("❌ NO ARTIFACTS FOUND")
        
        print()
        
        # Print recommendations
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