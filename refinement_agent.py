import ollama
import os
import json
from typing import Dict, Any, List, Optional
from task_queue import TaskQueue, TaskStatus
from context_manager import ContextManager
from language_classifier import LanguageClassifier

class RefinementAgent:
    """Autonomous agent that evaluates projects and generates improvement plans."""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.task_queue = TaskQueue()
        self.context_manager = ContextManager()
        self.language_classifier = LanguageClassifier()
        self.artifacts_dir = "artifacts"
    
    def evaluate_project(self, project_id: str, project_name: str) -> Dict[str, Any]:
        """Comprehensively evaluate a project and identify improvement opportunities."""
        
        print(f"[REFINEMENT] Analyzing project: {project_name}")
        
        # Gather project artifacts and context
        project_context = self._gather_project_context(project_id, project_name)
        
        if not project_context['artifacts']:
            return {
                'success': False,
                'error': 'No artifacts found to evaluate'
            }
        
        # Analyze each aspect of the project
        analyses = {
            'code_quality': self._analyze_code_quality(project_context),
            'functionality': self._analyze_functionality(project_context),
            'user_experience': self._analyze_user_experience(project_context),
            'architecture': self._analyze_architecture(project_context),
            'performance': self._analyze_performance(project_context),
            'completeness': self._analyze_completeness(project_context)
        }
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(project_context, analyses)
        
        # Create improvement plan
        improvement_plan = self._create_improvement_plan(project_context, analyses, overall_assessment)
        
        return {
            'success': True,
            'project_name': project_name,
            'analyses': analyses,
            'overall_assessment': overall_assessment,
            'improvement_plan': improvement_plan,
            'project_context': project_context
        }
    
    def _gather_project_context(self, project_id: str, project_name: str) -> Dict[str, Any]:
        """Gather comprehensive context about the project."""
        
        project_dir = os.path.join(self.artifacts_dir, project_name)
        artifacts = []
        
        if os.path.exists(project_dir):
            for item in os.listdir(project_dir):
                if item.startswith('.'):
                    continue
                    
                item_path = os.path.join(project_dir, item)
                if os.path.isfile(item_path):
                    try:
                        with open(item_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        artifacts.append({
                            'name': item,
                            'path': item_path,
                            'content': content,
                            'size': len(content),
                            'type': self._classify_file_type(item, content)
                        })
                    except Exception as e:
                        print(f"[REFINEMENT] Could not read {item}: {e}")
        
        # Get project state and completed tasks
        project_state = self.task_queue.get_project_state(project_id)
        completed_tasks = self.task_queue.get_completed_tasks()
        task_counts = self.task_queue.get_task_count_by_status()
        
        return {
            'project_id': project_id,
            'project_name': project_name,
            'project_dir': project_dir,
            'artifacts': artifacts,
            'project_state': project_state,
            'completed_tasks': completed_tasks,
            'task_counts': task_counts
        }
    
    def _classify_file_type(self, filename: str, content: str) -> str:
        """Classify the type of file based on extension and content."""
        
        if filename.endswith('.py'):
            return 'python_code'
        elif filename.endswith('.js'):
            return 'javascript_code'
        elif filename.endswith('.java'):
            return 'java_code'
        elif filename.endswith(('.cpp', '.cc', '.cxx')):
            return 'cpp_code'
        elif filename.endswith('.cs'):
            return 'csharp_code'
        elif filename.endswith('.go'):
            return 'go_code'
        elif filename.endswith('.rs'):
            return 'rust_code'
        elif filename.endswith('.html'):
            return 'html_markup'
        elif filename.endswith('.css'):
            return 'css_styles'
        elif filename.endswith('.md'):
            return 'documentation'
        elif filename.endswith('.txt'):
            return 'text_content'
        else:
            return 'unknown'
    
    def _analyze_code_quality(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code quality aspects."""
        
        code_files = [artifact for artifact in project_context['artifacts'] 
                     if 'code' in artifact['type']]
        
        if not code_files:
            return {'applicable': False, 'reason': 'No code files found'}
        
        # Analyze code using LLM
        analysis_prompt = f"""You are a senior code reviewer analyzing project quality.

PROJECT: {project_context['project_name']}
OBJECTIVE: {project_context['project_state']['objective'] if project_context['project_state'] else 'Unknown'}

CODE FILES TO ANALYZE:
"""
        
        for file_info in code_files[:5]:  # Analyze up to 5 files
            analysis_prompt += f"""
FILE: {file_info['name']} ({file_info['type']})
```
{file_info['content'][:2000]}{'...' if len(file_info['content']) > 2000 else ''}
```
"""
        
        analysis_prompt += """
Analyze the code quality and provide a detailed assessment:

1. CODE STRUCTURE AND ORGANIZATION
2. NAMING CONVENTIONS AND CLARITY  
3. ERROR HANDLING AND ROBUSTNESS
4. COMMENTS AND DOCUMENTATION
5. ADHERENCE TO BEST PRACTICES
6. POTENTIAL BUGS OR ISSUES

For each aspect, provide:
- Current state (Good/Fair/Poor)
- Specific issues found
- Improvement recommendations

Respond in JSON format:
{
  "overall_score": 1-10,
  "structure": {"rating": "Good/Fair/Poor", "issues": [], "recommendations": []},
  "naming": {"rating": "Good/Fair/Poor", "issues": [], "recommendations": []},
  "error_handling": {"rating": "Good/Fair/Poor", "issues": [], "recommendations": []},
  "documentation": {"rating": "Good/Fair/Poor", "issues": [], "recommendations": []},
  "best_practices": {"rating": "Good/Fair/Poor", "issues": [], "recommendations": []},
  "potential_bugs": {"rating": "Good/Fair/Poor", "issues": [], "recommendations": []}
}"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            content = response['message']['content']
            # Extract JSON from response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                analysis = json.loads(json_content)
                analysis['applicable'] = True
                return analysis
            else:
                return {'applicable': False, 'error': 'Could not parse analysis response'}
                
        except Exception as e:
            return {'applicable': False, 'error': f'Analysis failed: {str(e)}'}
    
    def _analyze_functionality(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if the project fulfills its intended functionality."""
        
        artifacts = project_context['artifacts']
        objective = project_context['project_state']['objective'] if project_context['project_state'] else 'Unknown'
        
        analysis_prompt = f"""You are a product manager evaluating project completeness.

PROJECT OBJECTIVE: {objective}

PROJECT FILES:
"""
        
        for artifact in artifacts[:10]:
            analysis_prompt += f"- {artifact['name']} ({artifact['type']}, {artifact['size']} chars)\n"
        
        analysis_prompt += f"""
MAIN FILE CONTENT:
```
{artifacts[0]['content'][:3000] if artifacts else 'No content'}
```

Evaluate functionality against the stated objective:

1. CORE FEATURES IMPLEMENTATION
2. FEATURE COMPLETENESS  
3. MISSING FUNCTIONALITY
4. USABILITY AND USER EXPERIENCE
5. EDGE CASE HANDLING

Respond in JSON format:
{{
  "completeness_score": 1-10,
  "implemented_features": [],
  "missing_features": [],
  "usability_rating": "Excellent/Good/Fair/Poor",
  "usability_issues": [],
  "recommendations": []
}}"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            content = response['message']['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx]
                analysis = json.loads(json_content)
                analysis['applicable'] = True
                return analysis
            else:
                return {'applicable': False, 'error': 'Could not parse functionality analysis'}
                
        except Exception as e:
            return {'applicable': False, 'error': f'Functionality analysis failed: {str(e)}'}
    
    def _analyze_user_experience(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user experience and interface design."""
        
        ui_files = [artifact for artifact in project_context['artifacts'] 
                   if any(keyword in artifact['type'] for keyword in ['code', 'html', 'css'])]
        
        if not ui_files:
            return {'applicable': False, 'reason': 'No UI-related files found'}
        
        # Simple UX analysis based on code patterns
        ux_issues = []
        ux_recommendations = []
        
        for file_info in ui_files:
            content = file_info['content'].lower()
            
            # Check for common UX patterns
            if 'tkinter' in content:
                if '.pack(' in content and '.grid(' in content:
                    ux_issues.append(f"{file_info['name']}: Mixing tkinter layout managers")
                    ux_recommendations.append("Use consistent layout manager (preferably grid)")
                
                if 'messagebox' not in content and 'error' in content:
                    ux_issues.append(f"{file_info['name']}: No user feedback for errors")
                    ux_recommendations.append("Add messagebox or status feedback for user actions")
            
            if 'input(' in content and 'try:' not in content:
                ux_issues.append(f"{file_info['name']}: No input validation")
                ux_recommendations.append("Add input validation and error handling")
        
        return {
            'applicable': True,
            'ux_score': max(1, 10 - len(ux_issues) * 2),
            'issues': ux_issues,
            'recommendations': ux_recommendations
        }
    
    def _analyze_architecture(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project architecture and organization."""
        
        artifacts = project_context['artifacts']
        
        # Simple architectural analysis
        has_main_file = any('main' in artifact['name'].lower() for artifact in artifacts)
        has_modules = len([a for a in artifacts if 'code' in a['type']]) > 1
        has_documentation = any('documentation' in artifact['type'] for artifact in artifacts)
        
        architecture_score = 0
        issues = []
        recommendations = []
        
        if has_main_file:
            architecture_score += 3
        else:
            issues.append("No clear main entry point")
            recommendations.append("Create a main.py or equivalent entry point")
        
        if has_modules:
            architecture_score += 3
        else:
            issues.append("Monolithic structure - all code in one file")
            recommendations.append("Split functionality into separate modules")
        
        if has_documentation:
            architecture_score += 2
        else:
            issues.append("Missing documentation")
            recommendations.append("Add README.md with usage instructions")
        
        # Check for separation of concerns
        code_files = [a for a in artifacts if 'code' in a['type']]
        if len(code_files) > 1:
            architecture_score += 2
        
        return {
            'applicable': True,
            'architecture_score': min(10, architecture_score),
            'has_main_entry': has_main_file,
            'is_modular': has_modules,
            'has_docs': has_documentation,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _analyze_performance(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze potential performance issues."""
        
        code_files = [artifact for artifact in project_context['artifacts'] 
                     if 'code' in artifact['type']]
        
        if not code_files:
            return {'applicable': False, 'reason': 'No code files to analyze'}
        
        performance_issues = []
        recommendations = []
        
        for file_info in code_files:
            content = file_info['content'].lower()
            
            # Check for common performance anti-patterns
            if 'for' in content and 'for' in content[content.find('for')+10:]:
                if 'sleep(' in content:
                    performance_issues.append(f"{file_info['name']}: Sleep in loop detected")
                    recommendations.append("Avoid blocking operations in loops")
            
            if content.count('import') > 20:
                performance_issues.append(f"{file_info['name']}: Too many imports")
                recommendations.append("Optimize imports and use specific imports")
            
            if 'while true:' in content and 'break' not in content:
                performance_issues.append(f"{file_info['name']}: Potential infinite loop")
                recommendations.append("Add proper loop termination conditions")
        
        performance_score = max(1, 10 - len(performance_issues) * 3)
        
        return {
            'applicable': True,
            'performance_score': performance_score,
            'issues': performance_issues,
            'recommendations': recommendations
        }
    
    def _analyze_completeness(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how complete the project is relative to its objective."""
        
        objective = project_context['project_state']['objective'] if project_context['project_state'] else 'Unknown'
        completed_tasks = len(project_context['completed_tasks'])
        pending_tasks = project_context['task_counts'].get('pending', 0)
        failed_tasks = project_context['task_counts'].get('failed', 0)
        
        total_tasks = completed_tasks + pending_tasks + failed_tasks
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Assess completeness based on objective keywords
        objective_lower = objective.lower()
        artifacts = project_context['artifacts']
        
        has_core_functionality = len([a for a in artifacts if 'code' in a['type']]) > 0
        has_documentation = any('documentation' in a['type'] for a in artifacts)
        has_tests = any('test' in a['name'].lower() for a in artifacts)
        
        completeness_factors = []
        if has_core_functionality:
            completeness_factors.append("Core functionality implemented")
        if has_documentation:
            completeness_factors.append("Documentation provided")
        if has_tests:
            completeness_factors.append("Tests included")
        if failed_tasks == 0:
            completeness_factors.append("No failed tasks")
        
        missing_elements = []
        if not has_documentation:
            missing_elements.append("User documentation")
        if not has_tests:
            missing_elements.append("Unit tests")
        if pending_tasks > 0:
            missing_elements.append(f"{pending_tasks} pending tasks")
        if failed_tasks > 0:
            missing_elements.append(f"{failed_tasks} failed tasks")
        
        return {
            'applicable': True,
            'completion_percentage': completion_percentage,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'failed_tasks': failed_tasks,
            'completeness_factors': completeness_factors,
            'missing_elements': missing_elements,
            'has_core_functionality': has_core_functionality,
            'has_documentation': has_documentation,
            'has_tests': has_tests
        }
    
    def _generate_overall_assessment(self, project_context: Dict[str, Any], analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an overall project assessment."""
        
        # Calculate overall scores
        applicable_analyses = {k: v for k, v in analyses.items() if v.get('applicable', True)}
        
        scores = []
        if 'code_quality' in applicable_analyses and 'overall_score' in applicable_analyses['code_quality']:
            scores.append(applicable_analyses['code_quality']['overall_score'])
        if 'functionality' in applicable_analyses and 'completeness_score' in applicable_analyses['functionality']:
            scores.append(applicable_analyses['functionality']['completeness_score'])
        if 'user_experience' in applicable_analyses and 'ux_score' in applicable_analyses['user_experience']:
            scores.append(applicable_analyses['user_experience']['ux_score'])
        if 'architecture' in applicable_analyses and 'architecture_score' in applicable_analyses['architecture']:
            scores.append(applicable_analyses['architecture']['architecture_score'])
        if 'performance' in applicable_analyses and 'performance_score' in applicable_analyses['performance']:
            scores.append(applicable_analyses['performance']['performance_score'])
        
        overall_score = sum(scores) / len(scores) if scores else 5
        
        # Determine project status
        if overall_score >= 8:
            status = "Excellent"
            priority = "Low"
        elif overall_score >= 6:
            status = "Good"
            priority = "Medium"
        elif overall_score >= 4:
            status = "Fair"
            priority = "High"
        else:
            status = "Needs Improvement"
            priority = "Critical"
        
        return {
            'overall_score': round(overall_score, 1),
            'status': status,
            'improvement_priority': priority,
            'strengths': self._identify_strengths(analyses),
            'key_weaknesses': self._identify_weaknesses(analyses)
        }
    
    def _identify_strengths(self, analyses: Dict[str, Any]) -> List[str]:
        """Identify project strengths from analyses."""
        
        strengths = []
        
        if analyses.get('architecture', {}).get('has_main_entry'):
            strengths.append("Clear entry point")
        if analyses.get('architecture', {}).get('is_modular'):
            strengths.append("Modular architecture")
        if analyses.get('completeness', {}).get('has_documentation'):
            strengths.append("Documentation provided")
        if analyses.get('completeness', {}).get('failed_tasks', 1) == 0:
            strengths.append("No failed tasks")
        
        return strengths
    
    def _identify_weaknesses(self, analyses: Dict[str, Any]) -> List[str]:
        """Identify key weaknesses from analyses."""
        
        weaknesses = []
        
        # Collect issues from all analyses
        for analysis_name, analysis in analyses.items():
            if analysis.get('applicable', True):
                if 'issues' in analysis:
                    weaknesses.extend(analysis['issues'][:2])  # Top 2 issues per analysis
        
        return weaknesses[:5]  # Return top 5 weaknesses
    
    def _create_improvement_plan(self, project_context: Dict[str, Any], analyses: Dict[str, Any], assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed improvement plan with prioritized tasks."""
        
        # Collect all recommendations
        all_recommendations = []
        
        for analysis_name, analysis in analyses.items():
            if analysis.get('applicable', True) and 'recommendations' in analysis:
                for rec in analysis['recommendations']:
                    all_recommendations.append({
                        'category': analysis_name,
                        'recommendation': rec,
                        'priority': self._calculate_recommendation_priority(analysis_name, assessment)
                    })
        
        # Sort by priority
        all_recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        # Group into improvement phases
        critical_improvements = [r for r in all_recommendations if r['priority'] >= 8]
        important_improvements = [r for r in all_recommendations if 5 <= r['priority'] < 8]
        nice_to_have = [r for r in all_recommendations if r['priority'] < 5]
        
        return {
            'total_recommendations': len(all_recommendations),
            'critical_improvements': critical_improvements[:5],
            'important_improvements': important_improvements[:5],
            'nice_to_have': nice_to_have[:3],
            'estimated_effort': self._estimate_improvement_effort(all_recommendations),
            'suggested_next_steps': self._generate_next_steps(critical_improvements, important_improvements)
        }
    
    def _calculate_recommendation_priority(self, category: str, assessment: Dict[str, Any]) -> int:
        """Calculate priority score for a recommendation."""
        
        base_priorities = {
            'functionality': 10,    # Core functionality is highest priority
            'code_quality': 8,      # Code quality is very important
            'user_experience': 7,   # UX is important for usability
            'architecture': 6,      # Architecture affects maintainability
            'performance': 5,       # Performance can be optimized later
            'completeness': 9       # Completeness is critical
        }
        
        base_score = base_priorities.get(category, 5)
        
        # Adjust based on overall assessment
        if assessment['improvement_priority'] == 'Critical':
            base_score += 2
        elif assessment['improvement_priority'] == 'High':
            base_score += 1
        
        return min(10, base_score)
    
    def _estimate_improvement_effort(self, recommendations: List[Dict[str, Any]]) -> str:
        """Estimate the effort required for improvements."""
        
        if len(recommendations) <= 3:
            return "Low (1-2 hours)"
        elif len(recommendations) <= 8:
            return "Medium (3-6 hours)"
        elif len(recommendations) <= 15:
            return "High (1-2 days)"
        else:
            return "Very High (3+ days)"
    
    def _generate_next_steps(self, critical: List[Dict], important: List[Dict]) -> List[str]:
        """Generate suggested next steps."""
        
        steps = []
        
        if critical:
            steps.append(f"Address critical issue: {critical[0]['recommendation']}")
        
        if len(critical) > 1:
            steps.append(f"Fix remaining critical issues ({len(critical)-1} items)")
        
        if important:
            steps.append(f"Improve: {important[0]['recommendation']}")
        
        if len(steps) == 0:
            steps.append("Project is in good shape - consider adding tests or documentation")
        
        return steps[:3]  # Return top 3 next steps
    
    def generate_refinement_tasks(self, project_id: str, improvement_plan: Dict[str, Any]) -> List[str]:
        """Generate specific refinement tasks from improvement plan."""
        
        refinement_tasks = []
        
        # Add critical improvements as high-priority tasks
        for improvement in improvement_plan['critical_improvements']:
            task_title = f"Critical Fix: {improvement['recommendation']}"
            task_description = f"Address critical {improvement['category']} issue: {improvement['recommendation']}"
            
            task_id = self.task_queue.add_task(
                title=task_title,
                description=task_description,
                subtask_data={
                    'deliverable': 'Improved code/functionality',
                    'project_id': project_id,
                    'refinement_type': 'critical',
                    'category': improvement['category']
                },
                priority=10
            )
            refinement_tasks.append(task_id)
        
        # Add important improvements as medium-priority tasks
        for improvement in improvement_plan['important_improvements'][:3]:  # Limit to 3
            task_title = f"Improve: {improvement['recommendation']}"
            task_description = f"Enhance {improvement['category']}: {improvement['recommendation']}"
            
            task_id = self.task_queue.add_task(
                title=task_title,
                description=task_description,
                subtask_data={
                    'deliverable': 'Enhanced functionality',
                    'project_id': project_id,
                    'refinement_type': 'improvement',
                    'category': improvement['category']
                },
                priority=7
            )
            refinement_tasks.append(task_id)
        
        return refinement_tasks