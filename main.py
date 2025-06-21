#!/usr/bin/env python3
"""
AI Agent Framework - Main Entry Point

This is a hierarchical multi-agent system where a Manager Agent breaks down
objectives into subtasks that Worker Agents execute serially.
"""

import time
import sys
from manager_agent import ManagerAgent
from worker_agent import WorkerAgent

def main():
    """Main framework execution loop."""
    
    print("=== AI Agent Framework ===")
    print("Hierarchical Multi-Agent System")
    print("Manager Agent + Worker Agents")
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
    
    # Main execution loop
    iteration = 0
    max_iterations = 20  # Safety limit
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'='*20} ITERATION {iteration} {'='*20}")
        
        # Worker processes next task
        print("\n[WORKER] Looking for next task...")
        task_result = worker.process_next_task()
        
        if not task_result:
            print("[WORKER] No pending tasks found.")
            break
        
        print(f"[WORKER] Processed: {task_result['title']}")
        print(f"[WORKER] Success: {task_result['success']}")
        
        # Manager evaluates progress
        print("\n[MANAGER] Evaluating progress...")
        evaluation = manager.evaluate_progress(project_id)
        
        print(f"[MANAGER] Status: {evaluation.get('status', 'unknown')}")
        print(f"[MANAGER] Completion: {evaluation.get('completion_percentage', 0)}%")
        
        if evaluation.get('assessment'):
            print(f"[MANAGER] Assessment: {evaluation['assessment']}")
        
        # Check if project is complete
        if evaluation.get('status') == 'complete':
            print("\n🎉 PROJECT COMPLETED!")
            break
        
        # Generate additional tasks if needed
        if evaluation.get('needs_additional_tasks'):
            print("[MANAGER] Generating additional tasks...")
            manager.generate_additional_tasks(project_id, evaluation)
        
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
    
    # Show artifacts created
    import os
    artifacts_dir = "artifacts"
    if os.path.exists(artifacts_dir):
        artifacts = [f for f in os.listdir(artifacts_dir) if f.endswith('.py')]
        if artifacts:
            print(f"\nArtifacts created ({len(artifacts)}):")
            for artifact in artifacts:
                print(f"  - {artifact}")
            print(f"\nCheck the '{artifacts_dir}' directory for generated code.")
        else:
            print("\nNo artifacts were created.")
    
    if iteration >= max_iterations:
        print(f"\n⚠️  Reached maximum iterations ({max_iterations})")
        print("Project may need manual intervention to complete.")

def run_simple_test():
    """Run a simple test with a calculator objective."""
    
    print("=== SIMPLE TEST: Calculator ===")
    
    manager = ManagerAgent()
    worker = WorkerAgent()
    
    # Create a simple calculator project
    objective = "Create a basic calculator that can add, subtract, multiply, and divide two numbers"
    project_id = manager.create_project("Calculator_Test", objective)
    
    print(f"Created test project: {objective}")
    
    # Process a few tasks
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
        
        if evaluation.get('status') == 'complete':
            print("Test completed!")
            break

if __name__ == "__main__":
    print("AI Agent Framework")
    print("1. Run with objective")
    print("2. Run simple test")
    
    choice = input("Choose (1/2) or press Enter for option 1: ").strip()
    
    if choice == "2":
        run_simple_test()
    else:
        main()