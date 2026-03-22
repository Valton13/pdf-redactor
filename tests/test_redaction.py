import sys
from pathlib import Path
import tempfile
import os
import fitz 
project_root = Path(__file__).parent.parent  
sys.path.insert(0, str(project_root))

from python.core.redactor import Redactor
from python.core.pdf_extractor import PDFExtractor

def test_metadata_strip():
    print("\n" + "="*60)
    print("test 1: meta data strip")
    print("="*60)
    
    temp_pdf = Path(tempfile.gettempdir())/"test_metadata.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50,100) , "Test Document" , fontsize = 12)
    doc.set_metadata({
        "author": "John Smith",
        "creator": "Test Creator",
        "producer": "Test Producer",
        "title": "Test Document"
    })
    doc.save(str(temp_pdf))
    doc.close()
    redactor = Redactor()
    output_pdf =Path(tempfile.gettempdir()) / "test_metadata_redacted.pdf" 
    redactor.redact_pii(str(temp_pdf), str(output_pdf), [])
    doc = fitz.open(str(output_pdf))
    metadata = doc.metadata
    doc.close()
    print(f"Original metadata:")
    print(f"  Author: John Smith")
    print(f"  Creator: Test Creator")
    print(f"\nRedacted metadata:")
    print(f"  Author: '{metadata.get('author')}'")
    print(f"  Creator: '{metadata.get('creator')}'")
    print(f"  Producer: '{metadata.get('producer')}'")
    metadata_stripped = (
        metadata.get('author') == "" and
        metadata.get('creator') == "" and
        metadata.get('producer') == ""
    )
    if metadata_stripped:
        print("\pass: Metadata successfully stripped")
        return True
    else:
        print("\fail: Metadata not fully stripped")
        return False

def test_pii_redaction():
    print("\n" + "="*60)
    print("TEST 2: Cryptographic PII Redaction")
    print("="*60)
    temp_pdf = Path(tempfile.gettempdir()) / "test_pii.pdf"
    doc = fitz.open()
    page = doc.new_page()
    text = "Contact John Smith at john@example.com for details"
    page.insert_text((50, 100), text, fontsize=12) 
    doc.save(str(temp_pdf))
    doc.close()
    print(f"Original text: {text}")
    redactor = Redactor()
    output_pdf = Path(tempfile.gettempdir()) / "test_pii_redacted.pdf"
    pii_spans = [
        (0, "John Smith", 0, 0),
        (0, "john@example.com", 0, 0)
    ]
    result = redactor.redact_pii(str(temp_pdf), str(output_pdf), pii_spans)
    print(f"\nRedaction applied: {result['redaction_count']} redactions")
    doc = fitz.open(str(output_pdf))
    redacted_text = ""
    for page in doc:
        redacted_text += page.get_text()
    doc.close()
    print(f"\nRedacted PDF text preview: {redacted_text[:50]}")
    pii_removed = (
        "John Smith" not in redacted_text and
        "john@example.com" not in redacted_text
    )
    
    if pii_removed:
        print("\n pass:")
        return True
    else:
        print("\n FAIL")
        return False

def test_visual_redaction():
    print("\n" + "="*60)
    print("TEST 3: Visual Redaction Boxes")
    print("="*60)
    temp_pdf = Path(tempfile.gettempdir()) / "test_visual.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Email: john@example.com", fontsize=12)
    doc.save(str(temp_pdf))
    doc.close()
    redactor = Redactor()
    output_pdf = Path(tempfile.gettempdir()) / "test_visual_redacted.pdf"
    pii_spans = [(0, "john@example.com", 0, 0)]
    redactor.redact_pii(str(temp_pdf), str(output_pdf), pii_spans)
    if output_pdf.exists():
        file_size = output_pdf.stat().st_size
        print(f" PASS: Redacted PDF created ({file_size} bytes)")
        print(f"   File: {output_pdf}")
        return True
    else:
        print("FAIL: Redacted PDF not created")
        return False   

def main():
    results = []
    results.append(("Metadata Stripping", test_metadata_strip()))
    results.append(("PII Cryptographic Removal", test_pii_redaction()))
    results.append(("Visual Redaction Boxes", test_visual_redaction()))
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = " PASS" if success else " FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n SUCCESS! Redaction engine working correctly")
        print("\n Redacted PDFs saved to:")
        print(f"   {tempfile.gettempdir()}/")
        return 0
    else:
        print("\n  Some tests failed - check error messages above")
        return 1


if __name__ == "__main__":
    sys.exit(main())     