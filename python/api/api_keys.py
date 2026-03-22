import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import os
API_KEYS: Dict[str, Dict] = {}
DEMO_KEY = "demo-key-12345"

def hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

def initialize_demo_key():
    if os.getenv("ENVIROMENT") != "productions":
        demo_hash = hash_key(DEMO_KEY)
        if demo_hash not in API_KEYS:
            API_KEYS[demo_hash] = {
                "tier": "authenticated",
                "created": datetime.utcnow(),
                "last_used": None,
                "description": "Demo key for testing (remove in production)"
            }
            print(f"Demo Api {DEMO_KEY}")

def generate_api_key(tier: str = "authenticated", description: str = "") -> str:
    key = "sk_" + secrets.token_urlsafe(32)
    key_hash = hash_key(key)
    API_KEYS[key_hash] = {
        "tier": tier,
        "created": datetime.utcnow(),
        "last_used": None,
        "description": description
    }
    return key

def validate_api_key(api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
    if not api_key or not api_key.strip():
        return False , None ,"No api"
    key_hash = hash_key(api_key.strip())
    if key_hash not in API_KEYS:
        return False , None , "Wrong api"
    API_KEYS[key_hash]["last used"] = datetime.utcnow()
    return True , API_KEYS[key_hash]["tier"] , None

def get_rate_limit(tier: Optional[str]) -> int:
    limits = {
        "premium": 100,     
        "authenticated": 50, 
        None: 5            
    }
    return limits.get(tier , 5)
    
def revoke_api_key(api_key: str) -> bool:
    key_hash = hash_key(api_key)
    if key_hash in API_KEYS:
        del API_KEYS[key_hash]
        return True
    return False

initialize_demo_key()



