import sys
import time
import requests
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

def upload_pdf():
    print("\n" + "="*60)
    print("STEP 1: Upload PDF")
    print("="*60)
    pdf_path = "test-corpus/03-medical-form.pdf"
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/redact", files=files)
    print(f"Status: {response.status_code}")
    if response.status_code == 202:
        data = response.json()
        print(f" Job created: {data['job_id']}")
        print(f"   Status: {data['status']}")
        print(f"   File: {data['file_name']}")
        return data['job_id']
    else:
        print(f" Upload failed: {response.json()}")
        return None
    
def poll_job_status(job_id: str, max_attempts: int = 30):
    print("\n" + "="*60)
    print("STEP 2: Poll Job Status")
    print("="*60)
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            print(f"Attempt {attempt + 1}/{max_attempts}: Status = {status}")
            if status == 'completed':
                print(f"\n Job completed!")
                print(f"   PII detected: {data.get('pii_detected')}")
                print(f"   Redactions: {data.get('redactions_applied')}")
                print(f"   Download URL: {data.get('download_url')}")
                return True
            elif status == 'failed':
                    print(f"\n Job failed: {data.get('error')}")
                    return False
        time.sleep(2)
    print(f"\n Timeout: Job still processing after {max_attempts} attempts")
    return False

def download_redacted_pdf(job_id: str):
    print("\n" + "="*60)
    print("STEP 3: Download Redacted PDF")
    print("="*60)
    response = requests.get(f"{BASE_URL}/download/{job_id}")
    if response.status_code == 200:
        import tempfile
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"redacted_{job_id}.pdf")
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f" Downloaded: {output_path}")
        print(f"   Size: {len(response.content)} bytes")
        if os.path.exists(output_path):
            print(f" File verified on disk")
            return True
        else:
            print(f" File not found after download")
            return False
    else:
        print(f" Download failed: {response.status_code}")
        print(f"   Error: {response.json()}")
        return False
        
def main():
    """Run complete async workflow test"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 4 DAY 2: END-TO-END ASYNC WORKFLOW TEST           ║")
    print("║  Upload → Queue → Process → Download                    ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    print("\  PREREQUISITES:")
    print("   1. FastAPI server running: uvicorn python.api.main:app --reload")
    print("   2. Celery worker running: celery -A python.worker.tasks worker --loglevel=info --pool=solo")
    print("   3. Redis/Upstash accessible")
    input("\nPress Enter when both server and worker are running...")
    job_id = upload_pdf()
    if not job_id:
        print("\n FAILED: Upload step")
        return 1
    completed = poll_job_status(job_id)
    if not completed:
        print("\n FAILED: Processing step")
        return 1
    downloaded = download_redacted_pdf(job_id)
    if not downloaded:
        print("\n FAILED: Download step")
        return 1
    print("\n" + "="*60)
    print(" SUCCESS! Complete async workflow validated")
    print("="*60)
    print("\n Pipeline working:")
    print("   1. Upload → Job created (non-blocking)")
    print("   2. Queue → Celery task queued to Redis")
    print("   3. Process → Worker executed redaction")
    print("   4. Status → Job status updated automatically")
    print("   5. Download → Redacted PDF served")
    print("\n Next: Commit to GitHub (Hour 8)")
    return 0

if __name__ == "__main__":
    sys.exit(main())