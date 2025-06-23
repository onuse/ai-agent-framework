#!/usr/bin/env python3
"""
AI Agent Framework - Main Entry Point with Self-Improvement Loop

This is a hierarchical multi-agent system where a Manager Agent breaks down
objectives into subtasks that Worker Agents execute serially. The system now
includes automatic self-improvement based on user perspective validation.
"""

import time
import sys
from manager_agent import ManagerAgent
from worker_agent import WorkerAgent

def main():
    """Main framework execution loop with self-improvement."""
    
    print("=== AI Agent Framework v2.0 ===")
    print("Hierarchical Multi-Agent System with Self-Improvement")
    print("Manager Agent + Worker Agents + Validation Loop")
    print("="*50)
    
    # Initialize agents
    manager = ManagerAgent()
    worker = WorkerAgent()
    
    # Get objective from user
    if len(sys.argv) > 1:
        objective = " ".join(sys.argv[1:])
    else:
        objective = input("Enter your objective: ").strip()
        
    if not objective:
        print("No objective provided. Exiting.")
        return
    
    print(f"\nObjective: {objective}")
    print("="*50)
    
    # Create project and generate initial tasks
    print("\n[MANAGER] Creating project and generating task breakdown...")
    project_id = manager.create_project("AI_Project", objective)
    
    # Show initial project summary
    summary = manager.get_project_summary(project_id)
    print(f"\nProject created: {summary['project_name']}")
    print(f"Initial tasks: {summary['task_counts'].get('pending', 0)}")
    
    # Main execution loop with self-improvement
    main_iteration = 0
    improvement_attempt = 0
    max_main_iterations = 25  # Increased to allow for improvement cycles
    max_improvement_attempts = 3
    
    while main_iteration < max_main_iterations:
        main_iteration += 1
        print(f"\n{'='*20} MAIN ITERATION {main_iteration} {'='*20}")
        
        # Phase 1: Execute pending tasks
        tasks_processed = execute_pending_tasks(worker, manager, project_id, main_iteration)
        
        if tasks_processed == 0:
            print("[MAIN] No pending tasks found")
            break
        
        # Phase 2: Evaluate progress
        print("\n[MANAGER] Evaluating progress...")
        evaluation = manager.evaluate_progress(project_id)
        
        print(f"[MANAGER] Status: {evaluation.get('status', 'unknown')}")
        print(f"[MANAGER] Completion: {evaluation.get('completion_percentage', 0)}%")
        
        # Phase 3: If ready for validation, perform user perspective check
        if evaluation.get('status') == 'ready_for_validation':
            print("\n🔍 PERFORMING USER PERSPECTIVE VALIDATION")
            print("="*50)
            
            validation_report = manager.perform_final_project_validation(project_id, objective)
            
            # Phase 4: Self-improvement loop
            if manager.should_continue_improvement(validation_report, improvement_attempt, max_improvement_attempts):
                improvement_attempt += 1
                print(f"\n🔧 STARTING IMPROVEMENT CYCLE {improvement_attempt}/{max_improvement_attempts}")
                print("="*50)
                
                # Generate improvement tasks
                improvement_task_ids = manager.generate_improvement_tasks_from_validation(
                    project_id, objective, validation_report
                )
                
                if improvement_task_ids:
                    print(f"[MANAGER] Generated {len(improvement_task_ids)} improvement tasks")
                    # Continue main loop to process improvement tasks
                    continue
                else:
                    print("[MANAGER] No improvement tasks generated - stopping")
                    break
            else:
                print("\n🎉 PROJECT COMPLETED WITH ACCEPTABLE USER SATISFACTION!")
                break
        
        # Small delay to prevent overwhelming the system
        time.sleep(1)
    
    # Final project summary
    print("\n" + "="*50)
    print("FINAL PROJECT SUMMARY")
    print("="*50)
    
    final_summary = manager.get_project_summary(project_id)
    print(f"Project: {final_summary['project_name']}")
    print(f"Objective: {final_summary['objective']}")
    print(f"Final Status: {final_summary['current_phase']}")
    print(f"Completed Tasks: {final_summary['completed_tasks']}")
    print(f"Task Breakdown: {final_summary['task_counts']}")
    print(f"Improvement Cycles: {improvement_attempt}")
    
    # Show organized project structure
    print(f"\n📁 PROJECT STRUCTURE:")
    worker.show_project_structure()
    
    if main_iteration >= max_main_iterations:
        print(f"\n⚠️  Reached maximum iterations ({max_main_iterations})")
        print("Project may need manual intervention to complete.")
    
    # Final recommendation
    print(f"\n💡 RECOMMENDATION:")
    print(f"Check the artifacts directory for your completed project.")
    print(f"Look for folders with clear entry points (index.html, main.py, etc.)")

def execute_pending_tasks(worker: WorkerAgent, manager: ManagerAgent, project_id: str, main_iteration: int) -> int:
    """Execute all pending tasks and return count of tasks processed."""
    
    tasks_processed = 0
    task_iteration = 0
    max_task_iterations = 10  # Safety limit per main iteration
    
    while task_iteration < max_task_iterations:
        task_iteration += 1
        
        print(f"\n[WORKER] Looking for next task... (Task {task_iteration})")
        task_result = worker.process_next_task()
        
        if not task_result:
            # No more tasks to process
            break
        
        tasks_processed += 1
        print(f"[WORKER] Processed: {task_result['title']}")
        print(f"[WORKER] Success: {task_result['success']}")
        
        # Quick progress check after each task
        evaluation = manager.evaluate_progress(project_id)
        print(f"[PROGRESS] {evaluation.get('completion_percentage', 0):.0f}% complete")
        
        # If we've completed initial development, break to allow validation
        if evaluation.get('status') == 'ready_for_validation':
            print("[PROGRESS] Ready for validation - stopping task execution")
            break
    
    if task_iteration >= max_task_iterations:
        print(f"[WORKER] Reached max task iterations ({max_task_iterations}) for this cycle")
    
    return tasks_processed

def run_simple_test():
    """Run a simple test with a calculator objective."""
    
    print("=== SIMPLE TEST: Calculator with Self-Improvement ===")
    
    manager = ManagerAgent()
    worker = WorkerAgent()
    
    # Create a simple calculator project
    objective = "Create a working calculator that can add, subtract, multiply, and divide two numbers with a clear way to run it"
    project_id = manager.create_project("Calculator_Test", objective)
    
    print(f"Created test project: {objective}")
    
    # Process initial tasks
    for i in range(5):
        print(f"\n--- Processing Task {i+1} ---")
        
        task_result = worker.process_next_task()
        if not task_result:
            print("No more tasks.")
            break
            
        print(f"Task: {task_result['title']}")
        print(f"Success: {task_result['success']}")
        
        # Quick evaluation
        evaluation = manager.evaluate_progress(project_id)
        print(f"Progress: {evaluation.get('completion_percentage', 0)}%")
        
        if evaluation.get('status') == 'ready_for_validation':
            print("Ready for validation!")
            
            # Test validation
            validation_report = manager.perform_final_project_validation(project_id, objective)
            
            # Test improvement if needed
            if manager.should_continue_improvement(validation_report, 0, 2):
                print("Generating improvement tasks...")
                improvement_tasks = manager.generate_improvement_tasks_from_validation(
                    project_id, objective, validation_report
                )
                print(f"Generated {len(improvement_tasks)} improvement tasks")
            
            break

def run_interactive_demo():
    """Interactive demo showing the self-improvement process."""
    
    print("=== INTERACTIVE SELF-IMPROVEMENT DEMO ===")
    print("This demo will show how the framework improves its own output")
    print()
    
    objectives = [
        "Create a simple tic-tac-toe game",
        "Write a short poem about artificial intelligence", 
        "Create a basic web page with JavaScript"
    ]
    
    print("Choose an objective to demonstrate self-improvement:")
    for i, obj in enumerate(objectives, 1):
        print(f"{i}. {obj}")
    
    choice = input("Enter choice (1-3): ").strip()
    
    try:
        objective = objectives[int(choice) - 1]
        print(f"\nDemonstrating self-improvement with: {objective}")
        print("="*60)
        
        # Run the main loop with the chosen objective
        original_argv = sys.argv
        sys.argv = [sys.argv[0], objective]
        main()
        sys.argv = original_argv
        
    except (ValueError, IndexError):
        print("Invalid choice, running with default objective")
        run_simple_test()

if __name__ == "__main__":
    print("AI Agent Framework v2.0 - Self-Improving AI Development System")
    print("="*60)
    print("1. Run with objective (default)")
    print("2. Run simple test")
    print("3. Run interactive demo")
    
    choice = input("Choose mode (1/2/3) or press Enter for mode 1: ").strip()
    
    if choice == "2":
        run_simple_test()
    elif choice == "3":
        run_interactive_demo()
    else:
        main()