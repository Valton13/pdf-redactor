
from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from typing import Dict, Tuple
import hashlib
from python.api.api_keys import validate_api_key, get_rate_limit


class RateLimiter:
    def __init__(self):
        self.storage: Dict[str, Dict] = {}
    
    def _get_client_identifier(self, request: Request, api_key: str = None) -> str:
        if "x-forwarded-for" in request.headers:
            ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
        
        if api_key:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"{ip_hash}:{key_hash}"
        return ip_hash
    
    def _cleanup_expired(self):
        now = datetime.utcnow()
        expired = [k for k, v in self.storage.items() if v["reset_time"] < now]
        for k in expired:
            del self.storage[k]
    
    def check_limit(self, request: Request, api_key: str = None) -> Tuple[bool, int, int, str]:
        self._cleanup_expired()
        
        is_valid_key, tier, _ = validate_api_key(api_key) if api_key else (False, None, None)
        rate_limit = get_rate_limit(tier if is_valid_key else None)
        burst_limit = 10 if is_valid_key else 2
        
        identifier = self._get_client_identifier(request, api_key if is_valid_key else None)
        now = datetime.utcnow()
        
        if identifier not in self.storage:
            reset_time = now + timedelta(hours=1)
            self.storage[identifier] = {
                "count": 1,
                "reset_time": reset_time,
                "last_request": now,
                "tier": tier if is_valid_key else "anonymous"
            }
            return True, rate_limit - 1, 3600, tier if is_valid_key else "anonymous"
        
        record = self.storage[identifier]
        
        if record["reset_time"] < now:
            record["count"] = 1
            record["reset_time"] = now + timedelta(hours=1)
            record["last_request"] = now
            return True, rate_limit - 1, 3600, record["tier"]
        
        seconds_since_last = (now - record["last_request"]).total_seconds()
        if seconds_since_last < 60 and record["count"] >= burst_limit:
            reset_after = 60 - int(seconds_since_last)
            return False, 0, reset_after, record["tier"]
        
        if record["count"] >= rate_limit:
            reset_after = int((record["reset_time"] - now).total_seconds())
            return False, 0, reset_after, record["tier"]
        
        record["count"] += 1
        record["last_request"] = now
        remaining = rate_limit - record["count"]
        reset_after = int((record["reset_time"] - now).total_seconds())
        
        return True, remaining, reset_after, record["tier"]
rate_limiter = RateLimiter()
async def rate_limit_dependency(request: Request):
    """
    CRITICAL FIXES APPLIED:
    1. Sets state variables BEFORE exception check
    2. Removed headers from HTTPException (middleware handles all headers)
    3. Proper tier propagation
    """
    api_key = request.headers.get("X-API-Key")
    is_allowed, remaining, reset_after, tier = rate_limiter.check_limit(request, api_key)
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_tier = tier  
    if api_key:
        is_valid, key_tier, _ = validate_api_key(api_key)
        request.state.api_key_valid = is_valid
        request.state.api_key_tier = key_tier if is_valid else None
    else:
        request.state.api_key_valid = False
        request.state.api_key_tier = None   
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({tier} tier). Try again in {reset_after} seconds."
        )
    
    return request