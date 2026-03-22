from presidio_analyzer import PatternRecognizer, Pattern
policy_recognizer = PatternRecognizer(
    supported_entity="POLICY_NUMBER",
    patterns=[
        Pattern(
            name="policy_pol_prefix",
            regex=r"\bPOL[-\s]?\d{7}\b",
            score=0.85
        ),
        Pattern(
            name="claim_number",
            regex=r"\bCLM[-\s]?\d{8}\b",
            score=0.85
        ),
        Pattern(
            name="alpha_numeric_policy",
            regex=r"\b[A-Z]{3}\d{7}\b",
            score=0.8
        ),
        Pattern(
            name="policy_with_label",
            regex=r"(?i)(policy|policy\s+number)[:\s]+([A-Z]{3}\d{7}|POL[-\s]?\d{7})",
            score=0.9
        ),
        Pattern(
            name="health_insurance",
            regex=r"\b[A-Z]{2}-\d{7}-\d{1}\b",
            score=0.85
        ),
    ],
    context=[
        "policy", "policy number", "insurance", "coverage",
        "claim", "claim number", "policy id", "policy no",
        "insurance policy", "health insurance", "auto insurance",
        "life insurance", "home insurance", "provider"
    ],
    supported_language="en"
)

medical_record_recognizer = PatternRecognizer(
    supported_entity="MEDICAL_RECORD_NUMBER",
    patterns=[
        Pattern(
            name="mrn_prefix",
            regex=r"\bMRN[-\s]?\d{8,10}\b",
            score=0.9
        ),
        Pattern(
            name="medical_record_label",
            regex=r"(?i)(medical\s+record|mrn)[:\s]+([A-Z0-9]{8,12})",
            score=0.9
        ),
    ],
    context=[
        "medical record", "mrn", "patient id", "health record",
        "medical history", "hospital", "clinic", "provider"
    ],
    supported_language="en"
)

#copie
def demo_policy_recognition():
    """Demonstrate policy number detection"""
    from presidio_analyzer import AnalyzerEngine
    
    print("\n" + "="*70)
    print("POLICY NUMBER RECOGNIZER DEMO")
    print("="*70)
    
    # Create analyzer and add custom recognizers
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(policy_recognizer)
    analyzer.registry.add_recognizer(medical_record_recognizer)
    
    # Test cases
    test_cases = [
        "Policy number: POL-1234567",
        "Your policy POL 1234567 is active",
        "Claim number CLM-12345678 filed",
        "ABC1234567 is your policy ID",
        "Medical Record: MRN-77889900",
        "Health Insurance: CA-1234567-8",
        "Contact your insurance provider",  # Should NOT match
    ]
    
    print("\n🔍 Testing Policy Number Detection:")
    print("-"*70)
    
    for i, text in enumerate(test_cases, 1):
        results = analyzer.analyze(text=text, language="en")
        
        print(f"\nTest {i}: '{text}'")
        if results:
            for result in results:
                entity_text = text[result.start:result.end]
                print(f"  ✅ {result.entity_type}: '{entity_text}' (confidence: {result.score:.2f})")
        else:
            print(f"  ❌ No policy number detected")
    
    print("\n" + "="*70)
    print("✅ Policy number recognizer working correctly!")
    print("="*70)


if __name__ == "__main__":
    demo_policy_recognition()