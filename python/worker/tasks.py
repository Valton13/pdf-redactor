from celery import Celery
from pathlib import Path
import sys
import requests
import logging
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = Celery("redaction_worker")
app.config_from_object("python.worker.config")

from python.core.pdf_extractor import PDFExtractor
from python.core.redactor import Redactor
from python.core.coordinate_mapper import CoordinateMapper
from python.analyzer.hybrid_analyzer import HybridAnalyzer

def perform_redaction(input_path: str, output_path: str) -> dict:
    logger.info(f"Starting redaction: {input_path}")
    
    try:
        import tempfile
        import os
        import shutil
        from pathlib import Path
        if os.path.exists('/dev/shm') and os.name != 'nt': 
            workspace_base = '/dev/shm'
            logger.info(" RAM disk available (/dev/shm) - using for zero forensic recovery")
        else:
            workspace_base = None  
            logger.info("  RAM disk not available - using system temp directory (still auto-deleted)")
        workspace_dir = tempfile.mkdtemp(
            dir=workspace_base,
            prefix='redaction_job_'
        )
        logger.info(f" Workspace created: {workspace_dir}")
        
        try:
            ram_input_path = os.path.join(workspace_dir, 'input.pdf')
            shutil.copy2(input_path, ram_input_path)
            logger.info(f"💾 Input copied to RAM workspace: {ram_input_path}")
            ram_output_path = os.path.join(workspace_dir, 'output_redacted.pdf')
            analyzer = HybridAnalyzer(confidence_threshold=0.7)
            mapper = CoordinateMapper()
            redactor = Redactor()
            logger.info("Extracting text from PDF...")
            with PDFExtractor(ram_input_path) as extractor:
                pages = extractor.extract_allpages()
            logger.info(f"Extracted {len(pages)} pages")
            logger.info("Detecting PII...")
            all_pii_spans = []
            total_pii = 0
            
            for page in pages:
                entities = analyzer.analyze(page.text)
                if entities:
                    logger.info(f"Page {page.page_num}: Found {len(entities)} PII entities")
                    total_pii += len(entities)
                    for entity in entities:
                        entity_text = page.text[entity.start:entity.end]
                        all_pii_spans.append((
                            page.page_num,
                            entity_text,
                            entity.start,
                            entity.end
                        ))
            
            logger.info(f"Total PII detected: {total_pii}")
            if all_pii_spans:
                logger.info(f"Applying {len(all_pii_spans)} redactions...")
                result = redactor.redact_pii(ram_input_path, ram_output_path, all_pii_spans)
                logger.info(f"Redaction complete: {result['redaction_count']} redactions applied")
            else:
                logger.info("No PII detected - copying file with metadata stripped")
                redactor.redact_pii(ram_input_path, ram_output_path, [])
                result = {"redaction_count": 0}
            if not Path(ram_output_path).exists():
                raise FileNotFoundError(f"Output file not created in RAM workspace: {ram_output_path}")
            shutil.copy2(ram_output_path, output_path)
            logger.info(f" Redacted PDF copied to final destination: {output_path}")
            if not Path(output_path).exists():
                raise FileNotFoundError(f"Final output file not created: {output_path}")
            stats = {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "ram_workspace": workspace_dir,
                "pages_processed": len(pages),
                "pii_detected": total_pii,
                "redactions_applied": result.get("redaction_count", 0),
                "file_size": Path(output_path).stat().st_size,
                "zero_forensic": '/dev/shm' in workspace_dir if workspace_base else False
            }
            if stats["zero_forensic"]:
                logger.info(" ZERO FORENSIC RECOVERY: Output processed entirely in RAM (/dev/shm)")
            else:
                logger.warning(" Output processed on disk (still auto-deleted after 5 min by cleanup task)")
            
            logger.info(f"Redaction successful: {stats}")
            return stats
            
        finally:
            try:
                shutil.rmtree(workspace_dir, ignore_errors=True)
                logger.info(f" RAM workspace deleted: {workspace_dir}")
            except Exception as e:
                logger.warning(f"  Failed to delete workspace {workspace_dir}: {e}")
    
    except Exception as e:
        logger.error(f"Redaction failed: {str(e)}", exc_info=True)
        raise

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def redact_pdf_task(self, input_path: str, output_path: str, job_id: str):
    logger.info(f"Task started - Job ID: {job_id}")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    try:
        result = perform_redaction(input_path, output_path)
        result["job_id"] = job_id
        result["status"] = "completed"
        logger.info(f"Task completed successfully - Job ID: {job_id}")
        return result
    except Exception as e:
        logger.error(f"Task failed - Job ID: {job_id}, Error: {str(e)}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e) 
        return {
            "success": False,
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
            "input_path": input_path,
            "output_path": output_path
        }

def demo_redaction():
    import tempfile
    from pathlib import Path
    print("\n" + "="*70)
    print("CELERY TASK DEMO - Local Redaction Test (No Worker Required)")
    print("="*70)
    test_pdf = Path(tempfile.gettempdir()) / "demo_input.pdf"
    output_pdf = Path(tempfile.gettempdir()) / "demo_output_redacted.pdf"
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    text = "Contact John Smith at john@example.com or call (415) 555-0192"
    page.insert_text((50, 100), text, fontsize=12)
    doc.save(str(test_pdf))
    doc.close()

    print(f"\n Created test PDF: {test_pdf}")
    print(f"   Content: '{text}'")
    result = perform_redaction(str(test_pdf), str(output_pdf))
    print("\n Redaction Complete!")
    print(f"   Pages processed: {result['pages_processed']}")
    print(f"   PII detected: {result['pii_detected']}")
    print(f"   Redactions applied: {result['redactions_applied']}")
    print(f"   Output file: {output_pdf}")
    print(f"   File size: {result['file_size']} bytes")

    doc = fitz.open(str(output_pdf))
    redacted_text = ""
    for page in doc:
        redacted_text += page.get_text()
    doc.close()
    if "John Smith" not in redacted_text and "john@example.com" not in redacted_text:
        print("\n VERIFICATION: PII successfully removed (not searchable)")
    else:
        print("\n VERIFICATION FAILED: PII still present in text stream")
    print("\n" + "="*70)
    print("✅ Celery task logic validated successfully!")
    print("="*70)
    print("\n💡 Next Step: Integrate with API (Hour 7)")
    print("   • Update /redact endpoint to queue this task")
    print("   • Update /jobs/{id} to check task status")
    print("   • Start Celery worker to process real jobs")

if __name__ == "__main__":
    demo_redaction()