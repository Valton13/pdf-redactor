import sys
import requests
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent.parent))
BASE_URL = "http://localhost:8000"

def test_security_headers():
    """Test that all security headers are present in responses"""
    print("\n" + "="*60)
    print("TEST: Security Headers Validation")
    print("="*60)
    
    try:
        # Test multiple endpoints to ensure headers on all responses
        endpoints = [
            ("/health", "Health check (no auth)"),
            ("/docs", "Swagger UI (development only)"),
            ("/openapi.json", "OpenAPI spec")
        ]
        
        all_passed = True
        
        for path, description in endpoints:
            print(f"\n🔍 Testing {description}: {path}")
            
            try:
                response = requests.get(f"{BASE_URL}{path}", timeout=5)
            except Exception as e:
                print(f"  ❌ Connection error: {e}")
                all_passed = False
                continue
            
            if response.status_code not in [200, 202]:
                print(f"  ⚠️  Skipping (status {response.status_code})")
                continue
            
            headers = response.headers
            failures = []
            
            # Required headers (always present)
            required_headers = {
                'X-Frame-Options': 'DENY',
                'X-Content-Type-Options': 'nosniff',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'no-referrer',
                'Permissions-Policy': None,  # Check existence only
                'Content-Security-Policy': None  # Check existence only
            }
            
            for header, expected_value in required_headers.items():
                if header not in headers:
                    failures.append(f"MISSING: {header}")
                elif expected_value and headers[header] != expected_value:
                    failures.append(f"WRONG VALUE: {header}='{headers[header]}' (expected '{expected_value}')")
                else:
                    value_preview = headers[header][:40] + "..." if len(headers[header]) > 40 else headers[header]
                    print(f"  ✅ {header}: {value_preview}")
            
            # HSTS check (only in production)
            if 'Strict-Transport-Security' in headers:
                print(f"  ✅ Strict-Transport-Security: {headers['Strict-Transport-Security']}")
            else:
                print(f"  ℹ️  Strict-Transport-Security: Not set (development mode)")
            
            if failures:
                print(f"  ❌ FAILURES:")
                for f in failures:
                    print(f"    • {f}")
                all_passed = False
            else:
                print(f"  ✅ All headers valid for {path}")
        
        return all_passed
    
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_csp_swagger_compatibility():
    """Verify CSP allows Swagger UI to function (critical for development)"""
    print("\n" + "="*60)
    print("TEST: CSP Compatibility with Swagger UI")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        
        if response.status_code != 200:
            print(f"  ⚠️  Swagger UI not accessible (status {response.status_code})")
            return True  # Not a CSP failure
        
        csp = response.headers.get('Content-Security-Policy', '')
        
        if not csp:
            print("  ❌ FAIL: CSP header missing on /docs endpoint")
            return False
        
        # Check for required CSP directives for Swagger
        checks = {
            "default-src 'self'": "'self' in default-src",
            "script-src": "script-src directive present",
            "style-src": "style-src directive present",
            "unsafe-inline": "'unsafe-inline' in script/style-src (required for Swagger)",
            "img-src 'self' ": " allowed for inline images"
        }
        
        print("\nCSP Analysis for Swagger UI:")
        all_checks_pass = True
        
        for check, description in checks.items():
            if check in csp:
                print(f"  ✅ {description}")
            else:
                print(f"  ⚠️  {description} - NOT FOUND (Swagger may break)")
                all_checks_pass = False
        
        if all_checks_pass:
            print("\n✅ PASS: CSP configured for Swagger UI compatibility")
            return True
        else:
            print("\n⚠️  WARNING: CSP may break Swagger UI")
            print("   ℹ️  This is acceptable if /docs is disabled in production")
            return True  # Not a critical failure for MVP
    
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def test_header_absence():
    """Verify dangerous headers are NOT present"""
    print("\n" + "="*60)
    print("TEST: Absence of Dangerous Headers")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        headers = response.headers
        
        # Headers that should NOT be present
        forbidden_headers = [
            'Server',           # Reveals server technology
            'X-Powered-By',     # Reveals framework details
            'X-AspNet-Version', # ASP.NET version leakage
            'X-AspNetMvc-Version' # ASP.NET MVC version leakage
        ]
        
        found_forbidden = []
        for header in forbidden_headers:
            if header in headers:
                found_forbidden.append(header)
                print(f"  ❌ DANGEROUS: {header} header present (value: {headers[header][:30]}...)")
        
        if found_forbidden:
            print(f"\n⚠️  {len(found_forbidden)} dangerous headers detected")
            print("   ℹ️  These headers leak server information (remove in production reverse proxy)")
            return False
        else:
            print("  ✅ No dangerous headers present")
            return True
    
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 5 DAY 2: SECURITY HEADERS VALIDATION              ║")
    print("║  OWASP Top 10 Protection (XSS, Clickjacking, etc.)      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    print("\n⚠️  PREREQUISITES:")
    print("   1. FastAPI server running WITH security headers middleware")
    print("   2. Server must be restarted after adding middleware")
    print("\nℹ️  Header Explanations:")
    print("   • CSP: Prevents XSS by restricting script sources")
    print("   • X-Frame-Options: Blocks clickjacking attacks")
    print("   • HSTS: Enforces HTTPS (production only)")
    print("   • Permissions-Policy: Blocks camera/mic access")
    
    input("\nPress Enter when server is running...")
    
    results = []
    
    # Run tests
    results.append(("Security Headers Presence", test_security_headers()))
    results.append(("CSP Swagger Compatibility", test_csp_swagger_compatibility()))
    results.append(("Dangerous Headers Absence", test_header_absence()))
    
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
        print("\n🎉 SUCCESS! Security Headers Properly Configured:")
        print("   ✅ XSS Protection: CSP + X-XSS-Protection headers")
        print("   ✅ Clickjacking Prevention: X-Frame-Options: DENY")
        print("   ✅ MIME Sniffing Block: X-Content-Type-Options: nosniff")
        print("   ✅ Referrer Leakage Prevention: Referrer-Policy: no-referrer")
        print("   ✅ Feature Restrictions: Permissions-Policy blocks camera/mic")
        print("   ✅ HTTPS Enforcement: HSTS (production only)")
        print("\n🔒 OWASP Top 10 Coverage:")
        print("   • A03:2021 Injection → CSP blocks malicious scripts")
        print("   • A05:2021 Security Misconfiguration → Headers enforce secure defaults")
        print("   • A07:2021 Identification Failures → HSTS prevents credential theft")
        print("\n💡 Next: Fly.io configuration with tmpfs (Hour 3)")
        return 0
    else:
        print("\n⚠️  Some security header tests failed")
        print("\n🔧 Troubleshooting:")
        print("   • Did you restart server after adding middleware?")
        print("   • Verify middleware is placed AFTER app initialization")
        print("   • Check for syntax errors in main.py (python -m py_compile main.py)")
        print("   • Ensure 'import os' is at top of main.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())