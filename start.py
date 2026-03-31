import os
import subprocess
import sys

# Get PORT from environment (Railway sets this)
port = os.getenv("PORT", "8000")

# Run uvicorn with correct port
cmd = [
    sys.executable, "-m", "uvicorn",
    "python.api.main:app",
    "--host", "0.0.0.0",
    "--port", port
]

print(f"🚀 Starting server on port {port}")
subprocess.run(cmd)