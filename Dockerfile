# Smart Document Redactor - Production Dockerfile (Render.com Compatible)
# Fixes permission issues by installing dependencies globally (not --user)

# 🔒 Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies globally (NOT --user)
WORKDIR /app
COPY requirements.txt requirements_api.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements_api.txt

# 🔒 Stage 2: Runtime image
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 🔒 Create non-root user (Render.com best practice)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Copy dependencies from builder
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY --chown=appuser:appuser . /app
WORKDIR /app

# 🔒 Drop privileges BEFORE running application
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 🔑 CRITICAL FIX: Use python -m uvicorn (avoids permission issues)
CMD ["python", "-m", "uvicorn", "python.api.main:app", "--host", "0.0.0.0", "--port", "8000"]