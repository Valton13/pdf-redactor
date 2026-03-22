import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_valid_pdf_upload():
    print("\n" + "="*60)
    print("TEST 1: Valid PDF Upload")
    print("="*60)
    
    pdf_path = "test-corpus/01-resume.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"SKIP: Test PDF not found: {pdf_path}")
        return False
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/redact", files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 202:
        data = response.json()
        print(f"\n PASS: Job created successfully")
        print(f"   Job ID: {data['job_id']}")
        print(f"   Status: {data['status']}")
        print(f"   File: {data['file_name']}")
        return data['job_id']
    else:
        print(f"\n FAIL: Expected 202, got {response.status_code}")
        return None
    
def test_invalid_file_type():
    """Test uploading non-PDF file (should fail)"""
    print("\n" + "="*60)
    print("TEST 2: Invalid File Type (PNG)")
    print("="*60)
    
    # Create temporary PNG file
    png_path = "error.png"
    with open(png_path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')  # PNG header
    
    with open(png_path, 'rb') as f:
        files = {'file': ('test_image.png', f, 'image/png')}
        response = requests.post(f"{BASE_URL}/redact", files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 400 and "PDF" in response.json()['detail']:
        print(f"\n PASS: Correctly rejected non-PDF file")
        return True
    else:
        print(f"\n FAIL: Should reject non-PDF files")
        return False

def test_file_too_large():
    """Test uploading file >10MB (should fail)"""
    print("\n" + "="*60)
    print("TEST 3: File Too Large (>10MB)")
    print("="*60)
    
    # Create 11MB temporary file
    large_path = "QA notes till dt. 12.02.2026.pdf"
    with open(large_path, 'wb') as f:
        f.write(b'%PDF-1.4\n' + b'x' * (11 * 1024 * 1024))  # 11MB PDF
    
    with open(large_path, 'rb') as f:
        files = {'file': ('large.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/redact", files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 413:
        print(f"\n PASS: Correctly rejected file >10MB")
        return True
    else:
        print(f"\n FAIL: Should reject files >10MB")
        return False

def test_missing_file():
    """Test POST without file (should fail)"""
    print("\n" + "="*60)
    print("TEST 4: Missing File Parameter")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/redact")
    
    print(f"Status Code: {response.status_code}")
    
    # FastAPI returns 422 for validation errors
    if response.status_code in [400, 422]:
        print(f"\n PASS: Correctly rejected missing file")
        return True
    else:
        print(f"\n FAIL: Should reject missing file parameter")
        return False

def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Health Check Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200 and response.json().get('status') == 'ok':
        print(f"\nPASS: Health check working")
        return True
    else:
        print(f"\n FAIL: Health check failed")
        return False

def main():
    """Run all upload endpoint tests"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 4 DAY 1: FASTAPI UPLOAD ENDPOINT TEST             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    results = []
    job_id = None
    
    # Run tests
    job_id = test_valid_pdf_upload()
    results.append(("Valid PDF Upload", job_id is not None))
    
    results.append(("Invalid File Type", test_invalid_file_type()))
    results.append(("File Too Large", test_file_too_large()))
    results.append(("Missing File", test_missing_file()))
    results.append(("Health Check", test_health_check()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = " PASS" if success else " FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n Results: {passed}/{total} tests passed")
    
    if passed == total and job_id:
        print(f"\n SUCCESS! Upload endpoint working correctly")
        print(f"\n Key Validations:")
        print(f"   • Accepts valid PDFs (returns job_id: {job_id[:8]}...)")
        print(f"   • Rejects non-PDF files (400 error)")
        print(f"   • Rejects files >10MB (413 error)")
        print(f"   • Requires file parameter (422 error)")
        print(f"   • Health check operational")
        print(f"\n Next Step: Test job status endpoint with job_id: {job_id}")
        return job_id
    else:
        print("\n Some tests failed - check error messages above")
        return None


if __name__ == "__main__":
    import sys
    job_id = main()
    sys.exit(0 if job_id else 1)