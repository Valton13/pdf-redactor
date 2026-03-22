#!/usr/bin/env python3
"""
API Authentication Tests (FIXED: IP Isolation)
Uses unique X-Forwarded-For headers to isolate test buckets
"""
import sys
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"
DEMO_KEY = "demo-key-12345"

# Unique IPs for test isolation (prevents rate limit pollution)
TEST_IPS = {
    "anonymous": "192.0.2.1",      # TEST 1
    "authenticated": "192.0.2.2",   # TEST 2
    "invalid_key": "192.0.2.3",     # TEST 3
    "headers_anon": "192.0.2.4",    # TEST 4 anonymous
    "headers_auth": "192.0.2.5",    # TEST 4 authenticated
}


def get_headers(ip: str, api_key: str = None):
    """Helper: Build headers with IP isolation + optional API key"""
    headers = {"X-Forwarded-For": ip}
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def test_anonymous_rate_limit():
    """Test anonymous user rate limit (5 req/hour) - ISOLATED IP"""
    print("\n" + "="*60)
    print("TEST 1: Anonymous Rate Limit (5 requests/hour)")
    print("="*60)
    
    pdf_path = "test-corpus/01-resume.pdf"
    if not Path(pdf_path).exists():
        print("❌ SKIP: Test PDF not found")
        return False
    
    ip = TEST_IPS["anonymous"]
    print(f"\nUsing isolated IP: {ip}")
    print("Sending 6 requests WITHOUT API key...")
    
    for i in range(6):
        with open(pdf_path, 'rb') as f:
            files = {'file': (f"anon{i}.pdf", f, 'application/pdf')}
            response = requests.post(
                f"{BASE_URL}/redact", 
                files=files, 
                headers=get_headers(ip),
                timeout=5
            )
        
        status = response.status_code
        tier = response.headers.get("X-RateLimit-Tier", "unknown")
        
        print(f"Request {i+1}: Status {status} | Tier: {tier}", end="")
        
        if status == 429 and tier == "anonymous":
            print(" ← RATE LIMITED!")
            return True
        elif status in [200, 201, 202]:
            print()
        else:
            print(f" ❌ Unexpected status: {status}")
            return False
        
        time.sleep(0.5)
    
    print("❌ FAIL: Should have been rate limited at 6th request")
    return False


def test_authenticated_rate_limit():
    """Test authenticated user rate limit (50 req/hour) - ISOLATED IP"""
    print("\n" + "="*60)
    print("TEST 2: Authenticated Rate Limit (50 requests/hour)")
    print("="*60)
    
    pdf_path = "test-corpus/01-resume.pdf"
    if not Path(pdf_path).exists():
        print("❌ SKIP: Test PDF not found")
        return False
    
    ip = TEST_IPS["authenticated"]
    print(f"\nUsing isolated IP: {ip}")
    print(f"Sending 6 requests WITH demo API key: {DEMO_KEY[:15]}...")
    
    for i in range(6):
        with open(pdf_path, 'rb') as f:
            files = {'file': (f"auth{i}.pdf", f, 'application/pdf')}
            response = requests.post(
                f"{BASE_URL}/redact",
                files=files,
                headers=get_headers(ip, DEMO_KEY),
                timeout=5
            )
        
        status = response.status_code
        tier = response.headers.get("X-RateLimit-Tier", "unknown")
        
        print(f"Request {i+1}: Status {status} | Tier: {tier}", end="")
        
        if status in [200, 201, 202] and tier == "authenticated":
            print()
        else:
            print(f" ❌ Unexpected: status={status}, tier={tier}")
            return False
        
        time.sleep(0.5)
    
    print("✅ PASS: All 6 requests succeeded with authenticated tier")
    return True


def test_invalid_api_key():
    """Test that invalid API keys are treated as anonymous - ISOLATED IP"""
    print("\n" + "="*60)
    print("TEST 3: Invalid API Key Handling")
    print("="*60)
    
    pdf_path = "test-corpus/01-resume.pdf"
    if not Path(pdf_path).exists():
        print("❌ SKIP: Test PDF not found")
        return False
    
    ip = TEST_IPS["invalid_key"]
    print(f"\nUsing isolated IP: {ip}")
    print("Sending 1 request with INVALID API key...")
    
    headers = get_headers(ip, "invalid-key-99999")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        response = requests.post(
            f"{BASE_URL}/redact",
            files=files,
            headers=headers,
            timeout=5
        )
    
    # Should accept request and treat as anonymous
    if response.status_code in [200, 201, 202]:
        tier = response.headers.get("X-RateLimit-Tier", "unknown")
        if tier == "anonymous":
            print(f"✅ PASS: Invalid key treated as anonymous (tier: {tier})")
            print(f"   Status: {response.status_code}, Limit: {response.headers.get('X-RateLimit-Limit')}")
            return True
        else:
            print(f"❌ FAIL: Invalid key should be anonymous tier, got: {tier}")
            return False
    else:
        print(f"❌ FAIL: Invalid key caused error (status {response.status_code})")
        print(f"   Response: {response.text[:100]}")
        return False


def test_tier_headers():
    """Test that rate limit headers reflect correct tier - ISOLATED IPs"""
    print("\n" + "="*60)
    print("TEST 4: Rate Limit Headers by Tier")
    print("="*60)
    
    pdf_path = "test-corpus/01-resume.pdf"
    if not Path(pdf_path).exists():
        print("❌ SKIP: Test PDF not found")
        return False
    
    # Anonymous request (isolated IP)
    anon_ip = TEST_IPS["headers_anon"]
    with open(pdf_path, 'rb') as f:
        files = {'file': ('anon.pdf', f, 'application/pdf')}
        anon_response = requests.post(
            f"{BASE_URL}/redact",
            files=files,
            headers=get_headers(anon_ip),
            timeout=5
        )
    
    # Authenticated request (isolated IP)
    auth_ip = TEST_IPS["headers_auth"]
    with open(pdf_path, 'rb') as f:
        files = {'file': ('auth.pdf', f, 'application/pdf')}
        auth_response = requests.post(
            f"{BASE_URL}/redact",
            files=files,
            headers=get_headers(auth_ip, DEMO_KEY),
            timeout=5
        )
    
    print("\nAnonymous request headers:")
    print(f"  X-RateLimit-Limit: {anon_response.headers.get('X-RateLimit-Limit', 'MISSING')}")
    print(f"  X-RateLimit-Tier: {anon_response.headers.get('X-RateLimit-Tier', 'MISSING')}")
    
    print("\nAuthenticated request headers:")
    print(f"  X-RateLimit-Limit: {auth_response.headers.get('X-RateLimit-Limit', 'MISSING')}")
    print(f"  X-RateLimit-Tier: {auth_response.headers.get('X-RateLimit-Tier', 'MISSING')}")
    
    anon_limit = anon_response.headers.get("X-RateLimit-Limit")
    auth_limit = auth_response.headers.get("X-RateLimit-Limit")
    anon_tier = anon_response.headers.get("X-RateLimit-Tier")
    auth_tier = auth_response.headers.get("X-RateLimit-Tier")
    
    if anon_limit == "5" and anon_tier == "anonymous" and auth_limit == "50" and auth_tier == "authenticated":
        print("\n✅ PASS: Headers correctly reflect tiered limits")
        return True
    else:
        print("\n❌ FAIL: Headers do not match expected tiered limits")
        return False


def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 5 DAY 2: API AUTHENTICATION TESTS (IP ISOLATED)   ║")
    print("║  Fixed test pollution with X-Forwarded-For isolation    ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    print(f"\nℹ️  Demo API Key: {DEMO_KEY}")
    print("   Test IPs isolated via X-Forwarded-For header:")
    for name, ip in TEST_IPS.items():
        print(f"   • {name:20s}: {ip}")
    
    print("\n⚠️  PREREQUISITES:")
    print("   1. FastAPI server running (no restart needed)")
    print("   2. Rate limiter uses X-Forwarded-For for client identification")
    
    input("\nPress Enter to run tests...")
    
    results = []
    
    # Run tests (now isolated)
    results.append(("Anonymous Rate Limit", test_anonymous_rate_limit()))
    results.append(("Authenticated Rate Limit", test_authenticated_rate_limit()))
    results.append(("Invalid API Key Handling", test_invalid_api_key()))
    results.append(("Tier Headers", test_tier_headers()))
    
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
        print("\n🎉 SUCCESS! API Authentication Working (With Test Isolation):")
        print("   ✅ Anonymous: 5 requests/hour limit (isolated bucket)")
        print("   ✅ Authenticated: 50 requests/hour limit (isolated bucket)")
        print("   ✅ Invalid keys treated as anonymous (isolated bucket)")
        print("   ✅ Headers reflect correct tier (X-RateLimit-Tier)")
        print("\n🔒 Why IP Isolation Matters:")
        print("   • Tests no longer pollute each other's rate limits")
        print("   • Real-world: X-Forwarded-For trusted in production (behind proxy)")
        print("   • Production: Fly.io sets X-Forwarded-For automatically")
        print("\n💡 Next: Security headers middleware (Hour 2)")
        return 0
    else:
        print("\n⚠️  Some tests failed - check output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())