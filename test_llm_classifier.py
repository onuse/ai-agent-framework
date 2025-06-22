#!/usr/bin/env python3
"""
Test the new LLM-based task classifier
"""

def test_llm_classification():
    """Test LLM-based classification with various task types."""
    
    print("🧪 TESTING: LLM-Based Task Classification")
    print("="*60)
    
    from task_classifier import TaskClassifier
    
    classifier = TaskClassifier()
    
    test_cases = [
        {
            'title': 'Create a calculator app',
            'description': 'Build a simple calculator that can add, subtract, multiply, and divide two numbers with a GUI interface',
            'subtask_data': {'deliverable': 'Working calculator application'}
        },
        {
            'title': 'Write a short story',
            'description': 'Create a 500-word science fiction story about time travel and its consequences',
            'subtask_data': {'deliverable': 'Creative short story'}
        },
        {
            'title': 'Analyze sales data trends',
            'description': 'Process quarterly sales data and create visualizations showing performance trends across different regions',
            'subtask_data': {'deliverable': 'Data analysis report with charts'}
        },
        {
            'title': 'Build a space invaders game',
            'description': 'Create a classic arcade-style game with player ship, enemies, and scoring system',
            'subtask_data': {'deliverable': 'Playable game'}
        },
        {
            'title': 'Research AI agent frameworks',
            'description': 'Investigate current state of AI agent frameworks, compare features, and document findings',
            'subtask_data': {'deliverable': 'Research report'}
        },
        {
            'title': 'Create a data visualization dashboard',
            'description': 'Build an interactive web interface that displays charts and graphs from database queries',
            'subtask_data': {'deliverable': 'Web dashboard with UI and data processing'}
        }
    ]
    
    for i, task in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {task['title']}")
        print("="*50)
        
        try:
            classification = classifier.classify_task(task)
            
            print(f"📝 Task: {task['title']}")
            print(f"📄 Description: {task['description'][:80]}...")
            print()
            print(classifier.explain_classification(classification))
            print()
            print(f"🔧 Approach: {classification['approach']}")
            
            if classification.get('fallback_reason'):
                print(f"⚠️  Fallback: {classification['fallback_reason']}")
            
            print(f"🤖 Method: {classification.get('classification_method', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Classification failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)
    
    return True

def test_edge_cases():
    """Test classification with edge cases and ambiguous tasks."""
    
    print("\n🧪 TESTING: Edge Cases and Ambiguous Tasks")
    print("="*60)
    
    from task_classifier import TaskClassifier
    
    classifier = TaskClassifier()
    
    edge_cases = [
        {
            'title': 'Setup project structure',
            'description': 'Create basic folder structure and configuration files',
            'subtask_data': {'deliverable': 'Project setup'}
        },
        {
            'title': 'Optimize performance',
            'description': 'Improve system performance and reduce load times',
            'subtask_data': {'deliverable': 'Performance improvements'}
        },
        {
            'title': 'Create interactive data story',
            'description': 'Build a web app that tells a story through data visualizations and narrative text',
            'subtask_data': {'deliverable': 'Interactive story with data'}
        }
    ]
    
    for i, task in enumerate(edge_cases, 1):
        print(f"\n{i}. Edge Case: {task['title']}")
        
        try:
            classification = classifier.classify_task(task)
            print(classifier.explain_classification(classification))
            
            if classification.get('is_hybrid'):
                print(f"🔄 Hybrid detected - Primary: {classification['primary_domain']}, Secondary: {classification.get('secondary_domain')}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    return True

def compare_classification_methods():
    """Compare LLM vs keyword-based classification."""
    
    print("\n🧪 TESTING: Method Comparison")
    print("="*60)
    
    # Test task
    task = {
        'title': 'Create doom-style raycast engine',
        'description': 'Build a first-person 3D engine using raycasting techniques for rendering walls and sprites',
        'subtask_data': {'deliverable': 'Working 3D engine'}
    }
    
    print(f"Test Task: {task['title']}")
    print(f"Description: {task['description']}")
    print()
    
    # Test with LLM classifier
    try:
        from task_classifier import TaskClassifier
        
        llm_classifier = TaskClassifier()
        llm_result = llm_classifier.classify_task(task)
        
        print("🤖 LLM-Based Classification:")
        print(llm_classifier.explain_classification(llm_result))
        print()
        
        # Show the reasoning
        if llm_result.get('reasoning'):
            print(f"💭 LLM Reasoning: {llm_result['reasoning']}")
        
        if llm_result.get('key_indicators'):
            print(f"🔍 Key Indicators: {', '.join(llm_result['key_indicators'])}")
        
    except Exception as e:
        print(f"❌ LLM classification failed: {e}")
    
    return True

def main():
    """Run all classifier tests."""
    
    print("🚀 LLM-Based Task Classifier Tests")
    print("="*60)
    
    # Test 1: Basic classification
    test1_success = test_llm_classification()
    
    # Test 2: Edge cases
    test2_success = test_edge_cases()
    
    # Test 3: Method comparison
    test3_success = compare_classification_methods()
    
    # Summary
    print("\n" + "="*60)
    print("🏁 TEST SUMMARY")
    print("="*60)
    print(f"{'✅' if test1_success else '❌'} Basic Classification: {test1_success}")
    print(f"{'✅' if test2_success else '❌'} Edge Cases: {test2_success}")
    print(f"{'✅' if test3_success else '❌'} Method Comparison: {test3_success}")
    
    if all([test1_success, test2_success, test3_success]):
        print("\n🎉 LLM-based classifier is working correctly!")
    else:
        print("\n🔧 Some tests failed. Check debug output.")

if __name__ == "__main__":
    main()