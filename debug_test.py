#!/usr/bin/env python3
"""
Debug Test Script - Quick validation of the AI Agent Framework
"""

import sys
import os
from manager_agent import ManagerAgent
from worker_agent import WorkerAgent

def test_simple_task():
    """Test with a very simple task to isolate the issue."""
    
    print("🧪 TESTING: Simple Hello World Task")
    print("="*50)
    
    # Initialize agents
    manager = ManagerAgent()
    worker = WorkerAgent()
    
    # Create a simple project
    objective = "Create a simple Python script that prints 'Hello, World!'"
    project_id = manager.create_project("HelloWorld_Test", objective)
    
    print(f"✅ Project created: {project_id}")
    
    # Check if tasks were generated
    from task_queue import TaskQueue
    task_queue = TaskQueue()
    task_counts = task_queue.get_task_count_by_status()
    print(f"📋 Task counts: {task_counts}")
    
    if task_counts.get('pending', 0) == 0:
        print("❌ No tasks generated!")
        return False
    
    # Process one task
    print("\n🔄 Processing first task...")
    task_result = worker.process_next_task()
    
    if task_result:
        print(f"📝 Task: {task_result['title']}")
        print(f"{'✅' if task_result['success'] else '❌'} Success: {task_result['success']}")
        
        # Check if artifact was created
        artifacts_dir = "artifacts"
        if os.path.exists(artifacts_dir):
            files = [f for f in os.listdir(artifacts_dir) if f.endswith('.py')]
            print(f"📁 Artifacts created: {len(files)} files")
            for file in files:
                print(f"   - {file}")
        else:
            print("📁 No artifacts directory found")
        
        return task_result['success']
    else:
        print("❌ No task to process")
        return False

def test_task_classification():
    """Test the task classification system."""
    
    print("\n🧪 TESTING: Task Classification")
    print("="*50)
    
    from task_classifier import TaskClassifier
    
    classifier = TaskClassifier()
    
    test_tasks = [
        {
            'title': 'Create a calculator',
            'description': 'Build a simple calculator in Python',
            'subtask_data': {'deliverable': 'Working calculator'}
        },
        {
            'title': 'Write a story',
            'description': 'Create a short science fiction story',
            'subtask_data': {'deliverable': 'Creative story'}
        },
        {
            'title': 'Analyze data',
            'description': 'Process CSV data and create charts',
            'subtask_data': {'deliverable': 'Data analysis'}
        }
    ]
    
    for task in test_tasks:
        classification = classifier.classify_task(task)
        print(f"📝 Task: {task['title']}")
        print(f"🏷️  Domain: {classification['primary_domain']} (confidence: {classification['confidence']:.2f})")
        print(f"🔄 Approach: {classification['approach']}")
        print()
    
    return True

def test_solution_generation():
    """Test solution generation directly."""
    
    print("\n🧪 TESTING: Solution Generation")
    print("="*50)
    
    from robust_solution_creator import RobustSolutionCreator
    from task_classifier import TaskClassifier
    
    creator = RobustSolutionCreator()
    classifier = TaskClassifier()
    
    task = {
        'title': 'Create Hello World',
        'description': 'Create a simple Python script that prints Hello World',
        'subtask_data': {'deliverable': 'Working Python script'}
    }
    
    print(f"📝 Task: {task['title']}")
    
    # Classify
    classification = classifier.classify_task(task)
    print(f"🏷️  Classification: {classification['primary_domain']} ({classification['confidence']:.2f})")
    
    # Generate solution
    solution_result = creator.create_solution(task, classification)
    print(f"{'✅' if solution_result['success'] else '❌'} Solution generated: {solution_result['success']}")
    
    if solution_result['success']:
        solution = solution_result['solution']
        print(f"📏 Solution length: {len(solution)} characters")
        print(f"🔍 Contains 'print': {'print' in solution}")
        print(f"🔍 Contains 'Hello': {'Hello' in solution}")
        
        # Show first few lines
        lines = solution.split('\n')[:5]
        print("📄 First 5 lines:")
        for i, line in enumerate(lines, 1):
            print(f"   {i}: {line}")
    else:
        print(f"❌ Error: {solution_result.get('error')}")
    
    return solution_result['success']

def main():
    """Run all tests."""
    
    print("🚀 AI Agent Framework Debug Tests")
    print("="*50)
    
    # Test 1: Task Classification
    print("Test 1: Task Classification")
    test1_success = test_task_classification()
    
    # Test 2: Solution Generation
    print("\nTest 2: Solution Generation")
    test2_success = test_solution_generation()
    
    # Test 3: Full Task Execution
    print("\nTest 3: Full Task Execution")
    test3_success = test_simple_task()
    
    # Summary
    print("\n" + "="*50)
    print("🏁 TEST SUMMARY")
    print("="*50)
    print(f"{'✅' if test1_success else '❌'} Task Classification: {test1_success}")
    print(f"{'✅' if test2_success else '❌'} Solution Generation: {test2_success}")
    print(f"{'✅' if test3_success else '❌'} Full Task Execution: {test3_success}")
    
    if all([test1_success, test2_success, test3_success]):
        print("\n🎉 ALL TESTS PASSED! Framework is working correctly.")
    else:
        print("\n🔧 Some tests failed. Check the debug output above.")

if __name__ == "__main__":
    main()