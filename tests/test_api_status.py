import requests
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

def upload_pdf():
    """Helper: Upload PDF and return job_id"""
    pdf_path = "test-corpus/01-resume.pdf"
    with open(pdf_path, 'rb') as f:
        files = {'file': ('resume.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/redact", files=files)
    
    if response.status_code == 202:
        return response.json()['job_id']
    return None

def test_job_status_pending():
    """Test status endpoint for pending job"""
    print("\n" + "="*60)
    print("TEST 1: Job Status (Pending)")
    print("="*60)
    
    job_id = upload_pdf()
    if not job_id:
        print(" FAIL: Could not upload test PDF")
        return False
    
    print(f"Uploaded job: {job_id}")
    
    response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'pending' and data['job_id'] == job_id:
            print("\n PASS: Job status is 'pending'")
            return job_id
        else:
            print("\n FAIL: Status not 'pending'")
            return None
    else:
        print(f"\n FAIL: Expected 200, got {response.status_code}")
        return None
    
def test_job_not_found():
    """Test status endpoint with invalid job_id"""
    print("\n" + "="*60)
    print("TEST 2: Job Not Found")
    print("="*60)
    
    invalid_id = "invalid-job-id-12345"
    response = requests.get(f"{BASE_URL}/jobs/{invalid_id}")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 404 and "not found" in response.json()['detail'].lower():
        print("\n PASS: Correctly returns 404 for invalid job_id")
        return True
    else:
        print("\n FAIL: Should return 404 for invalid job_id")
        return False
    
def test_job_completed_status():
    """Test status after job completion (using debug endpoint)"""
    print("\n" + "="*60)
    print("TEST 3: Job Status (Completed)")
    print("="*60)
    
    job_id = upload_pdf()
    if not job_id:
        print("❌ FAIL: Could not upload test PDF")
        return False
    
    print(f"Uploaded job: {job_id}")
    
    # Force-complete job using debug endpoint
    print("  Forcing job completion via debug endpoint...")
    debug_response = requests.post(f"{BASE_URL}/debug/complete-job/{job_id}?pii_count=7&redactions=7")
    
    if debug_response.status_code != 200:
        print(f"   Debug endpoint failed: {debug_response.status_code}")
        return False
    
    # Check status
    time.sleep(0.5)  # Small delay for processing
    response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        if (data['status'] == 'completed' and 
            data['pii_detected'] == 7 and 
            data['redactions_applied'] == 7 and
            data.get('download_url')):
            print("\n PASS: Job status updated to 'completed' with metrics")
            print(f"   Download URL: {data['download_url']}")
            return job_id
        else:
            print("\n FAIL: Status not updated correctly")
            return None
    else:
        print(f"\n FAIL: Expected 200, got {response.status_code}")
        return None
    
def test_download_endpoint():
    """Test download endpoint for completed job"""
    print("\n" + "="*60)
    print("TEST 4: Download Redacted PDF")
    print("="*60)
    
    job_id = upload_pdf()
    if not job_id:
        print(" FAIL: Could not upload test PDF")
        return False
    
    # Force-complete job
    requests.post(f"{BASE_URL}/debug/complete-job/{job_id}")
    time.sleep(0.5)
    
    # Download file
    response = requests.get(f"{BASE_URL}/download/{job_id}")
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
    print(f"Content-Disposition: {response.headers.get('content-disposition', 'N/A')}")
    
    if (response.status_code == 200 and 
        'application/pdf' in response.headers.get('content-type', '') and
        'attachment' in response.headers.get('content-disposition', '')):
        print("\n PASS: Download endpoint serves PDF correctly")
        print(f"   File size: {len(response.content)} bytes")
        return True
    else:
        print("\n FAIL: Download endpoint not working correctly")
        return False

def test_download_pending_job():
    """Test download endpoint for pending job (should fail)"""
    print("\n" + "="*60)
    print("TEST 5: Download Pending Job (Should Fail)")
    print("="*60)
    
    job_id = upload_pdf()
    if not job_id:
        print("❌ FAIL: Could not upload test PDF")
        return False
    
    response = requests.get(f"{BASE_URL}/download/{job_id}")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 400 and "not completed" in response.json()['detail'].lower():
        print("\n PASS: Correctly rejects download for pending job")
        return True
    else:
        print("\n FAIL: Should reject download for pending job")
        return False

def main():
    """Run all status endpoint tests"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 4 DAY 1: JOB STATUS ENDPOINT TEST                 ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    results = []
    job_id_pending = None
    job_id_completed = None
    
    # Run tests
    job_id_pending = test_job_status_pending()
    results.append(("Job Status (Pending)", job_id_pending is not None))
    
    results.append(("Job Not Found", test_job_not_found()))
    
    job_id_completed = test_job_completed_status()
    results.append(("Job Status (Completed)", job_id_completed is not None))
    
    results.append(("Download Redacted PDF", test_download_endpoint()))
    results.append(("Download Pending Job", test_download_pending_job()))
    
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
    
    if passed == total and job_id_pending and job_id_completed:
        print("\n SUCCESS! Job status tracking working correctly")
        print("\n Key Validations:")
        print(f"   • Pending jobs show status='pending'")
        print(f"   • Invalid job IDs return 404")
        print(f"   • Completed jobs show status='completed' + metrics")
        print(f"   • Download URL provided for completed jobs")
        print(f"   • Download endpoint serves PDF with correct headers")
        print(f"   • Pending jobs cannot be downloaded (400 error)")
        print(f"\n Test job IDs:")
        print(f"   Pending: {job_id_pending}")
        print(f"   Completed: {job_id_completed}")
        return True
    else:
        print("\n  Some tests failed - check error messages above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)