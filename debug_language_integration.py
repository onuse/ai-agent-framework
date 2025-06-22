#!/usr/bin/env python3
"""
Debug the language detection integration
"""

def test_robust_solution_creator():
    """Test that RobustSolutionCreator uses language detection."""
    
    print("🔧 TESTING: RobustSolutionCreator Language Integration")
    print("="*60)
    
    from robust_solution_creator import RobustSolutionCreator
    from task_classifier import TaskClassifier
    
    creator = RobustSolutionCreator()
    classifier = TaskClassifier()
    
    # Test JavaScript Doom clone task
    doom_task = {
        'title': 'Create JavaScript Doom Clone',
        'description': 'Build a raycasting engine using JavaScript and HTML5 Canvas',
        'subtask_data': {
            'deliverable': 'Working JavaScript Doom clone'
        }
    }
    
    print(f"📝 Task: {doom_task['title']}")
    
    # Step 1: Domain classification
    domain_classification = classifier.classify_task(doom_task)
    print(f"🏷️ Domain: {domain_classification['primary_domain']} ({domain_classification['confidence']:.2f})")
    
    # Step 2: Solution generation (should trigger language detection)
    print(f"\n🔄 Generating solution...")
    solution_result = creator.create_solution(doom_task, domain_classification)
    
    print(f"{'✅' if solution_result['success'] else '❌'} Solution generated: {solution_result['success']}")
    
    if solution_result['success']:
        language = solution_result.get('language', 'unknown')
        approach = solution_result.get('approach_used', 'unknown')
        
        print(f"💻 Detected language: {language}")
        print(f"🔧 Approach used: {approach}")
        
        # Check if solution contains JavaScript
        solution = solution_result['solution']
        has_js_keywords = any(keyword in solution.lower() for keyword in [
            'function', 'const', 'let', 'var', 'canvas', 'getcontext', '=>'
        ])
        
        print(f"🔍 Contains JS keywords: {has_js_keywords}")
        
        # Show solution preview
        lines = solution.split('\n')[:10]
        print(f"\n📄 Solution preview:")
        for i, line in enumerate(lines, 1):
            print(f"   {i}: {line}")
        
        if len(solution.split('\n')) > 10:
            print("   ...")
        
        return language == 'javascript' and has_js_keywords
    else:
        print(f"❌ Error: {solution_result.get('error')}")
        return False

def test_manual_language_detection():
    """Test language detection in isolation."""
    
    print("\n🔍 TESTING: Manual Language Detection")
    print("="*60)
    
    from language_classifier import LanguageClassifier
    
    classifier = LanguageClassifier()
    
    doom_task = {
        'title': 'Create JavaScript Doom Clone',
        'description': 'Build a raycasting engine using JavaScript and HTML5 Canvas',
        'subtask_data': {
            'deliverable': 'Working JavaScript Doom clone'
        }
    }
    
    print(f"📝 Task: {doom_task['title']}")
    
    # Test language detection
    language_result = classifier.classify_language(doom_task)
    
    print(f"💻 Language: {language_result['language']}")
    print(f"🎯 Confidence: {language_result['confidence']:.2f}")
    print(f"💭 Reasoning: {language_result.get('reasoning', 'N/A')}")
    print(f"🔍 Method: {language_result.get('classification_method', 'N/A')}")
    
    if language_result.get('key_indicators'):
        print(f"🏷️ Key indicators: {', '.join(language_result['key_indicators'])}")
    
    return language_result['language'] == 'javascript' and language_result['confidence'] > 0.7

def main():
    """Run language integration tests."""
    
    print("🔤 Language Detection Integration Tests")
    print("="*60)
    
    # Test 1: Manual language detection
    test1_success = test_manual_language_detection()
    
    # Test 2: RobustSolutionCreator integration
    test2_success = test_robust_solution_creator()
    
    # Summary
    print("\n" + "="*60)
    print("🏁 LANGUAGE INTEGRATION SUMMARY")
    print("="*60)
    print(f"{'✅' if test1_success else '❌'} Manual Language Detection: {test1_success}")
    print(f"{'✅' if test2_success else '❌'} RobustSolutionCreator Integration: {test2_success}")
    
    if test1_success and test2_success:
        print("\n🎉 LANGUAGE DETECTION IS WORKING!")
        print("🎮 Ready to generate JavaScript Doom clone!")
    elif test1_success:
        print("\n🔧 Language detection works, but integration needs fixing")
        print("The RobustSolutionCreator might not be using the detected language")
    else:
        print("\n❌ Language detection is still broken")
        print("The LLM classifier might not be working properly")

if __name__ == "__main__":
    main()