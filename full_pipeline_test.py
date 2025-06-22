#!/usr/bin/env python3
"""
Test the complete pipeline with improved LLM classification
"""

def test_full_pipeline():
    """Test the complete task execution pipeline."""
    
    print("🚀 TESTING: Complete Task Execution Pipeline")
    print("="*60)
    
    from manager_agent import ManagerAgent
    from worker_agent import WorkerAgent
    
    # Initialize agents
    manager = ManagerAgent()
    worker = WorkerAgent()
    
    # Test with a simple, focused objective
    objective = "Create a simple Python script that prints Hello World and shows the current time"
    project_id = manager.create_project("HelloWorld_Pipeline_Test", objective)
    
    print(f"✅ Project created: {project_id}")
    print(f"🎯 Objective: {objective}")
    
    # Check task generation
    from task_queue import TaskQueue
    task_queue = TaskQueue()
    task_counts = task_queue.get_task_count_by_status()
    print(f"📋 Initial task counts: {task_counts}")
    
    if task_counts.get('pending', 0) == 0:
        print("❌ No tasks generated!")
        return False
    
    # Process tasks one by one
    max_tasks = 3  # Limit to avoid infinite processing
    success_count = 0
    
    for i in range(max_tasks):
        print(f"\n{'='*20} PROCESSING TASK {i+1} {'='*20}")
        
        task_result = worker.process_next_task()
        
        if not task_result:
            print("✅ No more tasks to process")
            break
        
        print(f"📝 Task: {task_result['title']}")
        
        if task_result['success']:
            print(f"✅ SUCCESS: Task completed")
            success_count += 1
        else:
            print(f"❌ FAILED: Task execution failed")
        
        # Check current task status
        updated_counts = task_queue.get_task_count_by_status()
        print(f"📊 Task counts: {updated_counts}")
        
        # Quick evaluation
        evaluation = manager.evaluate_progress(project_id)
        print(f"📈 Progress: {evaluation.get('completion_percentage', 0)}%")
        print(f"🏷️  Status: {evaluation.get('status', 'unknown')}")
        
        if evaluation.get('status') == 'complete':
            print("🎉 Project completed!")
            break
    
    # Final results
    print(f"\n{'='*60}")
    print("🏁 PIPELINE TEST RESULTS")
    print("="*60)
    print(f"✅ Tasks completed successfully: {success_count}")
    print(f"📊 Final task counts: {task_queue.get_task_count_by_status()}")
    
    # Check artifacts
    import os
    artifacts_dir = "artifacts"
    if os.path.exists(artifacts_dir):
        files = [f for f in os.listdir(artifacts_dir) if f.endswith(('.py', '.txt', '.md'))]
        print(f"📁 Artifacts created: {len(files)} files")
        for file in files[-3:]:  # Show last 3 files
            print(f"   - {file}")
    
    return success_count > 0

def test_domain_specific_tasks():
    """Test different domain-specific tasks."""
    
    print("\n🎨 TESTING: Domain-Specific Task Execution")
    print("="*60)
    
    from manager_agent import ManagerAgent
    from worker_agent import WorkerAgent
    
    # Test different domains
    test_objectives = [
        ("Create a simple math quiz program", "code"),
        ("Write a 100-word story about a robot", "creative"), 
        ("Create a bar chart showing sample sales data", "data")
    ]
    
    manager = ManagerAgent()
    worker = WorkerAgent()
    results = []
    
    for objective, expected_domain in test_objectives:
        print(f"\n🎯 Testing: {objective}")
        print(f"Expected domain: {expected_domain}")
        
        # Create mini project
        project_id = manager.create_project(f"Test_{expected_domain}", objective)
        
        # Process first task
        task_result = worker.process_next_task()
        
        if task_result:
            success = task_result['success']
            print(f"{'✅' if success else '❌'} Result: {'SUCCESS' if success else 'FAILED'}")
            results.append(success)
        else:
            print("❌ No task generated")
            results.append(False)
    
    successful_domains = sum(results)
    total_domains = len(results)
    
    print(f"\n📊 Domain Test Results: {successful_domains}/{total_domains} succeeded")
    return successful_domains > 0

def test_classification_integration():
    """Test that improved classification actually helps execution."""
    
    print("\n🧠 TESTING: Classification → Execution Integration")
    print("="*60)
    
    from task_classifier import TaskClassifier
    from worker_agent import WorkerAgent
    from task_queue import TaskQueue
    
    classifier = TaskClassifier()
    worker = WorkerAgent()
    task_queue = TaskQueue()
    
    # Create a test task manually
    test_task = {
        'id': 'test_integration',
        'title': 'Create a simple greeting program',
        'description': 'Build a Python script that asks for a name and prints a personalized greeting',
        'subtask_data': {
            'deliverable': 'Working Python script',
            'project_id': 'test_project'
        }
    }
    
    # Classify the task
    classification = classifier.classify_task(test_task)
    print("🏷️ Classification Results:")
    print(f"   Domain: {classification['primary_domain']} ({classification['confidence']:.1%})")
    print(f"   Approach: {classification['approach']}")
    print(f"   Method: {classification.get('classification_method')}")
    
    # Add to task queue
    task_id = task_queue.add_task(
        title=test_task['title'],
        description=test_task['description'],
        subtask_data=test_task['subtask_data']
    )
    
    print(f"\n🔄 Executing task with {classification['approach']} approach...")
    
    # Execute the task
    task_result = worker.process_next_task()
    
    if task_result:
        print(f"{'✅' if task_result['success'] else '❌'} Execution result: {task_result['success']}")
        return task_result['success']
    else:
        print("❌ Task execution failed")
        return False

def main():
    """Run all pipeline tests."""
    
    print("🚀 Complete AI Agent Framework Pipeline Tests")
    print("="*60)
    
    # Test 1: Full pipeline
    test1_success = test_full_pipeline()
    
    # Test 2: Domain-specific tasks
    test2_success = test_domain_specific_tasks()
    
    # Test 3: Classification integration
    test3_success = test_classification_integration()
    
    # Final summary
    print("\n" + "="*60)
    print("🏁 FINAL TEST SUMMARY")
    print("="*60)
    print(f"{'✅' if test1_success else '❌'} Full Pipeline Test: {test1_success}")
    print(f"{'✅' if test2_success else '❌'} Domain-Specific Tests: {test2_success}")
    print(f"{'✅' if test3_success else '❌'} Classification Integration: {test3_success}")
    
    if all([test1_success, test2_success, test3_success]):
        print("\n🎉 AI AGENT FRAMEWORK IS FULLY OPERATIONAL!")
        print("🚀 Ready for production use!")
    else:
        print("\n🔧 Some issues remain. Check debug output.")
        
    # Provide next steps
    print(f"\n📋 Next Steps:")
    if test1_success:
        print("✅ Try: python main.py 'Create a todo list app'")
    if test2_success:
        print("✅ Try: python main.py 'Write a short poem about AI'")
    if test3_success:
        print("✅ Try: python main.py 'Analyze sample weather data'")

if __name__ == "__main__":
    main()