import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_upstash_redis():
    print("\n" + "="*60)
    print("TEST: Upstash Cloud Redis Connection")
    print("="*60)
    try:
        import redis
        from python.worker.config import REDIS_URL
        print(f" Connecting to: {REDIS_URL[:30]}")
        r = redis.Redis.from_url(
            REDIS_URL,decode_responses=True,ssl_cert_reqs=None)
        if r.ping():
            print(" SUCCESS: Connected to Upstash Redis!")
            try:
                info = r.info()
                print(f"   Version: {info.get('redis_version', 'N/A')}")
                print(f"   Memory: {info.get('used_memory_human', 'N/A')}")
                print(f"   Keys: {r.dbsize()}")
            except Exception as e:
                print(f"    Info unavailable (restricted on free tier): {e}")
            test_key = "upstash_test"
            r.set(test_key, "cloud_redis_working")
            value = r.get(test_key)
            r.delete(test_key)
            if value == "cloud_redis_working":
                print("   Set/Get test:  PASS")
                print("\n🎉 Upstash Redis is ready for Celery!")
                return True
            else:
                print("   Set/Get test:  FAIL")
                return False
        else:
            print(" Connection failed (no ping response)")
            return False
    except redis.AuthenticationError:
        print(" AUTHENTICATION ERROR: Invalid password or URL")
        print("    Check: Did you paste the FULL password?")
        print("    Check: Is URL missing 'rediss://' prefix?")
        return False
    except redis.ConnectionError as e:
        print(f" CONNECTION ERROR: {e}")
        print("    Check: Is URL format correct?")
        print("    Check: Firewall blocking port 6379?")
        return False
    except Exception as e:
        print(f" ERROR: {type(e).__name__}: {e}")
        return False
    
def show_setup_instructions():
    from python.worker.config import UPSTASH_REDIS_PASSWORD , UPSTASH_REDIS_URL
    if "YOUR_UPSTASH" in UPSTASH_REDIS_URL or "YOUR_UPSTASH" in UPSTASH_REDIS_PASSWORD:
        print("\ SETUP INCOMPLETE!")
        print("="*60)
        print("You need to update python/worker/config.py with your Upstash credentials:")
        print("\n1. Get credentials from Upstash dashboard:")
        print("   • URL: From 'REST API' tab (remove 'https://' prefix)")
        print("   • Password: From 'Python' tab")
        print("\n2. Edit python/worker/config.py:")
        print('   UPSTASH_REDIS_URL = "your-db-name-xyz.upstash.io"')
        print('   UPSTASH_REDIS_PASSWORD = "your_full_password_here"')
        print("\n3. Run this test again")
        print("="*60)
        return False
    return True

def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 4 DAY 2: UPSTASH CLOUD REDIS SETUP                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Check if config is updated
    if not show_setup_instructions():
        return 1
    
    # Run connection test
    success = test_upstash_redis()
    
    if success:
        print("\n NEXT STEP: Build Celery redaction task (Hour 6)")
        print("\n Why Upstash Rocks:")
        print("   • Zero maintenance (no Docker/local install)")
        print("   • Global edge network (low latency worldwide)")
        print("   • Free tier: 10k commands/day (enough for 100+ PDFs)")
        print("   • Production-ready from minute 1")
        print("\n Security Note:")
        print("   • Connection is TLS encrypted (rediss://)")
        print("   • Password is in config (move to env vars for production)")
        return 0
    else:
        print("\n TROUBLESHOOTING:")
        print("   1. Verify URL format: 'your-db.upstash.io' (NO https://)")
        print("   2. Paste FULL password (starts with 'AQAB...')")
        print("   3. Check firewall: Port 6379 must be open")
        print("   4. Test manually: redis-cli -u rediss://default:PASSWORD@YOUR_DB.upstash.io")
        return 1


if __name__ == "__main__":
    sys.exit(main())