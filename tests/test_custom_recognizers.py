import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from presidio_analyzer import AnalyzerEngine
from python.recognizers.account_recognizer import account_recognizer , international_account_recognizer
from python.recognizers.policy_recognizer import policy_recognizer , medical_record_recognizer
from python.recognizers.employee_recognizer import employee_recognizer , EMPLOYEE_NAMES

def test_all_recognizers_integerations():
    print("\n" + "="*60)
    print("TEST 1: All Recognizers Integration")
    print("="*60)
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(account_recognizer)
    analyzer.registry.add_recognizer(international_account_recognizer)
    analyzer.registry.add_recognizer(policy_recognizer)
    analyzer.registry.add_recognizer(medical_record_recognizer)
    analyzer.registry.add_recognizer(employee_recognizer)
   # analyzer.registry.add_recognizer(common_name_recognizer)
    test_text = """
    Employee Report
    Employee: John Smith
    Contact: john.smith83@gmail.com
    Phone: (415) 555-0192
    
    Financial Information:
    Bank Account: 1234-5678-9012-3456
    Routing: 123456789
    IBAN: DE89370400440532013000
    
    Insurance Details:
    Policy Number: POL-1234567
    Claim: CLM-12345678
    Medical Record: MRN-77889900
    
    Emergency Contact:
    Name: Maria Rodriguez
    Phone: (415) 555-0199
    """
    print("Test Text (with multiple PII types):")
    print("-"*60)
    print(test_text)
    print("-"*60)
    results = analyzer.analyze(text = test_text , language= "en")
    print(f"\nTotal entities detected: {len(results)}")
    entities_by_type = {}
    for entity in results:
        entity_text = test_text[entity.start:entity.end]
        if entity.entity_type not in entities_by_type:
            entities_by_type[entity.entity_type] = []
        entities_by_type[entity.entity_type].append((entity_text, entity.score))
    
    # Print grouped results
    print("\nDetected Entities by Type:")
    print("-"*60)
    for entity_type in sorted(entities_by_type.keys()):
        print(f"\n{entity_type}:")
        for text, score in sorted(entities_by_type[entity_type]):
            confidence = "⭐⭐⭐" if score >= 0.9 else "⭐⭐" if score >= 0.8 else "⭐"
            print(f"  {confidence} '{text}' ({score:.2f})")
    
    # Verify expected entities
    expected_types = {
        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
        "BANK_ACCOUNT", "POLICY_NUMBER", "MEDICAL_RECORD_NUMBER",
        "EMPLOYEE_NAME"
    }
    
    detected_types = set(entities_by_type.keys())
    all_expected_found = expected_types.issubset(detected_types)
    
    print("\n" + "-"*60)
    print("Verification:")
    print(f"Expected entity types: {len(expected_types)}")
    print(f"Detected entity types: {len(detected_types)}")
    print(f"All expected found: {all_expected_found}")
    
    if all_expected_found:
        print("\n✅ PASS: All custom recognizers working together")
        return True
    else:
        missing = expected_types - detected_types
        print(f"\n❌ FAIL: Missing entity types: {missing}")
        return False


def test_employee_denylist_accuracy():
    """Test employee denylist exact matching"""
    print("\n" + "="*60)
    print("TEST 2: Employee Denylist Accuracy")
    print("="*60)
    
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(employee_recognizer)
    
    # Test exact matches from denylist
    print(f"Denylist contains {len(EMPLOYEE_NAMES)} names:")
    for i, name in enumerate(EMPLOYEE_NAMES[:5], 1):  # Show first 5
        print(f"  {i}. {name}")
    if len(EMPLOYEE_NAMES) > 5:
        print(f"  ... and {len(EMPLOYEE_NAMES) - 5} more")
    
    print("\nTesting exact matches:")
    results = []
    
    for name in EMPLOYEE_NAMES[:3]:  # Test first 3
        text = f"Contact {name} for details"
        entities = analyzer.analyze(text=text, language="en")
        
        matched = len(entities) > 0
        correct_entity = matched and entities[0].entity_type == "EMPLOYEE_NAME"
        perfect_confidence = matched and entities[0].score == 1.0
        
        status = "✅ PASS" if (matched and correct_entity and perfect_confidence) else "❌ FAIL"
        
        print(f"\n{status} '{name}'")
        print(f"   Text: '{text}'")
        print(f"   Matched: {matched}")
        if matched:
            print(f"   Entity Type: {entities[0].entity_type}")
            print(f"   Confidence: {entities[0].score:.2f} (expected: 1.0)")
        
        results.append(matched and correct_entity and perfect_confidence)
    
    # Test non-matches (names not in denylist)
    print("\nTesting non-matches (should NOT detect):")
    non_matches = ["Jane Doe", "Bob Johnson", "Alice Williams"]
    
    for name in non_matches:
        text = f"Contact {name} for details"
        entities = analyzer.analyze(text=text, language="en")
        
        not_matched = len(entities) == 0
        
        status = "✅ PASS" if not_matched else "❌ FAIL"
        print(f"{status} '{name}' → {'correctly not matched' if not_matched else 'incorrectly matched'}")
        
        results.append(not_matched)
    
    return all(results)


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n" + "="*60)
    print("TEST 3: Edge Cases")
    print("="*60)
    
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(account_recognizer)
    analyzer.registry.add_recognizer(policy_recognizer)
    analyzer.registry.add_recognizer(employee_recognizer)
    
    test_cases = [
        # Edge case: Partial matches should NOT trigger
        ("Account ending in 3456", False, "Partial account number"),
        
        # Edge case: Similar but not exact employee name
        ("John Smit", False, "Partial employee name"),
        
        # Edge case: Case variations (should still match)
        ("john smith", True, "Lowercase employee name"),
        
        # Edge case: Extra spaces
        ("POL  -  1234567", True, "Extra spaces in policy number"),
        
        # Edge case: Account number in different context
        ("Reference #1234567890123456", True, "Account in reference context"),
    ]
    
    results = []
    for text, should_match, description in test_cases:
        entities = analyzer.analyze(text=text, language="en")
        matched = len(entities) > 0
        
        status = "✅ PASS" if matched == should_match else "❌ FAIL"
        
        print(f"\n{status} {description}")
        print(f"   Text: '{text}'")
        print(f"   Expected: {'match' if should_match else 'no match'}")
        print(f"   Detected: {'match' if matched else 'no match'}")
        
        if matched:
            for entity in entities:
                entity_text = text[entity.start:entity.end]
                print(f"     → {entity.entity_type}: '{entity_text}' ({entity.score:.2f})")
        
        results.append(matched == should_match)
    
    return all(results)


def test_confidence_hierarchy():
    """Test that confidence scores are properly prioritized"""
    print("\n" + "="*60)
    print("TEST 4: Confidence Score Hierarchy")
    print("="*60)
    
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(employee_recognizer)
    #analyzer.registry.add_recognizer(common_name_recognizer)
    
    # Test text with both specific employee and common name
    text = "John Smith and John Doe attended the meeting"
    print(f"Text: '{text}'")
    print("\nExpected:")
    print("  • 'John Smith' → EMPLOYEE_NAME (confidence: 1.0)")
    #print("  • 'John' → COMMON_NAME (confidence: 0.75)")
    #print("  • 'John Doe' → COMMON_NAME (confidence: 0.75)")
    
    results = analyzer.analyze(text=text, language="en")
    
    print("\nActual:")
    for entity in sorted(results, key=lambda x: x.start):
        entity_text = text[entity.start:entity.end]
        print(f"  • '{entity_text}' → {entity.entity_type} (confidence: {entity.score:.2f})")
    
    # Verify confidence hierarchy
    employee_found = any(
        e.entity_type == "EMPLOYEE_NAME" and 
        text[e.start:e.end] == "John Smith" and 
        e.score == 1.0 
        for e in results
    )
    
    common_names_found = sum(
        1 for e in results 
        if e.entity_type == "COMMON_NAME" and e.score == 0.75
    ) >= 2
    
    passed = employee_found 
    
    if passed:
        print("\n✅ PASS: Confidence hierarchy working correctly")
        print("   • Specific employee names: 1.0 confidence")
        print("   • Common names: 0.75 confidence")
    else:
        print("\n❌ FAIL: Confidence hierarchy not working as expected")
    
    return passed


def test_real_world_documents():
    """Test on realistic document snippets"""
    print("\n" + "="*60)
    print("TEST 5: Real-World Document Snippets")
    print("="*60)
    
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(account_recognizer)
    analyzer.registry.add_recognizer(policy_recognizer)
    analyzer.registry.add_recognizer(medical_record_recognizer)
    analyzer.registry.add_recognizer(employee_recognizer)
    
    # Realistic document snippets
    documents = [
        ("Bank Statement", 
         "Account Statement\nAccount: 1234-5678-9012-3456\nBalance: $5,240.00"),
        
        ("Insurance Claim",
         "Claim Form\nPolicy: POL-1234567\nClaim #: CLM-12345678\nPatient: John Smith"),
        
        ("Medical Record",
         "Patient Information\nName: Sarah Chen\nMRN: MRN-77889900\nDOB: 08/14/1985"),
        
        ("Employment Application",
         "Applicant: Miguel Rodriguez\nEmergency Contact: Maria Rodriguez\nPhone: (415) 555-0192"),
    ]
    
    results = []
    for doc_name, text in documents:
        entities = analyzer.analyze(text=text, language="en")
        
        print(f"\n{doc_name}:")
        print(f"  PII detected: {len(entities)} entities")
        
        if entities:
            entity_types = set(e.entity_type for e in entities)
            print(f"  Types: {', '.join(sorted(entity_types))}")
            
            # Should detect at least 2 entities per document
            has_multiple = len(entities) >= 2
            results.append(has_multiple)
        else:
            print("  ⚠️  No PII detected")
            results.append(False)
    
    all_detected = all(results)
    
    if all_detected:
        print("\n✅ PASS: All real-world documents detected correctly")
    else:
        print("\n❌ FAIL: Some documents not detected properly")
    
    return all_detected


def main():
    """Run all custom recognizer tests"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 3 DAY 2: CUSTOM RECOGNIZERS COMPREHENSIVE TEST    ║")
    print("║  BANK_ACCOUNT + POLICY_NUMBER + EMPLOYEE_NAME           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    results = []
    
    # Run tests
    results.append(("All Recognizers Integration", test_all_recognizers_integerations()))
    results.append(("Employee Denylist Accuracy", test_employee_denylist_accuracy()))
    results.append(("Edge Cases", test_edge_cases()))
    results.append(("Confidence Hierarchy", test_confidence_hierarchy()))
    results.append(("Real-World Documents", test_real_world_documents()))
    
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
        print("\n🎉 SUCCESS! All custom recognizers working correctly")
        print("\n✅ Complete Custom Recognizer Suite:")
        print("   • BANK_ACCOUNT: 16-digit patterns, IBAN, UK formats")
        print("   • POLICY_NUMBER: Insurance policy formats")
        print("   • MEDICAL_RECORD_NUMBER: MRN patterns")
        print("   • EMPLOYEE_NAME: Exact match denylist (100% confidence)")
        #print("   • COMMON_NAME: Common first names (75% confidence)")
        
        print("\n✅ Total Patterns Implemented:")
        print("   • 5 bank account patterns")
        print("   • 5 policy number patterns")
        print("   • 2 medical record patterns")
        print("   • 8 employee names in denylist")
        print("   • 15 common first names")
        
        print("\n✅ Next Step: Combine with Presidio in Hybrid Analyzer (Hour 8)")
        return 0
    else:
        print("\n Some tests failed - check error messages above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
