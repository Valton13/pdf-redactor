import os
UPSTASH_REDIS_URL = "immense-goshawk-66079.upstash.io"
UPSTASH_REDIS_PASSWORD ="gQAAAAAAAQIfAAIncDJjZmE3Mjc4M2ZhNjM0ODA1YjYzOTdiZDRhZmM2ODg5MnAyNjYwNzk"

REDIS_URL = f"rediss://default:{UPSTASH_REDIS_PASSWORD}@{UPSTASH_REDIS_URL}:6379?ssl_cert_reqs=CERT_REQUIRED"
#REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

'''if os.getenv("ENVIRONMENT", "development") == "production":
    if "ssl_cert_reqs=CERT_NONE" in REDIS_URL:
        raise ValueError(
            " SECURITY VIOLATION: CERT_NONE not allowed in production. "
            "Use ssl_cert_reqs=CERT_REQUIRED"
        )
    if "ssl_cert_reqs=CERT_REQUIRED" not in REDIS_URL:
        raise ValueError(
            " SECURITY VIOLATION: Redis URL must include ssl_cert_reqs=CERT_REQUIRED"
        )'''
if "upstash.io" in REDIS_URL:
    # Upstash - replace any existing ssl_cert_reqs with CERT_NONE
    if "ssl_cert_reqs=" in REDIS_URL:
        # Remove existing ssl_cert_reqs parameter
        REDIS_URL = REDIS_URL.split("?ssl_cert_reqs=")[0]
    # Append correct parameter
    REDIS_URL = f"{REDIS_URL}?ssl_cert_reqs=CERT_NONE"
else:
    # Self-hosted Redis - enforce CERT_REQUIRED
    if "ssl_cert_reqs=" not in REDIS_URL:
        REDIS_URL = f"{REDIS_URL}?ssl_cert_reqs=CERT_REQUIRED"
    elif "ssl_cert_reqs=CERT_NONE" in REDIS_URL:
        raise ValueError(
            "SECURITY VIOLATION: CERT_NONE not allowed for self-hosted Redis. "
            "Use ssl_cert_reqs=CERT_REQUIRED"
        )
broker_url = REDIS_URL
result_backend = REDIS_URL

# Task settings
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Timeouts (30 seconds max per task)
task_time_limit = 30
task_soft_time_limit = 25

# Task routing
task_default_queue = "redaction"
task_default_exchange = "redaction"
task_default_routing_key = "redaction"

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 100

# Logging
worker_redirect_stdouts_level = "INFO"
