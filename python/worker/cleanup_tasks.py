from celery import Celery
from datetime import datetime , timedelta
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

app = Celery("cleanup_worker")
app.config_from_object("python.worker.config")

from python.api.main import jobs

@app.task(name="cleanup_expired_jobs")
def cleanup_expired_jobs(max_age_minutes: int = 5):
    now = datetime.utcnow()
    max_age = timedelta(minutes=max_age_minutes)
    deleted_jobs = []
    deleted_files = 0
    errors = []
    print(f"[CLEANUP] Starting cleanup (max age: {max_age_minutes} min)...")
    for job_id in list(jobs.keys()):
        job = jobs[job_id]
        created_at = job.get("created_at")
        if not created_at:
            continue
        age = now - created_at
        if age > max_age:
            print(f"[CLEANUP] Deleting expired job: {job_id} (age: {age.total_seconds():.0f}s)")
            temp_dir = job.get("temp_dir")
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    deleted_files += 1
                    print(f"Deleted temp dir: {temp_dir}")
                except Exception as e:
                    errors.append(f"Failed to delete {temp_dir}: {str(e)}")
                    print(f"ERROR: {e}")
            del jobs[job_id]
            deleted_jobs.append(job_id)
    stats= {
        "success": True,
        "timestamp": now.isoformat(),
        "max_age_minutes": max_age_minutes,
        "jobs_deleted": len(deleted_jobs),
        "files_deleted": deleted_files,
        "errors": errors,
        "remaining_jobs": len(jobs)
    }
    print(f"[CLEANUP] Complete: {len(deleted_jobs)} jobs deleted, {deleted_files} files removed")
    print(f"  Remaining jobs: {len(jobs)}")
    if errors:
        print(f"  Errors: {len(errors)}")
    return stats

def demo_cleanup():
    import tempfile
    from datetime import timedelta , datetime
    print("\n" + "="*70)
    print("AUTO-CLEANUP DEMO - Zero Retention Enforcement")
    print("="*70)
    mock_jobs = {
        "recent_job": {
            "job_id": "recent_job",
            "created_at": datetime.utcnow(),
            "temp_dir": tempfile.mkdtemp(prefix="job_recent_")
        },
        "expired_job": {
            "job_id": "expired_job",
            "created_at": datetime.utcnow() - timedelta(minutes=10),  
            "temp_dir": tempfile.mkdtemp(prefix="job_expired_")
        }
    }
    print(f"\n Created mock jobs:")
    print(f"recent_job: created now (should NOT be deleted)")
    print(f"expired_job: created 10 min ago (should be DELETED)")
    print("\n Running cleanup (max age: 5 minutes)...")
    now = datetime.utcnow()
    max_age = timedelta(minutes=5)
    deleted = []
    for job_id , job in list(mock_jobs.items()):
        age = now-job["created_at"]
        if age  >max_age:
            print(f"Deleting {job_id} (age: {age.total_seconds()/60:.1f} min)")
            if os.path.exists(job["temp_dir"]):
                shutil.rmtree(job["temp_dir"])
            deleted.append(job_id)
        else:
            print(f"Keeping {job_id} (age: {age.total_seconds()/60:.1f} min)")
    for job_id in deleted:
            exists = os.path.exists(mock_jobs[job_id]["temp_dir"])
            status = "FAILED" if exists else " SUCCESS"
            print(f"{status}: {job_id} temp dir deleted")
    print("   • All files auto-deleted after 5 minutes Sucessssss")

if __name__ == "__main__":
    demo_cleanup()
