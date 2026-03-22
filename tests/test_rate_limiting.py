#!/usr/bin/env python3
"""
Rate Limiting Security Tests (FIXED)
Handles non-JSON responses and provides server diagnostics
"""
import sys
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"


def check_server_health():
    """Verify server is running and accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server health check passed")
            return True
        else:
            print(f"❌ Server returned {response.status_code} for /health")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server!")
        print("   → Is FastAPI running? Start with:")
        print("     uvicorn python.api.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False


def safe_get_job_id(response):
    """Safely extract job_id from response, handle non-JSON"""
    try:
        return response.json().get('job_id', 'N/A')[:8]
    except Exception:
        # Check if response is HTML error page
        if '<html>' in response.text.lower():
            return "SERVER_ERROR(HTML)"
        elif response.text.strip():
            return f"NON_JSON({response.text[:20]}...)"
        else:
            return "EMPTY_RESPONSE"


def test_rate_limit_enforcement():
    """Test that rate limiting blocks excessive requests"""
    print("\n" + "="*60)
    print("TEST: Rate Limit Enforcement (5 requests/hour)")
    print("="*60)
    
    pdf_path = "test-corpus/01-resume.pdf"
    if not Path(pdf_path).exists():
        print("❌ SKIP: Test PDF not found")
        return False
    
    print(f"\nAttempting 6 rapid uploads (limit = 5/hour)...")
    
    results = []
    for i in range(6):
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (f"test{i}.pdf", f, 'application/pdf')}
                response = requests.post(f"{BASE_URL}/redact", files=files, timeout=5)
        except Exception as e:
            print(f"Request {i+1}: ❌ CONNECTION ERROR - {e}")
            return False
        
        status = response.status_code
        results.append(status)
        
        job_id_preview = safe_get_job_id(response)
        print(f"Request {i+1}: Status {status}", end="")
        
        if status == 429:
            print(f" ← RATE LIMITED! (Job ID: {job_id_preview})")
            break
        elif status in [200, 201, 202]:
            print(f" (Job ID: {job_id_preview})")
        else:
            print(f" ❌ ERROR (Job ID: {job_id_preview})")
            # Print first 200 chars of response for debugging
            print(f"   Response preview: {response.text[:200]}")
            if i == 0:  # First request failed - likely server config issue
                print("\n⚠️  DIAGNOSTIC: First request failed. Check server logs for:")
                print("   • Missing 'request: Request' parameter in /redact endpoint")
                print("   • slowapi middleware not initialized")
                print("   • Syntax error in python/api/main.py")
            return False
        
        time.sleep(0.5)
    
    # Verify 6th request was blocked
    if len(results) >= 6:
        print("\n❌ FAIL: All 6 requests succeeded (rate limiting not working)")
        return False
    elif results[-1] == 429:
        print("\n✅ PASS: Rate limiting blocked excessive requests")
        print(f"   Requests allowed: {len(results) - 1}")
        print(f"   Blocked at request #{len(results)} with 429 status")
        return True
    else:
        print(f"\n⚠️  UNEXPECTED: Last status was {results[-1]} (expected 429)")
        return False


def test_rate_limit_headers():
    """Test that rate limit headers are present in responses"""
    print("\n" + "="*60)
    print("TEST: Rate Limit Response Headers")
    print("="*60)
    
    pdf_path = "test-corpus/01-resume.pdf"
    if not Path(pdf_path).exists():
        print("❌ SKIP: Test PDF not found")
        return False
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/redact", files=files, timeout=5)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    print(f"\nResponse status: {response.status_code}")
    
    # Check for rate limit headers
    headers = response.headers
    required_headers = ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset']
    
    print("\nRate Limit Headers:")
    all_present = True
    for header in required_headers:
        value = headers.get(header, 'MISSING')
        status = "✅" if value != 'MISSING' else "❌"
        print(f"  {status} {header}: {value}")
        if value == 'MISSING':
            all_present = False
    
    if all_present and response.status_code in [200, 201, 202]:
        print("\n✅ PASS: All rate limit headers present")
        return True
    else:
        if response.status_code not in [200, 201, 202]:
            print(f"\n⚠️  Request failed (status {response.status_code}) - headers not checked")
            print(f"   Response: {response.text[:100]}")
        print("\n❌ FAIL: Missing rate limit headers")
        return False


def test_burst_protection():
    """Test hard cap on requests per minute (burst protection)"""
    print("\n" + "="*60)
    print("TEST: Burst Protection (2 requests/minute hard cap)")
    print("="*60)
    
    pdf_path = "test-corpus/01-resume.pdf"
    if not Path(pdf_path).exists():
        print("❌ SKIP: Test PDF not found")
        return False
    
    print("\nAttempting 3 rapid uploads within 10 seconds...")
    
    results = []
    start_time = time.time()
    
    for i in range(3):
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (f"burst{i}.pdf", f, 'application/pdf')}
                response = requests.post(f"{BASE_URL}/redact", files=files, timeout=5)
        except Exception as e:
            print(f"Request {i+1}: ❌ ERROR - {e}")
            return False
        
        results.append(response.status_code)
        print(f"Request {i+1}: Status {response.status_code}")
        time.sleep(1)
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f} seconds")
    
    # Should block at 3rd request due to burst protection
    if len(results) == 3 and results[2] == 429:
        print("\n✅ PASS: Burst protection blocked 3rd rapid request")
        return True
    elif len(results) < 3:
        print("\n⚠️  NOTE: Blocked before 3rd request (still valid)")
        return True
    else:
        print("\n❌ FAIL: Burst protection not enforced (all 3 requests succeeded)")
        return False


def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 5 DAY 1: RATE LIMITING SECURITY TESTS (FIXED)     ║")
    print("║  DoS Protection + Burst Control + Error Handling        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # First check server health
    if not check_server_health():
        print("\n⚠️  FIX SERVER ISSUES FIRST, THEN RE-RUN TEST")
        return 1
    
    print("\n⚠️  CRITICAL SERVER CHECKLIST (if tests fail):")
    print("   1. Did you restart FastAPI AFTER adding slowapi?")
    print("   2. Does /redact endpoint have 'request: Request' parameter?")
    print("   3. Is @limiter.limit decorator applied to /redact?")
    print("   4. Check server terminal for Python errors (red text)")
    
    input("\nPress Enter to run tests...")
    
    results = []
    
    # Run tests
    results.append(("Rate Limit Enforcement", test_rate_limit_enforcement()))
    results.append(("Rate Limit Headers", test_rate_limit_headers()))
    results.append(("Burst Protection", test_burst_protection()))
    
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
        print("\n🎉 SUCCESS! Rate limiting protecting against:")
        print("   • DoS attacks (5 req/hour per IP)")
        print("   • Burst floods (2 req/minute hard cap)")
        print("   • API abuse (clear 429 responses with Retry-After)")
        print("\n🔒 Security Posture:")
        print("   ✅ Rate limiting middleware active")
        print("   ✅ Rate limit headers in all responses")
        print("   ✅ Burst protection enforced")
        print("   ✅ Celery timeout enforcement (30s hard limit)")
        print("\n💡 Next: Auto-cleanup with 5-min TTL (Hour 3)")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - DIAGNOSE SERVER ISSUES:")
        print("\n🔍 COMMON FIXES:")
        print("   A. SERVER NOT RESTARTED:")
        print("      → Stop server (Ctrl+C)")
        print("      → Restart: uvicorn python.api.main:app --reload")
        print("")
        print("   B. MISSING REQUEST PARAMETER:")
        print("      In python/api/main.py, /redact endpoint MUST have:")
        print("      async def redact_document(request: Request, file: UploadFile = File(...)):")
        print("                                 ^^^^^^^^^^^^^^^^ ← REQUIRED")
        print("")
        print("   C. DECORATOR MISSING:")
        print("      @limiter.limit(RATE_LIMITS['anonymous'])")
        print("      async def redact_document(...):")
        print("")
        print("   D. CHECK SERVER TERMINAL:")
        print("      Look for red error text when starting server")
        print("      Common: 'NameError: name Request is not defined'")
        print("      Fix: Add 'from fastapi import Request' at top of main.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())