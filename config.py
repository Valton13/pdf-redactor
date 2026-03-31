import os
UPSTASH_REDIS_URL = "immense-goshawk-66079.upstash.io"
UPSTASH_REDIS_PASSWORD ="gQAAAAAAAQIfAAIncDJjZmE3Mjc4M2ZhNjM0ODA1YjYzOTdiZDRhZmM2ODg5MnAyNjYwNzk"

REDIS_URL = f"rediss://default:{UPSTASH_REDIS_PASSWORD}@{UPSTASH_REDIS_URL}:6379?ssl_cert_reqs=CERT_NONE"
#REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

if os.getenv("ENVIRONMENT", "development") == "production":
    if "ssl_cert_reqs=CERT_NONE" in REDIS_URL:
        raise ValueError(
            " SECURITY VIOLATION: CERT_NONE not allowed in production. "
            "Use ssl_cert_reqs=CERT_REQUIRED"
        )
    if "ssl_cert_reqs=CERT_REQUIRED" not in REDIS_URL:
        raise ValueError(
            " SECURITY VIOLATION: Redis URL must include ssl_cert_reqs=CERT_REQUIRED"
        )
if "upstash.io" in REDIS_URL:
    # Upstash - safe to use CERT_NONE
    if "ssl_cert_reqs=CERT_NONE" not in REDIS_URL:
        # Auto-append if missing
        REDIS_URL = REDIS_URL.rstrip("/") + "?ssl_cert_reqs=CERT_NONE"
else:
    # Self-hosted Redis - enforce CERT_REQUIRED
    if "ssl_cert_reqs=CERT_NONE" in REDIS_URL:
        raise ValueError(
            "SECURITY VIOLATION: CERT_NONE not allowed for self-hosted Redis. "
            "Use ssl_cert_reqs=CERT_REQUIRED"
        )
broker_url = REDIS_URL
result_backend = REDIS_URL

broker_url = REDIS_URL
result_backend = REDIS_URL
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

task_time_limit = 30
task_soft_time_limit = 25

task_default_queue = "redaction"
task_default_exchange = "redaction"
task_default_routing_key = "redaction"

worker_prefetch_multiplier = 1 
worker_max_tasks_per_child = 100 

worker_redirect_stdouts_level = "INFO"  
