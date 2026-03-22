from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi import Request 
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends
from datetime import datetime
import uuid
import requests
import os
import logging
import tempfile
from python.api.rate_limiter import limiter
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from python.api.schemas import(RedactionJob,JobStatusResponse,HealthCheck,JobStatus,ErrorResponse)
from python.worker.tasks import redact_pdf_task
from python.core.file_validator import FileValidator
from python.api.rate_limiter import RATE_LIMITS , limiter , rate_limit_exceeded_handler
from python.api.dependencies import rate_limit_dependency
from python.api import api_keys

jobs={}
logger = logging.getLogger(__name__)

app = FastAPI(
    title="pdf redact",
    description="Privacy-preserving PDF redaction service with zero data retention",
    version="1.0.0",
)

@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """
    Middleware to inject rate limit headers into ALL responses
    Solves: Headers missing on 200/202 responses
    """
    response = await call_next(request)
    
    # Inject rate limit headers if available in request state
    if hasattr(request.state, 'rate_limit_remaining'):
        response.headers['X-RateLimit-Remaining'] = str(request.state.rate_limit_remaining)
    
    if hasattr(request.state, 'rate_limit_tier'):
        tier = request.state.rate_limit_tier
        response.headers['X-RateLimit-Tier'] = tier
        # Set limit based on tier
        limit = 50 if tier == "authenticated" else 5
        response.headers['X-RateLimit-Limit'] = str(limit)
    
    return response

ENVIRONMENT = os.getenv("ENVIROMENT" , "development")
IS_PRODUCTION = ENVIRONMENT == "production"

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response  = await call_next(request)
    if IS_PRODUCTION:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    csp_directives =[
        "default-src 'self'",                       
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net", 
        "img-src 'self' ",                       
        "font-src 'self' https://cdn.jsdelivr.net",   
        "connect-src 'self'",                        
        "frame-ancestors 'none'",                    
        "form-action 'self'"                     
    ] 
    response.headers['Content-Security-Policy'] = "; ".join(csp_directives)
    response.headers['X-Frame-Options'] = 'DENY' 
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'no-referrer'
    permissions_policy = [
        "camera=()",        
        "microphone=()",  
        "geolocation=()",   
        "payment=()"        
    ]
    response.headers['Permissions-Policy'] = ", ".join(permissions_policy)
    DANGEROUS_HEADERS = ['Server', 'X-Powered-By', 'X-AspNet-Version', 'X-AspNetMvc-Version']
    for header in DANGEROUS_HEADERS:
        if header in response.headers:
            del response.headers[header]

    return response

#app.state.limiter = limiter
#app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
#app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


def update_job_status(job_id: str, status: JobStatus, **kwargs):
    """Update job status and additional fields"""
    if job_id in jobs:
        jobs[job_id]["status"] = status
        jobs[job_id].update(kwargs)
        return True
    return False

def get_job(job_id: str):
    """Get job details or raise 404"""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return jobs[job_id]

@app.get("/")
async def root():
    return {
        "service": "Smart Document Redactor API",
        "version": "1.0.0",
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="ok",
        timestamp=datetime.utcnow(),
        queue_depth=len([j for j in jobs.values() if j["status"] == JobStatus.PENDING]),
        workers_active=1
    )

@app.post("/redact",
    response_model=RedactionJob,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload PDF for redaction",
    description="Upload a PDF document for PII redaction. Returns job ID for status tracking.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type or size"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    dependencies=[Depends(rate_limit_dependency)]
)
#@limiter.limit(RATE_LIMITS["anonymous"])
async def redact_document(request: Request,file: UploadFile = File(...)):
    validator = FileValidator(max_size_mb=10 , timeout_sec=30)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    try:
        content = await file.read()
        file_size = len(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )
    is_valid ,error = validator.validate_upload(content , file.filename)
    if not is_valid:
        logger.warning(f"File validation failed: {error} | Filename: {file.filename} | Size: {len(content)}")
        if "size" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=error
            )
        elif "traversal" in error.lower() or "invalid characters" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Security violation detected: Path traversal attempt blocked"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

    job_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    temp_dir = tempfile.mkdtemp(prefix=f"job_{job_id}_")
    input_path = os.path.join(temp_dir, "input.pdf")
    output_path = os.path.join(temp_dir, "output_redacted.pdf")
    with open(input_path, "wb") as f:
        f.write(content)
    task = redact_pdf_task.delay(input_path, output_path, job_id)
    jobs[job_id] = {
        "job_id": job_id,
        "task_id": task.id,  
        "status": JobStatus.PENDING,
        "created_at": created_at,
        "file_name": file.filename,
        "file_size": file_size,
        "temp_dir": temp_dir,
        "input_path": input_path,
        "output_path": output_path,
    }
    return RedactionJob(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=created_at,
        file_name=file.filename,
        file_size=file_size
    )

@app.get("/jobs/{job_id}", response_model=JobStatusResponse,
    summary="Get job status",description="Check the status of a redaction job using job ID",
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"}
    }
)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    job = jobs[job_id]
    task_id = job.get("task_id")
    if task_id:
        task_result = redact_pdf_task.AsyncResult(task_id)
        celery_state = task_result.state
        if celery_state == "PENDING":
            job["status"] = JobStatus.PENDING
        elif celery_state == "STARTED":
            job["status"] = JobStatus.PROCESSING
        elif celery_state == "SUCCESS":
            job["status"] = JobStatus.COMPLETED
            result = task_result.result
            if isinstance(result, dict):
                job["pii_detected"] = result.get("pii_detected")
                job["redactions_applied"] = result.get("redactions_applied")
                job["completed_at"] = datetime.utcnow()
        elif celery_state == "FAILURE":
            job["status"] = JobStatus.FAILED
            job["error"] = str(task_result.result)
            job["completed_at"] = datetime.utcnow()
    response = JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        completed_at=job.get("completed_at"),
        error=job.get("error"),
        pii_detected=job.get("pii_detected"),
        redactions_applied=job.get("redactions_applied")
    )
    if job["status"] == JobStatus.COMPLETED:
        response.download_url = f"/download/{job_id}"
    return response

    
@app.get("/download/{job_id}",summary="Download redacted PDF",
    description="Download the redacted PDF file",
    responses={
        404: {"model": ErrorResponse, "description": "Job not found or not completed"},
        400: {"model": ErrorResponse, "description": "Job failed or file not ready"}
    }
)
async def download_redacted(job_id: str):
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    job = jobs[job_id]
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job not completed (status: {job['status']})"
        )
    output_path = os.path.join(job["temp_dir"], "output_redacted.pdf")
    if not os.path.exists(output_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Redacted file not found"
        )
    return FileResponse(
        path=output_path,
        filename=f"redacted_{job['file_name']}",
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=redacted_{job['file_name']}"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )
'''''
@app.post("/debug/complete-job/{job_id}")
async def debug_complete_job(job_id: str, pii_count: int = 5, redactions: int = 5):
    """
    DEBUG ONLY: Force-complete a job for testing
    Simulates background processing completion
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create dummy redacted file
    job = jobs[job_id]
    output_path = os.path.join(job["temp_dir"], "output_redacted.pdf")
    
    # Copy input to output (simulating redaction)
    import shutil
    shutil.copy2(job["input_path"], output_path)
    
    # Update job status
    update_job_status(
        job_id,
        JobStatus.COMPLETED,
        completed_at=datetime.utcnow(),
        pii_detected=pii_count,
        redactions_applied=redactions
    )
    
    return {"status": "completed", "job_id": job_id, "output_path": output_path}
'''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)