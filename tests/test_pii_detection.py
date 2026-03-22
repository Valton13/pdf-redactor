import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from python.analyzer.pii_detector import PIIDetector
detector = PIIDetector(confidence_threshold=0.5)
test_cases = [
    ("Phone: (415) 555-0192", "PHONE_NUMBER"),
    ("SSN: 123-45-6789", "US_SSN"),
    ("Email: john@example.com", "EMAIL_ADDRESS"),
]

print("Quick Presidio Validation Test")
print("="*50)

all_passed = True
for text, expected_type in test_cases:
    results = detector.analyze_text(text)
    detected_types = [r.entity_type for r in results]
    passed = expected_type in detected_types
    
    status = "PASS" if passed else " FAIL"
    print(f"{status} | '{text}'")
    print(f"Expected: {expected_type}")
    print(f"Detected: {detected_types}")
    if results and passed:
        entity = results[0]
        print(f"Confidence: {entity.score:.2f}")
    print()
    
    if not passed:
        all_passed = False

if all_passed:
    print(" All quick tests passed! Presidio is working correctly.")
    sys.exit(0)
else:
    print("Some tests failed - this is normal for SSN without perfect formatting")
    sys.exit(1)