#!/usr/bin/env python3
"""
AI Agent Framework v3.0 - Main Entry Point with Intelligent Planning

This is a hierarchical multi-agent system with intelligent project planning:
1. Project Planner creates comprehensive plans based on complexity assessment
2. Manager Agent coordinates task execution according to the plan
3. Worker Agents execute tasks with plan-aware context
4. System adapts the plan based on actual progress and discoveries

Key improvements:
- No more hardcoded "2-3 tasks" limitation
- Complexity-based task generation (1-20+ tasks)
- Dependency-aware execution
- Adaptive planning that evolves with progress
"""

import time
import sys
from manager_agent import ManagerAgent
from worker_agent import WorkerAgent

def main():
    """Main framework execution loop with intelligent planning."""
    
    print("=== AI Agent Framework v3.0 ===")
    print("Intelligent Planning + Hierarchical Multi-Agent System")
    print("Planning Agent → Manager Agent → Worker Agents")
    print("="*60)
    
    # Initialize agents
    manager = ManagerAgent()
    worker = WorkerAgent()
    
    # Set up communication between manager and worker
    worker.set_task_completion_callback(manager.on_task_completed)
    
    # Get objective from user
    if len(sys.argv) > 1:
        objective = " ".join(sys.argv[1:])
    else:
        objective = input("Enter your objective: ").strip()
        
    if not objective:
        print("No objective provided. Exiting.")
        return
    
    print(f"\nObjective: {objective}")
    print("="*60)
    
    # Phase 1: Intelligent Project Planning & Initial Task Generation
    print("\n🧠 PHASE 1: INTELLIGENT PROJECT PLANNING")
    print("="*60)
    
    project_id = manager.create_project("AI_Project", objective)
    
    # Show project plan status
    manager.show_project_plan_status(project_id)
    
    # Show initial project summary
    summary = manager.get_project_summary(project_id)
    print(f"\n📊 PROJECT OVERVIEW:")
    print(f"Name: {summary['project_name']}")
    print(f"Complexity: {summary['plan_info'].get('complexity_score', 0)}/10")
    print(f"Domain: {summary['plan_info'].get('primary_domain', 'unknown')}")
    print(f"Languages: {', '.join(summary['plan_info'].get('programming_languages', []))}")
    print(f"Planned Tasks: {summary['plan_info'].get('total_planned_tasks', 0)}")
    print(f"Current Phase: {summary['plan_info'].get('current_phase', 'unknown')}")
    print(f"Initial Queue: {summary['task_counts'].get('pending', 0)} tasks ready")
    
    # Phase 2: Adaptive Task Execution Loop
    print(f"\n⚙️ PHASE 2: ADAPTIVE TASK EXECUTION")
    print("="*60)
    
    main_iteration = 0
    improvement_attempt = 0
    max_main_iterations = 50  # Increased to handle larger projects
    max_improvement_attempts = 3
    
    while main_iteration < max_main_iterations:
        main_iteration += 1
        print(f"\n{'='*20} EXECUTION CYCLE {main_iteration} {'='*20}")
        
        # Execute pending tasks
        tasks_processed = execute_pending_tasks(worker, manager, project_id, main_iteration)
        
        if tasks_processed == 0:
            print("[MAIN] No pending tasks found")
            break
        
        # Evaluate progress using plan-aware evaluation
        print("\n[MANAGER] Evaluating progress...")
        evaluation = manager.evaluate_progress(project_id)
        
        print(f"[MANAGER] Status: {evaluation.get('status', 'unknown')}")
        print(f"[MANAGER] Completion: {evaluation.get('completion_percentage', 0):.1f}%")
        print(f"[MANAGER] Phase: {evaluation.get('current_phase', 'unknown')}")
        
        if evaluation.get('estimated_tasks_remaining', 0) > 0:
            print(f"[MANAGER] Remaining: {evaluation['estimated_tasks_remaining']} planned tasks")
        
        # Check if we need to generate more tasks from the plan
        if evaluation.get('status') != 'ready_for_validation':
            pending_tasks = manager.task_queue.get_task_count_by_status().get('pending', 0)
            if pending_tasks == 0 and evaluation.get('estimated_tasks_remaining', 0) > 0:
                print("\n[MANAGER] No pending tasks but plan has remaining work - generating next batch")
                project_plan = manager.get_project_plan(project_id)
                if project_plan:
                    manager._generate_tasks_from_plan(project_id, project_plan, max_tasks=5)
                continue
        
        # Phase 3: Validation and Self-Improvement
        if evaluation.get('status') == 'ready_for_validation':
            print("\n🔍 PHASE 3: USER PERSPECTIVE VALIDATION")
            print("="*60)
            
            validation_report = manager.perform_final_project_validation(project_id, objective)
            
            # Self-improvement loop
            if manager.should_continue_improvement(validation_report, improvement_attempt, max_improvement_attempts):
                improvement_attempt += 1
                print(f"\n🔧 IMPROVEMENT CYCLE {improvement_attempt}/{max_improvement_attempts}")
                print("="*60)
                
                improvement_task_ids = manager.generate_improvement_tasks_from_validation(
                    project_id, objective, validation_report
                )
                
                if improvement_task_ids:
                    print(f"[MANAGER] Generated {len(improvement_task_ids)} improvement tasks")
                    continue
                else:
                    print("[MANAGER] No improvement tasks generated - stopping")
                    break
            else:
                print("\n🎉 PROJECT COMPLETED WITH ACCEPTABLE SATISFACTION!")
                break
        
        # Small delay to prevent overwhelming the system
        time.sleep(1)
    
    # Phase 4: Final Project Summary
    print("\n" + "="*60)
    print("🏁 FINAL PROJECT SUMMARY")
    print("="*60)
    
    final_summary = manager.get_project_summary(project_id)
    plan_info = final_summary.get('plan_info', {})
    
    print(f"📋 Project: {final_summary['project_name']}")
    print(f"🎯 Objective: {final_summary['objective']}")
    print(f"📊 Complexity: {plan_info.get('complexity_score', 0)}/10")
    print(f"🏷️  Domain: {plan_info.get('primary_domain', 'unknown')}")
    print(f"💻 Languages: {', '.join(plan_info.get('programming_languages', []))}")
    print(f"✅ Planned Tasks: {plan_info.get('completed_planned_tasks', 0)}/{plan_info.get('total_planned_tasks', 0)}")
    print(f"📈 Final Status: {final_summary['current_phase']}")
    print(f"🔄 Improvement Cycles: {improvement_attempt}")
    print(f"⚙️ Total Execution Cycles: {main_iteration}")
    
    # Show final plan status
    if manager.get_project_plan(project_id):
        print(f"\n📋 FINAL PLAN STATUS:")
        manager.show_project_plan_status(project_id)
    
    # Show organized project structure
    print(f"\n📁 GENERATED PROJECT STRUCTURE:")
    worker.show_project_structure()
    
    # Provide user guidance
    print(f"\n💡 NEXT STEPS:")
    print(f"1. Check the artifacts directory for your completed project")
    print(f"2. Look for folders with entry points (index.html, main.py, etc.)")
    print(f"3. Read the README.md files for usage instructions")
    
    if main_iteration >= max_main_iterations:
        print(f"\n⚠️  Reached maximum execution cycles ({max_main_iterations})")
        print("Project may need manual intervention to complete.")
    else:
        print(f"\n🎊 Project completed successfully in {main_iteration} cycles!")

def execute_pending_tasks(worker: WorkerAgent, manager: ManagerAgent, project_id: str, main_iteration: int) -> int:
    """Execute all pending tasks and return count of tasks processed."""
    
    tasks_processed = 0
    task_iteration = 0
    max_task_iterations = 15  # Increased for larger projects
    
    while task_iteration < max_task_iterations:
        task_iteration += 1
        
        print(f"\n[WORKER] Processing task {task_iteration}...")
        task_result = worker.process_next_task()
        
        if not task_result:
            # No more tasks to process
            break
        
        tasks_processed += 1
        print(f"[WORKER] ✅ Completed: {task_result['title']}")
        print(f"[WORKER] Success: {task_result['success']}")
        
        # Show plan task information if available
        subtask_data = task_result.get('subtask_data', {})
        if subtask_data.get('plan_task_id'):
            print(f"[WORKER] Plan Task: {subtask_data['plan_task_id']}")
            dependencies = subtask_data.get('dependencies', [])
            if dependencies:
                print(f"[WORKER] Dependencies: {', '.join(dependencies)}")
        
        # Quick progress check after each task
        evaluation = manager.evaluate_progress(project_id)
        print(f"[PROGRESS] {evaluation.get('completion_percentage', 0):.0f}% complete")
        print(f"[PROGRESS] Phase: {evaluation.get('current_phase', 'unknown')}")
        
        # If we've completed initial development, break to allow validation
        if evaluation.get('status') == 'ready_for_validation':
            print("[PROGRESS] Plan completed - ready for validation")
            break
    
    if task_iteration >= max_task_iterations:
        print(f"[WORKER] Reached max task iterations ({max_task_iterations}) for this cycle")
    
    return tasks_processed

def run_complexity_demo():
    """Demo showing how the system handles different complexity levels."""
    
    print("=== COMPLEXITY-BASED PLANNING DEMO ===")
    print("See how the system adapts to different objective complexities")
    print()
    
    demo_objectives = [
        ("Simple: Create a hello world program", 1),
        ("Moderate: Create a calculator with GUI", 5), 
        ("Complex: Create a JavaScript doom clone with raycasting", 8),
        ("Advanced: Create a web-based project management system", 9)
    ]
    
    print("Choose a complexity level to demonstrate adaptive planning:")
    for i, (obj, complexity) in enumerate(demo_objectives, 1):
        print(f"{i}. {obj} (Complexity ~{complexity}/10)")
    
    choice = input("Enter choice (1-4): ").strip()
    
    try:
        objective, expected_complexity = demo_objectives[int(choice) - 1]
        objective = objective.split(": ", 1)[1]  # Remove prefix
        
        print(f"\n🧪 TESTING ADAPTIVE PLANNING")
        print(f"Objective: {objective}")
        print(f"Expected Complexity: {expected_complexity}/10")
        print("="*60)
        
        # Test just the planning phase
        from project_planner import ProjectPlanner
        planner = ProjectPlanner()
        
        # Show complexity assessment
        complexity_assessment = planner._assess_objective_complexity(objective)
        print(f"🔍 COMPLEXITY ASSESSMENT:")
        print(f"Score: {complexity_assessment.get('complexity_score', 0)}/10")
        print(f"Level: {complexity_assessment.get('complexity_level', 'unknown')}")
        print(f"Reasoning: {complexity_assessment.get('reasoning', 'No reasoning')}")
        
        # Show project plan
        project_plan = planner.create_project_plan(objective)
        estimated_tasks = project_plan['task_breakdown'].get('estimated_tasks', 0)
        
        print(f"\n📋 GENERATED PLAN:")
        print(f"Estimated Tasks: {estimated_tasks}")
        print(f"Primary Domain: {project_plan.get('project_summary', {}).get('primary_domain', 'unknown')}")
        
        # Show first few tasks
        tasks = project_plan['task_breakdown'].get('tasks', [])
        print(f"\nFirst 3 Tasks:")
        for i, task in enumerate(tasks[:3], 1):
            print(f"  {i}. {task.get('title', 'Unknown')}")
            deps = task.get('dependencies', [])
            if deps:
                print(f"     Dependencies: {', '.join(deps)}")
        
        if len(tasks) > 3:
            print(f"  ... and {len(tasks) - 3} more tasks")
        
        print(f"\n✨ Adaptive planning successfully created {estimated_tasks} tasks!")
        print(f"This demonstrates how the system scales from simple to complex projects.")
        
    except (ValueError, IndexError):
        print("Invalid choice, running default demo")
        run_simple_test()

def run_simple_test():
    """Run a simple test to verify the planning system works."""
    
    print("=== SIMPLE PLANNING SYSTEM TEST ===")
    
    manager = ManagerAgent()
    worker = WorkerAgent()
    worker.set_task_completion_callback(manager.on_task_completed)
    
    # Test with a moderate complexity objective
    objective = "Create a simple calculator that can add, subtract, multiply, and divide two numbers"
    project_id = manager.create_project("Calculator_Test", objective)
    
    print(f"Created test project: {objective}")
    
    # Show the generated plan
    manager.show_project_plan_status(project_id)
    
    # Process a few tasks to test the system
    for i in range(8):  # Increased to test larger plans
        print(f"\n--- Processing Task {i+1} ---")
        
        task_result = worker.process_next_task()
        if not task_result:
            print("No more tasks.")
            break
            
        print(f"Task: {task_result['title']}")
        print(f"Success: {task_result['success']}")
        
        # Quick evaluation
        evaluation = manager.evaluate_progress(project_id)
        print(f"Progress: {evaluation.get('completion_percentage', 0):.1f}%")
        print(f"Phase: {evaluation.get('current_phase', 'unknown')}")
        
        if evaluation.get('status') == 'ready_for_validation':
            print("✅ Plan completed - ready for validation!")
            break

def run_planning_analysis():
    """Analyze how the planning system works with different objectives."""
    
    print("=== PLANNING SYSTEM ANALYSIS ===")
    
    test_objectives = [
        "Write a haiku about AI",
        "Create a simple todo list app", 
        "Build a JavaScript raycasting game engine",
        "Develop a data analysis dashboard with charts"
    ]
    
    from project_planner import ProjectPlanner
    planner = ProjectPlanner()
    
    print("Analyzing planning for different objective types:\n")
    
    for i, objective in enumerate(test_objectives, 1):
        print(f"{i}. {objective}")
        
        # Get complexity assessment
        complexity = planner._assess_objective_complexity(objective)
        print(f"   Complexity: {complexity.get('complexity_score', 0)}/10 ({complexity.get('complexity_level', 'unknown')})")
        
        # Get basic plan info
        try:
            plan = planner.create_project_plan(objective)
            estimated_tasks = plan['task_breakdown'].get('estimated_tasks', 0)
            domain = plan.get('project_summary', {}).get('primary_domain', 'unknown')
            languages = ', '.join(plan.get('project_summary', {}).get('programming_languages', []))
            
            print(f"   Tasks: {estimated_tasks}")
            print(f"   Domain: {domain}")
            print(f"   Languages: {languages}")
            
        except Exception as e:
            print(f"   Planning failed: {e}")
        
        print()

if __name__ == "__main__":
    print("🚀 AI Agent Framework v3.0 - Intelligent Planning System")
    print("="*60)
    print("1. Run with objective (default)")
    print("2. Run simple test")
    print("3. Run complexity demo")
    print("4. Run planning analysis")
    
    choice = input("Choose mode (1/2/3/4) or press Enter for mode 1: ").strip()
    
    if choice == "2":
        run_simple_test()
    elif choice == "3":
        run_complexity_demo()
    elif choice == "4":
        run_planning_analysis()
    else:
        main()