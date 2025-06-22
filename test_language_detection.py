#!/usr/bin/env python3
"""
Test language detection for the Doom clone objective
"""

def test_doom_language_detection():
    """Test language detection for Doom clone."""
    
    print("🔍 TESTING: Language Detection for Doom Clone")
    print("="*60)
    
    from language_classifier import LanguageClassifier
    
    classifier = LanguageClassifier()
    
    # Test the exact task
    doom_task = {
        'title': 'Create a JavaScript doom clone with raycasting engine, player movement, and basic enemies',
        'description': 'Build a JavaScript doom clone with raycasting engine, player movement, and basic enemies',
        'subtask_data': {
            'deliverable': 'Working JavaScript Doom clone'
        }
    }
    
    print(f"📝 Task: {doom_task['title']}")
    print()
    
    # Test language classification
    language_result = classifier.classify_language(doom_task)
    
    print("🏷️ Language Classification Results:")
    print(f"   Language: {language_result['language']}")
    print(f"   Confidence: {language_result['confidence']:.2f}")
    print(f"   Is Programming Task: {language_result['is_programming_task']}")
    print(f"   Reason: {language_result.get('reason', 'N/A')}")
    print()
    
    # Show all scores
    if 'all_scores' in language_result:
        print("📊 All Language Scores:")
        scores = language_result['all_scores']
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for lang, score in sorted_scores:
            print(f"   {lang}: {score:.3f}")
    print()
    
    # Expected: Should detect JavaScript
    expected_language = 'javascript'
    actual_language = language_result['language']
    
    success = actual_language == expected_language
    print(f"🎯 Expected: {expected_language}")
    print(f"🎯 Actual: {actual_language}")
    print(f"{'✅' if success else '❌'} Detection: {'SUCCESS' if success else 'FAILED'}")
    
    return success

def test_various_js_phrases():
    """Test detection with various JavaScript-related phrases."""
    
    print("\n🧪 TESTING: Various JavaScript Phrases")
    print("="*60)
    
    from language_classifier import LanguageClassifier
    
    classifier = LanguageClassifier()
    
    test_phrases = [
        "Create a JavaScript game",
        "Build a JS web application", 
        "Make a Node.js server",
        "Develop a React component",
        "Build a web app with HTML and JavaScript",
        "Create browser-based game in JavaScript"
    ]
    
    js_detected = 0
    
    for phrase in test_phrases:
        task = {
            'title': phrase,
            'description': f'Please {phrase.lower()}',
            'subtask_data': {'deliverable': 'Working application'}
        }
        
        result = classifier.classify_language(task)
        detected_js = result['language'] == 'javascript'
        
        if detected_js:
            js_detected += 1
        
        print(f"{'✅' if detected_js else '❌'} '{phrase}'")
        print(f"    → {result['language']} ({result['confidence']:.2f})")
    
    accuracy = js_detected / len(test_phrases)
    print(f"\n📊 JavaScript Detection Rate: {accuracy:.1%} ({js_detected}/{len(test_phrases)})")
    
    return accuracy > 0.5

def fix_language_detection():
    """Show how to fix the language detection."""
    
    print("\n🔧 LANGUAGE DETECTION FIX")
    print("="*60)
    
    print("The issue is likely in the language classifier patterns.")
    print("The word 'JavaScript' should trigger JavaScript detection.")
    print()
    print("Quick fix options:")
    print("1. Modify the objective to be more explicit:")
    print("   'Create a web-based doom clone using JavaScript and HTML5 Canvas'")
    print()
    print("2. Or create a manual task with explicit language:")
    print("   - Title: 'Build JavaScript Doom Clone'")
    print("   - Description: 'Use JavaScript, HTML5 Canvas, and raycasting'")
    print()
    print("3. Check language_classifier.py patterns for 'javascript' domain")

def main():
    """Run language detection tests."""
    
    print("🚀 Language Detection Debug for Doom Clone")
    print("="*60)
    
    # Test 1: Doom clone detection
    test1_success = test_doom_language_detection()
    
    # Test 2: Various JS phrases
    test2_success = test_various_js_phrases()
    
    # Show fix suggestions
    fix_language_detection()
    
    # Summary
    print("\n" + "="*60)
    print("🏁 LANGUAGE DETECTION SUMMARY")
    print("="*60)
    print(f"{'✅' if test1_success else '❌'} Doom Clone Detection: {test1_success}")
    print(f"{'✅' if test2_success else '❌'} General JS Detection: {test2_success}")
    
    if not test1_success:
        print("\n🔧 RECOMMENDED FIXES:")
        print("1. Use more explicit objective:")
        print("   'Create a web-based doom clone using JavaScript and HTML5 Canvas'")
        print()
        print("2. Or modify language_classifier.py to better detect JavaScript")

if __name__ == "__main__":
    main()