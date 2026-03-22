import sys
from pathlib import Path
import tempfile
project_root = Path(__file__).parent.parent  
sys.path.insert(0, str(project_root))
from python.core.coordinate_mapper import CoordinateMapper
import fitz

def test_direct_match():
    """Test direct text-to-rectangle mapping"""
    print("\n" + "="*60)
    print("TEST 1: Direct Text Match")
    print("="*60)
    
    # Create PDF with known text
    pdf_path = Path(tempfile.gettempdir()) / "test_direct.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 150), "John Smith", fontsize=12)
    page.insert_text((100, 180), "john@example.com", fontsize=12)
    doc.save(str(pdf_path))
    doc.close()
    
    # Map coordinates
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    
    mapper = CoordinateMapper()
    
    # Test cases
    test_cases = [
        ("John Smith", True, "Exact name match"),
        ("john@example.com", True, "Exact email match"),
        ("Jane Doe", False, "Non-existent text"),
    ]
    
    results = []
    for text, should_find, description in test_cases:
        rects = mapper.map_text_to_rects(page, text)
        found = len(rects) > 0
        passed = found == should_find
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {description}")
        print(f"   Text: '{text}' → {len(rects)} rect(s)")
        if rects:
            rect = rects[0]
            print(f"   Rect: ({rect.x0:.1f}, {rect.y0:.1f}, {rect.x1:.1f}, {rect.y1:.1f})")
        results.append(passed)
    doc.close()  
    return all(results)

def test_multi_line_text():
    """Test multi-line text mapping"""
    print("\n" + "="*60)
    print("TEST 2: Multi-Line Text")
    print("="*60)
    
    # Create PDF with multi-line address
    pdf_path = Path(tempfile.gettempdir()) / "test_multiline.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    
    address = """123 Main St
Apt 4B
San Francisco, CA 94105"""
    
    page.insert_text((50, 100), address, fontsize=11)
    doc.save(str(pdf_path))
    doc.close()
    
    # Map coordinates
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    
    mapper = CoordinateMapper()
    
    # Test multi-line match
    text = "123 Main St"
    rects = mapper.map_text_to_rects(page, text)
    
    print(f"Text: '{text}'")
    print(f"Rectangles found: {len(rects)}")
    
    if rects:
        print("✅ PASS: Multi-line text mapped successfully")
        for i, rect in enumerate(rects, 1):
            print(f"   Rect {i}: ({rect.x0:.1f}, {rect.y0:.1f}, {rect.x1:.1f}, {rect.y1:.1f})")
        result = True
    else:
        print("❌ FAIL: No rectangles found for multi-line text")
        result = False
    
    doc.close()
    
    return result


def test_case_insensitive():
    """Test case-insensitive matching"""
    print("\n" + "="*60)
    print("TEST 3: Case-Insensitive Matching")
    print("="*60)
    
    # Create PDF with mixed case
    pdf_path = Path(tempfile.gettempdir()) / "test_case.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 150), "John Smith", fontsize=12)
    doc.save(str(pdf_path))
    doc.close()
    
    # Map coordinates with different cases
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    
    mapper = CoordinateMapper(case_sensitive=False)
    
    test_cases = [
        ("John Smith", True, "Exact case"),
        ("john smith", True, "Lowercase"),
        ("JOHN SMITH", True, "Uppercase"),
        ("John smith", True, "Mixed case"),
    ]
    
    results = []
    for text, should_find, description in test_cases:
        rects = mapper.map_text_to_rects(page, text)
        found = len(rects) > 0
        passed = found == should_find
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {description}: '{text}' → {len(rects)} rect(s)")
        results.append(passed)
    
    doc.close()
    
    return all(results)


def test_confidence_scoring():
    """Test confidence scoring for PII spans"""
    print("\n" + "="*60)
    print("TEST 4: Confidence Scoring")
    print("="*60)
    
    # Create PDF
    pdf_path = Path(tempfile.gettempdir()) / "test_confidence.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 150), "john@example.com", fontsize=12)
    doc.save(str(pdf_path))
    doc.close()
    
    # Map with confidence
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    
    mapper = CoordinateMapper()
    
    pii_spans = [
        ("john@example.com", 0, 16),
        ("fake@email.com", 0, 15),  # Should not be found
    ]
    
    results = mapper.map_pii_spans(page, pii_spans, min_confidence=0.7)
    
    print(f"PII spans input: {len(pii_spans)}")
    print(f"PII spans mapped: {len(results)}")
    
    for text, rects, confidence in results:
        print(f"✅ '{text}' → {len(rects)} rect(s), confidence: {confidence:.2f}")
    
    # Should find 1, not find 1
    passed = len(results) == 1 and results[0][0] == "john@example.com"
    
    if passed:
        print("\n✅ PASS: Confidence scoring working correctly")
    else:
        print("\n❌ FAIL: Confidence scoring incorrect")
    
    doc.close()
    
    return passed


def main():
    """Run all coordinate mapping tests"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 3 DAY 1: COORDINATE MAPPING TEST                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    results = []
    
    # Run tests
    results.append(("Direct Text Match", test_direct_match()))
    results.append(("Multi-Line Text", test_multi_line_text()))
    results.append(("Case-Insensitive Matching", test_case_insensitive()))
    results.append(("Confidence Scoring", test_confidence_scoring()))
    
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
        print("\n🎉 SUCCESS! Coordinate mapping working correctly")
        return 0
    else:
        print("\n⚠️  Some tests failed - check error messages above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
