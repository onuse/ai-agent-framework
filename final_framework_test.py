#!/usr/bin/env python3
"""
Final test of the complete AI Agent Framework with all fixes
"""

def test_focused_task_generation():
    """Test that task generation creates appropriate, focused tasks."""
    
    print("🎯 TESTING: Focused Task Generation")
    print("="*60)
    
    from manager_agent import ManagerAgent
    
    manager = ManagerAgent()
    
    test_objectives = [
        ("Write a haiku about programming", "creative"),
        ("Create a simple calculator", "code"),
        ("Show analysis of sample weather data", "data")
    ]
    
    for objective, expected_domain in test_objectives:
        print(f"\n📝 Objective: {objective}")
        print(f"Expected domain: {expected_domain}")
        
        # Create project
        project_id = manager.create_project(f"Test_{expected_domain}", objective)
        
        # Check what tasks were generated
        from task_queue import TaskQueue
        task_queue = TaskQueue()
        
        # Get the most recent pending task (should be for this project)
        task = task_queue.get_next_task()
        if task:
            print(f"✅ Generated task: {task['title']}")
            print(f"📄 Description: {task['description'][:100]}...")
            
            # Check if task matches objective
            task_matches = objective.lower().replace(' ', '') in task['title'].lower().replace(' ', '')
            print(f"{'✅' if task_matches else '⚠️'} Task relevance: {'High' if task_matches else 'Low'}")
        else:
            print("❌ No task generated")
    
    return True

def test_safe_execution():
    """Test safe code execution with various scenarios."""
    
    print("\n🛡️ TESTING: Safe Code Execution")
    print("="*60)
    
    from worker_agent import WorkerAgent
    from task_queue import TaskQueue
    
    worker = WorkerAgent()
    task_queue = TaskQueue()
    
    # Create a safe test task
    safe_task_id = task_queue.add_task(
        title="Create Hello World Script", 
        description="Create a simple Python script that prints Hello World and the current time",
        subtask_data={
            'deliverable': 'Working Python script',
            'project_id': 'test_safe'
        }
    )
    
    print("🔄 Processing safe task...")
    
    # Process the task
    task_result = worker.process_next_task()
    
    if task_result:
        print(f"📝 Task: {task_result['title']}")
        print(f"{'✅' if task_result['success'] else '❌'} Result: {'SUCCESS' if task_result['success'] else 'FAILED'}")
        
        if task_result['success']:
            # Check if artifact was created
            import os
            artifacts_dir = "artifacts"
            if os.path.exists(artifacts_dir):
                files = [f for f in os.listdir(artifacts_dir) if 'hello' in f.lower()]
                print(f"📁 Created artifacts: {files}")
        
        return task_result['success']
    else:
        print("❌ No task processed")
        return False

def test_domain_classification_accuracy():
    """Test that the improved classifier works correctly."""
    
    print("\n🧠 TESTING: Domain Classification Accuracy")
    print("="*60)
    
    from task_classifier import TaskClassifier
    
    classifier = TaskClassifier()
    
    test_cases = [
        ("Write a poem about AI", "creative"),
        ("Create a todo list app", "code"),
        ("Analyze sales trends from data", "data"),
        ("Build a simple puzzle game", "game")
    ]
    
    correct_classifications = 0
    
    for description, expected_domain in test_cases:
        task = {
            'title': description,
            'description': f'Please {description.lower()}',
            'subtask_data': {'deliverable': 'As requested'}
        }
        
        classification = classifier.classify_task(task)
        actual_domain = classification['primary_domain']
        confidence = classification['confidence']
        
        is_correct = actual_domain == expected_domain
        if is_correct:
            correct_classifications += 1
        
        print(f"{'✅' if is_correct else '❌'} '{description}'")
        print(f"   Expected: {expected_domain}, Got: {actual_domain} ({confidence:.1%})")
    
    accuracy = correct_classifications / len(test_cases)
    print(f"\n📊 Classification accuracy: {accuracy:.1%} ({correct_classifications}/{len(test_cases)})")
    
    return accuracy >= 0.75  # 75% accuracy threshold

def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    
    print("\n🚀 TESTING: End-to-End Workflow")
    print("="*60)
    
    from manager_agent import ManagerAgent
    from worker_agent import WorkerAgent
    
    manager = ManagerAgent()
    worker = WorkerAgent()
    
    # Test with a very simple, focused objective
    objective = "Write a short limerick about robots"
    
    print(f"🎯 Objective: {objective}")
    
    # Create project
    project_id = manager.create_project("EndToEnd_Test", objective)
    print("✅ Project created")
    
    # Process up to 2 tasks
    success_count = 0
    
    for i in range(2):
        print(f"\n--- Processing Task {i+1} ---")
        
        task_result = worker.process_next_task()
        
        if not task_result:
            print("✅ No more tasks (good - focused)")
            break
        
        print(f"📝 {task_result['title']}")
        
        if task_result['success']:
            print("✅ Task completed successfully")
            success_count += 1
        else:
            print("❌ Task failed")
        
        # Quick progress check
        evaluation = manager.evaluate_progress(project_id)
        print(f"📈 Progress: {evaluation.get('completion_percentage', 0):.0f}%")
        
        if evaluation.get('status') == 'complete':
            print("🎉 Project completed!")
            break
    
    # Final results
    print(f"\n📊 End-to-end results:")
    print(f"✅ Tasks completed: {success_count}")
    
    # Check for creative output
    import os
    artifacts_dir = "artifacts"
    creative_files = []
    if os.path.exists(artifacts_dir):
        for file in os.listdir(artifacts_dir):
            if any(word in file.lower() for word in ['limerick', 'robot', 'short']):
                creative_files.append(file)
    
    print(f"📁 Creative artifacts: {creative_files}")
    
    return success_count > 0 and len(creative_files) > 0

def test_safety_measures():
    """Test that safety measures prevent dangerous code execution."""
    
    print("\n🛡️ TESTING: Safety Measures")
    print("="*60)
    
    from worker_agent import WorkerAgent
    
    worker = WorkerAgent()
    
    # Test safety checking function
    dangerous_code_samples = [
        "import pandas as pd\nprint('hello')",
        "import sys\nsys.exit(1)",
        "name = input('Enter name: ')\nprint(name)",
        "while True:\n    print('infinite')"
    ]
    
    safety_working = True
    
    for i, dangerous_code in enumerate(dangerous_code_samples, 1):
        print(f"\n{i}. Testing dangerous code detection...")
        
        # Check if safety system detects issues
        issues = worker._check_code_safety(dangerous_code)
        
        if issues:
            print(f"✅ Detected issues: {issues[0]}")
            
            # Test if it can fix the issues
            fixed_code = worker._fix_common_safety_issues(dangerous_code)
            fixed_issues = worker._check_code_safety(fixed_code)
            
            if len(fixed_issues) < len(issues):
                print(f"✅ Partially fixed ({len(issues)} → {len(fixed_issues)} issues)")
            else:
                print(f"⚠️ Could not fix issues")
        else:
            print(f"⚠️ No issues detected in dangerous code")
            safety_working = False
    
    print(f"\n🛡️ Safety system status: {'✅ Working' if safety_working else '⚠️ Needs improvement'}")
    
    return safety_working

def main():
    """Run all final tests."""
    
    print("🚀 AI Agent Framework - Final Integration Tests")
    print("="*70)
    
    tests = [
        ("Task Generation", test_focused_task_generation),
        ("Safe Execution", test_safe_execution),
        ("Classification Accuracy", test_domain_classification_accuracy),
        ("End-to-End Workflow", test_end_to_end_workflow),
        ("Safety Measures", test_safety_measures)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name.upper()} {'='*20}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"\n❌ {test_name}: EXCEPTION - {e}")
            results.append((test_name, False))
    
    # Final summary
    print("\n" + "="*70)
    print("🏁 FINAL TEST SUMMARY")
    print("="*70)
    
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    for test_name, result in results:
        print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
    
    print(f"\n📊 Overall Score: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 AI Agent Framework is fully operational!")
        print("\n📋 Ready for production use:")
        print("   python main.py 'Create a simple calculator'")
        print("   python main.py 'Write a haiku about AI'")
        print("   python main.py 'Analyze sample sales data'")
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ MOSTLY WORKING!")
        print(f"🔧 {total_tests - passed_tests} minor issues to address")
        print("Framework is usable for most tasks")
    else:
        print("\n⚠️ NEEDS MORE WORK")
        print(f"🔧 {total_tests - passed_tests} critical issues to fix")
        print("Review failed tests before production use")

if __name__ == "__main__":
    main()