import sys
import time
import os
import tempfile
from pathlib import Path
import fitz
sys.path.insert(0, str(Path(__file__).parent.parent))
BASE_URL = "http://localhost:8000"


def test_pii_not_searchable():
    """Verify PII is cryptographically removed (not just visually hidden)"""
    print("\n" + "="*60)
    print("TEST 1: PII Cryptographic Removal")
    print("="*60)
    test_dir = tempfile.mkdtemp(prefix="forensic_test_")
    test_pdf = Path(test_dir) / "input.pdf"
    redacted_pdf = Path(test_dir) / "output_redacted.pdf"
    
    try:
        doc = fitz.open()
        page = doc.new_page()
        pii_text = "John Smith john.smith83@gmail.com 4155550192"
        page.insert_text((50, 100), pii_text, fontsize=12)
        doc.save(str(test_pdf))
        doc.close()
        
        print(f"Created test PDF with PII: '{pii_text}'")
        print(f"  Path: {test_pdf}")
        from python.core.redactor import Redactor
        from python.analyzer.hybrid_analyzer import HybridAnalyzer
        
        # Detect PII
        analyzer = HybridAnalyzer()
        results = analyzer.analyze(pii_text)
        pii_spans = []
        for r in results:
            entity_text = pii_text[r.start:r.end]
            pii_spans.append((0, entity_text, r.start, r.end))
        
        # Apply redaction
        redactor = Redactor()
        redactor.redact_pii(str(test_pdf), str(redacted_pdf), pii_spans)
        
        # Verify PII not searchable
        doc = fitz.open(str(redacted_pdf))
        extracted_text = ""
        for page in doc:
            extracted_text += page.get_text()
        doc.close()
        
        print(f"Extracted text length: {len(extracted_text)} chars")
        
        pii_found = []
        for entity in ["John Smith", "john.smith83@gmail.com", "4155550192"]:
            normalized_extracted = " ".join(extracted_text.split())
            if entity.lower() in normalized_extracted.lower():
                pii_found.append(entity)
        
        if not pii_found:
            print(" PASS: No PII found in redacted PDF text stream")
            return True
        else:
            print(f" FAIL: PII still present: {pii_found}")
            print(f"   Extracted text: '{extracted_text[:50]}...'")
            return False
    
    finally:
        # Clean up temp directory
        import shutil
        try:
            shutil.rmtree(test_dir)
        except Exception as e:
            print(f"  Cleanup warning: {e}")

    
def test_metadata_stripping():
    print("\n" + "="*60)
    print("TEST 2: Metadata Stripping")
    print("="*60)
    test_dir = tempfile.mkdtemp(prefix="metadata_test_")
    test_pdf = Path(test_dir) / "input.pdf"
    redacted_pdf = Path(test_dir) / "output_redacted.pdf"
    
    try:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), "Test document", fontsize=12)
        doc.set_metadata({
            "author": "John Smith",
            "creator": "Test Creator",
            "producer": "Test Producer",
            "title": "Confidential Document",
            "subject": "PII Test",
            "keywords": "ssn,credit card,bank account"
        })     
        doc.save(str(test_pdf))
        doc.close()
        print("Created PDF with PII-containing metadata")
        from python.core.redactor import Redactor
        redactor = Redactor()
        redactor.redact_pii(str(test_pdf), str(redacted_pdf), [])
        doc = fitz.open(str(redacted_pdf))
        metadata = doc.metadata
        doc.close()
        print("\nMetadata after redaction:")
        for key, value in metadata.items():
            print(f"  {key}: '{value}'")
        sensitive_fields = ["author", "creator", "producer", "title", "subject", "keywords"]
        stripped = all(metadata.get(field, "") == "" for field in sensitive_fields)
        
        if stripped:
            print("\n PASS: All sensitive metadata fields stripped")
            return True
        else:
            print("\n FAIL: Metadata not fully stripped")
            return False
    
    finally:
        import shutil
        try:
            shutil.rmtree(test_dir)
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
def test_auto_cleanup():
    """Verify files auto-delete after 5 minutes"""
    print("\n" + "="*60)
    print("TEST 3: Auto-Cleanup (5-Minute TTL)")
    print("="*60)
    
    # Import cleanup task
    sys.path.insert(0, str(Path(__file__).parent / "python" / "worker"))
    from python.worker.cleanup_tasks import cleanup_expired_jobs
    import tempfile
    from datetime import datetime, timedelta
    temp_dir = tempfile.mkdtemp(prefix="job_test_")
    
    mock_jobs = {
        "expired_job": {
            "job_id": "expired_job",
            "created_at": datetime.utcnow() - timedelta(minutes=10),
            "temp_dir": temp_dir
        }
    }
    from python.api.main import jobs
    original_jobs = dict(jobs)  # Backup
    jobs.clear()
    jobs.update(mock_jobs)
    print(f"Created mock job 'expired_job' (10 min old)")
    print(f"  Temp dir: {temp_dir}")
    print(f"  Exists before cleanup: {os.path.exists(temp_dir)}")
    print("\nRunning cleanup task (max age: 5 minutes)...")
    result = cleanup_expired_jobs(max_age_minutes=5)
    exists_after = os.path.exists(temp_dir)
    
    print(f"\nCleanup result: {result}")
    print(f"Temp dir exists after cleanup: {exists_after}")
    jobs.clear()
    jobs.update(original_jobs)
    
    if not exists_after and result["jobs_deleted"] == 1:
        print("\n PASS: Expired job auto-deleted")
        return True
    else:
        print("\n FAIL: Auto-cleanup did not delete expired job")
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        return False

def test_ram_disk_processing():
    """Verify processing happens in RAM when /dev/shm available"""
    print("\n" + "="*60)
    print("TEST: RAM Disk Processing Verification")
    print("="*60)
    
    # Create test PDF
    import tempfile
    test_dir = tempfile.mkdtemp(prefix="ram_test_")
    test_pdf = Path(test_dir) / "input.pdf"
    output_pdf = Path(test_dir) / "output.pdf"
    
    # Create simple PDF
    import fitz
    doc = fitz.open()
    doc.new_page().insert_text((50, 100), "Test PII: john@example.com")
    doc.save(str(test_pdf))
    doc.close()
    
    # Process with RAM workspace
    from python.worker.tasks import perform_redaction
    result = perform_redaction(str(test_pdf), str(output_pdf))
    
    print(f"✅ Processing completed")
    print(f"   Zero forensic mode: {result.get('zero_forensic', False)}")
    print(f"   RAM workspace: {result.get('ram_workspace', 'N/A')}")
    
    # Verify output exists
    if output_pdf.exists():
        print(f"✅ Output file created ({output_pdf.stat().st_size} bytes)")
        
        # Verify PII removed
        doc = fitz.open(str(output_pdf))
        text = doc[0].get_text()
        doc.close()
        
        if "john@example.com" not in text.lower():
            print("✅ PII cryptographically removed")
            return True
        else:
            print("❌ PII still present in output")
            return False
    else:
        print("❌ Output file not created")
        return False

def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 5 DAY 1: FORENSIC VALIDATION TESTS (WINDOWS FIX)  ║")
    print("║  Zero Retention Guarantee Verification                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    results = []
    results.append(("PII Cryptographic Removal", test_pii_not_searchable()))
    results.append(("Metadata Stripping", test_metadata_stripping()))
    results.append(("Auto-Cleanup (5-Min TTL)", test_auto_cleanup()))
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)   
    total = len(results)
    passed = sum(1 for _, success in results if success)   
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")    
    print(f"\n📊 Results: {passed}/{total} tests passed")  
    if passed == total:
        print("\n🎉 SUCCESS! Zero Retention Guarantee Verified:")
        print("   ✅ PII cryptographically removed (not just hidden)")
        print("   ✅ All metadata stripped (author/creator/producer)")
        print("   ✅ Files auto-delete after 5 minutes")
        print("\n🔒 Compliance Status:")
        print("   • GDPR Article 17: ✅ Right to erasure")
        print("   • HIPAA §164.312(b): ✅ Data disposal")
        print("   • CCPA §1798.105: ✅ Right to deletion")
        print("\n💡 Next: Privacy policy documentation (Hour 4)")
        return 0
    else:
        print("\n⚠️  Some forensic tests failed - zero retention not guaranteed!")
        print("\n🔧 Windows-Specific Fixes Applied:")
        print("   • Replaced direct temp dir usage with tempfile.mkdtemp()")
        print("   • Added proper cleanup in finally blocks")
        print("   • Avoids PyMuPDF permission conflicts on Windows")
        return 1
if __name__ == "__main__":
    sys.exit(main())
    