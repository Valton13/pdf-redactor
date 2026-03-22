import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from presidio_analyzer import AnalyzerEngine
from python.recognizers.account_recognizer import account_recognizer, international_account_recognizer
from python.recognizers.policy_recognizer import policy_recognizer, medical_record_recognizer

def test_bank_acc_recg():
    print("\n" + "="*60)
    print("TEST 1: BANK_ACCOUNT Recognizer")
    print("="*60)
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(account_recognizer)
    analyzer.registry.add_recognizer(international_account_recognizer)
    test_cases = [
        ("Account: 1234-5678-9012-3456", True, "Standard hyphenated format"),
        ("1234 5678 9012 3456", True, "Space-separated format"),
        ("1234567890123456", True, "Plain 16-digit format"),
        ("Routing: 123456789, Account: 9876-5432-1098-7654", True, "With routing number"),
        ("IBAN: DE89370400440532013000", True, "IBAN format"),
        ("UK Account: 12-34-56 12345678", True, "UK sort code format"),
        ("support@bank.com", False, "Email (should not match)"),
        ("Account balance is $5000", False, "No account number"),
    ]
    results =[]
    for text, should_match, description in test_cases:
        entities = analyzer.analyze(text=text, language="en")
        matched = len(entities) > 0
        
        status = "PASS" if matched == should_match else " FAIL"
        print(f"{status} {description}")
        print(f"Text: '{text}'")
        print(f"Expected: {'match' if should_match else 'no match'}")
        print(f"Detected: {'match' if matched else 'no match'}")        
        if matched:
            for entity in entities:
                entity_text = text[entity.start:entity.end]
                print(f"{entity.entity_type}: '{entity_text}' ({entity.score:.2f})")       
        results.append(matched == should_match)
        print()   
    return all(results)

def test_policy_no_recg():
    print("\n" + "="*60)
    print("TEST 2: POLICY_NUMBER Recognizer")
    print("="*60)  
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(policy_recognizer)
    analyzer.registry.add_recognizer(medical_record_recognizer) 
    test_cases = [
        ("Policy: POL-1234567", True, "POL- prefix format"),
        ("POL 1234567", True, "POL with space"),
        ("Claim number CLM-12345678", True, "Claim number format"),
        ("ABC1234567", True, "Alpha-numeric format"),
        ("Policy Number: XYZ9876543", True, "With label"),
        ("Medical Record: MRN-77889900", True, "Medical record number"),
        ("Health Insurance: CA-1234567-8", True, "Health insurance format"),
        ("Contact insurance provider", False, "No policy number"),
        ("Premium due next month", False, "No policy number"),
    ]   
    results = []
    for text, should_match, description in test_cases:
        entities = analyzer.analyze(text=text, language="en")
        matched = len(entities) > 0
        
        status = "PASS" if matched == should_match else "FAIL"
        print(f"{status} {description}")
        print(f"Text: '{text}'")
        print(f"Expected: {'match' if should_match else 'no match'}")
        print(f"Detected: {'match' if matched else 'no match'}")       
        if matched:
            for entity in entities:
                entity_text = text[entity.start:entity.end]
                print(f"{entity.entity_type}: '{entity_text}' ({entity.score:.2f})")
                results.append(matched == should_match)
        print()  
    return all(results)

def text_context_enhancement():
    print("\n" + "="*60)
    print("TEST 3: Context Enhancement")
    print("="*60)
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(account_recognizer)
    text_with_context = "Your bank account 1234-5678-9012-3456 has been verified"
    text_without_context = "Reference number 1234-5678-9012-3456 processed"   
    results_with = analyzer.analyze(text=text_with_context, language="en")
    results_without = analyzer.analyze(text=text_without_context, language="en")
    print(f"Text with context: '{text_with_context}'")
    print(f"Entities detected: {len(results_with)}")
    if results_with:
        for e in results_with:
            print(f"{e.entity_type} (confidence: {e.score:.2f})")
    print(f"\nText without context: '{text_without_context}'")
    print(f"  Entities detected: {len(results_without)}")
    if results_without:
        for e in results_without:
            print(f"{e.entity_type} (confidence: {e.score:.2f})")
    detected_both = len(results_with)  >0 and len(results_without) >0
    if detected_both:
        print("\nPASS")
        return True
    else:
        print("\nFAIL")
        return False        
    
def test_confidence_scores():
    print("\n" + "="*60)
    print("TEST 4: Confidence Score Validation")
    print("="*60)
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(account_recognizer)
    analyzer.registry.add_recognizer(policy_recognizer)
    test_cases = [
        ("Account: 1234-5678-9012-3456", "BANK_ACCOUNT", 0.85),
        ("POL-1234567", "POLICY_NUMBER", 0.80),
    ]
    results = []
    for text, expected_type, min_confidence in test_cases:
        entities = analyzer.analyze(text=text, language="en")       
        if entities:
            entity = entities[0]
            entity_text = text[entity.start:entity.end]
            confidence = entity.score           
            meets_threshold = confidence >= min_confidence           
            status = "PASS" if meets_threshold else " FAIL"
            print(f"{status} '{text}'")
            print(f"Type: {entity.entity_type}, Confidence: {confidence:.2f}")
            print(f"Expected min confidence: {min_confidence}")            
            results.append(meets_threshold)
        else:
            print(f" FAIL '{text}'")
            results.append(False)
        print() 
    return all(results)

#copies
def main():
    """Run all custom recognizer tests"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 3 DAY 2: CUSTOM RECOGNIZERS TEST (PART 1)         ║")
    print("║  BANK_ACCOUNT + POLICY_NUMBER Patterns                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    results = []
    
    # Run tests
    results.append(("BANK_ACCOUNT Recognizer", test_bank_acc_recg()))
    results.append(("POLICY_NUMBER Recognizer", test_policy_no_recg()))
    results.append(("Context Enhancement", text_context_enhancement()))
    results.append(("Confidence Scores", test_confidence_scores()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! Custom recognizers working correctly")
        print("\n✅ BANK_ACCOUNT patterns:")
        print("   • 1234-5678-9012-3456 (hyphenated)")
        print("   • 1234 5678 9012 3456 (space-separated)")
        print("   • 1234567890123456 (plain)")
        print("   • IBAN, UK sort code formats")
        
        print("\n✅ POLICY_NUMBER patterns:")
        print("   • POL-1234567 (prefix format)")
        print("   • CLM-12345678 (claim numbers)")
        print("   • ABC1234567 (alpha-numeric)")
        print("   • MRN-77889900 (medical records)")
        return 0
    else:
        print("\n⚠️  Some tests failed - check error messages above")
        return 1


if __name__ == "__main__":
    sys.exit(main())



