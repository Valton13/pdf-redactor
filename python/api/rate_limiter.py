from slowapi import Limiter ,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

RATE_LIMITS = {
    "anonymous": "5/hour",
    "authenticated": "50/hour",
    "burst": "2/minute" 
}

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMITS["anonymous"]],
    headers_enabled=True,
    storage_uri=None
)
rate_limit_exceeded_handler = _rate_limit_exceeded_handler
'''
def rate_limit_exceedhandler(request : Request , exc:RateLimitExceeded):
    retry_after = exc.limit.limit.remaining_seconds_in_period
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "limit": str(exc.limit.limit),
            "remaining": exc.limit.remaining,
            "reset_after": retry_after
        },
        headers={"Retry-After": str(retry_after)}
    )
    '''