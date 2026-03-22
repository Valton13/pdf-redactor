import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from python.core.file_validator import FileValidator

def test_valid_pdf():
    print("\n" + "="*60)
    print("TEST 1: Valid PDF Upload")
    print("="*60)
    pdf_path = "test-corpus/01-resume.pdf"
    if not os.path.exists(pdf_path):
        print("Test pdf noty found")
        return False
    with open(pdf_path ,'rb') as f:
        content = f.read()
    validator = FileValidator()
    is_valid, error = validator.validate_upload(content, "resume.pdf")
    print(f"File: {pdf_path}")
    print(f"Size: {len(content)} bytes")
    print(f"Magic bytes: {content[:5]}")
    print(f"Result: {' PASS' if is_valid else ' FAIL'}")
    if error:
        print(f"Error :{error}")
    return is_valid

def test_malware_disguised_as_pdf():
    print("\n" + "="*60)
    print("TEST 2: Malware Disguised as PDF (.exe renamed)")
    print("="*60)
    fake_pdf_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00'  
    fake_pdf_content += b'\x00' * 10
    validator = FileValidator()
    is_valid, error = validator.validate_upload(fake_pdf_content, "invoice.pdf")
    print(f"Content (first 10 bytes): {fake_pdf_content[:10]}")
    print(f"Result: {' PASS' if not is_valid else ' FAIL'}")
    print(f"Blocked reason: {error}")
    return not is_valid and "Invalid PDF format" in error

def test_oversized_file():
    print("\n" + "="*60)
    print("TEST 3: Oversized File (>10MB)")
    print("="*60)
    oversized_content = b'%PDF-1.4\n' + b'x' * (11 * 1024 * 1024)
    validator = FileValidator(max_size_mb=10)
    is_valid, error = validator.validate_upload(oversized_content, "large.pdf")
    print(f"Size: {len(oversized_content) / (1024*1024):.1f}MB")
    print(f"Result: {' PASS' if not is_valid else ' FAIL'}")
    print(f"Blocked reason: {error}")
    return not is_valid and "exceeds limit" in error

def test_path_traversal():
    print("\n" + "="*60)
    print("TEST 4: Path Traversal Attempt")
    print("="*60)
    valid_pdf = b'%PDF-1.4\ntrailer<</Root<</Pages<</Kids[<</MediaBox[0 0 612 792]>>]>>>>>>'
    validator = FileValidator()
    test_cases = [
        ("../../etc/passwd.pdf", "Linux path traversal"),
        ("..\\..\\windows\\system32\\cmd.exe.pdf", "Windows path traversal"),
        ("/etc/shadow.pdf", "Absolute path"),
    ]
    all_blocked = True
    for filename, description in test_cases:
        is_valid, error = validator.validate_upload(valid_pdf, filename)
        status = " BLOCKED" if not is_valid else " ALLOWED"
        print(f"{status} | {description}: {filename}")
        if is_valid:
            all_blocked = False
    return all_blocked

def test_corrupted_pdf():
    print("\n" + "="*60)
    print("TEST 5: Corrupted PDF (Header Not at Start)")
    print("="*60)
    corrupted_pdf = b'GARBAGE_DATA_BEFORE_HEADER' + b'%PDF-1.4\nvalid content'  
    validator = FileValidator()
    is_valid, error = validator.validate_upload(corrupted_pdf, "corrupted.pdf")   
    print(f"Content starts with: {corrupted_pdf[:30]}")
    print(f"Result: {' PASS' if not is_valid else ' FAIL'}")
    print(f"Blocked reason: {error}") 
    return not is_valid and "header not at start" in error

def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 5 DAY 1: SECURITY VALIDATION TESTS                 ║")
    print("║  Magic Bytes + Path Traversal + Size Enforcement        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    results = []
    results.append(("Valid PDF", test_valid_pdf()))
    results.append(("Malware Disguised as PDF", test_malware_disguised_as_pdf()))
    results.append(("Oversized File", test_oversized_file()))
    results.append(("Path Traversal", test_path_traversal()))
    results.append(("Corrupted PDF", test_corrupted_pdf()))
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
        print("\n🎉 SUCCESS! File validation hardened against:")
        print("   • Malware disguised as PDFs (.exe renamed)")
        print("   • Path traversal attacks (../../etc/passwd)")
        print("   • Oversized file DoS attempts")
        print("   • Corrupted PDFs with hidden headers")
        print("\n🔒 Security Posture:")
        print("   ✅ Magic bytes validation (%PDF- header check)")
        print("   ✅ Path traversal prevention")
        print("   ✅ Size enforcement (10MB hard limit)")
        print("   ✅ Filename sanitization")
        print("\n💡 Next: Timeout enforcement in Celery tasks (Hour 2)")
        return 0
    else:
        print("\n⚠️  Some security tests failed - critical vulnerabilities remain!")
        return 1
if __name__ == "__main__":
    sys.exit(main())
