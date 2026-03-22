from pydantic import BaseModel , Field
from typing import Optional , List
from datetime import datetime
from enum import Enum

class JobStatus(str ,Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class RedactionJob(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")

class JobStatusResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    download_url: Optional[str] = Field(None, description="URL to download redacted PDF")
    error: Optional[str] = Field(None, description="Error message if job failed")
    pii_detected: Optional[int] = Field(None, description="Number of PII entities detected")
    redactions_applied: Optional[int] = Field(None, description="Number of redactions applied")

class HealthCheck(BaseModel):
    status: str = Field("ok", description="Service status")
    version: str = Field("1.0.0", description="API version")
    timestamp: datetime = Field(..., description="Current server time")
    queue_depth: int = Field(0, description="Number of pending jobs")
    workers_active: int = Field(1, description="Number of active workers")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")