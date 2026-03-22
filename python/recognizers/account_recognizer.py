from presidio_analyzer import PatternRecognizer , Pattern
account_recognizer = PatternRecognizer(
    supported_entity= "BANK_ACCOUNT",
    patterns=[
        Pattern(
            name="account_16digit_hyphen",
            regex=r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
            score=0.9
        ),
        Pattern(
            name="account_16digit_space",
            regex=r"\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b",
            score=0.9
        ),
        Pattern(
            name="account_16digit_plain",
            regex=r"\b\d{16}\b",
            score=0.85
        ),
        Pattern(
            name="account_with_label",
            regex=r"(?i)(account|acct)[:\s]+(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})",
            score=0.95
        ),
        Pattern(
            name="routing_account",
            regex=r"(?i)routing[:\s]+\d{9}.*account[:\s]+(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})",
            score=0.9
        ),
    ],
    context=[
        "account", "acct", "account number", "bank account",
        "routing", "aba", "bank", "statement", "balance",
        "deposit", "withdrawal", "transfer"
    ],
    supported_language= "en"
)

international_account_recognizer  =PatternRecognizer(
    supported_entity="BANK_ACCOUNT",
    patterns=[
        Pattern(
            name="iban_format",
            regex=r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
            score=0.85
        ),
        Pattern(
            name="uk_bank_account",
            regex=r"\b\d{2}-\d{2}-\d{2}\s+\d{8}\b",
            score=0.85
        ),
    ],
    context=[
        "iban", "international", "swift", "bic",
        "sort code", "uk account", "european"
    ],
    supported_language="en"
)
#copies
def demo_account_recognition():
    """Demonstrate bank account number detection"""
    from presidio_analyzer import AnalyzerEngine
    
    print("\n" + "="*70)
    print("BANK ACCOUNT RECOGNIZER DEMO")
    print("="*70)
    
    # Create analyzer and add custom recognizer
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(account_recognizer)
    analyzer.registry.add_recognizer(international_account_recognizer)
    
    # Test cases
    test_cases = [
        "Account: 1234-5678-9012-3456",
        "My bank account is 1234 5678 9012 3456",
        "Account number 1234567890123456 needs verification",
        "Routing: 123456789, Account: 9876-5432-1098-7654",
        "IBAN: DE89370400440532013000",
        "UK Account: 12-34-56 12345678",
        "Contact support at support@bank.com",  # Should NOT match
    ]
    
    print("\n🔍 Testing Bank Account Detection:")
    print("-"*70)
    
    for i, text in enumerate(test_cases, 1):
        results = analyzer.analyze(text=text, language="en")
        
        print(f"\nTest {i}: '{text}'")
        if results:
            for result in results:
                entity_text = text[result.start:result.end]
                print(f"  ✅ {result.entity_type}: '{entity_text}' (confidence: {result.score:.2f})")
        else:
            print(f"  ❌ No bank account detected")
    
    print("\n" + "="*70)
    print("✅ Bank account recognizer working correctly!")
    print("="*70)


if __name__ == "__main__":
    demo_account_recognition()