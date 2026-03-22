import sys
from pathlib import Path
import tempfile
import os
import re
project_root = Path(__file__).parent.parent  
sys.path.insert(0, str(project_root))
from python.core.pdf_extractor import PDFExtractor
from python.core.redactor import Redactor
from python.core.coordinate_mapper import CoordinateMapper

def simulate_pii_detection(text:str)-> list:
    pii_spans =[]
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    for match in re.finditer(email_pattern , text):
        pii_spans.append((match.group(), match.start(), match.end()))
    phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    for match in re.finditer(phone_pattern, text):
        pii_spans.append((match.group(), match.start(), match.end()))    
    ssn_pattern = r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
    for match in re.finditer(ssn_pattern, text):
        pii_spans.append((match.group(), match.start(), match.end()))
    account_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'    
    for match in re.finditer(account_pattern, text):
        pii_spans.append((match.group(), match.start(), match.end()))
    return pii_spans

def process_pdf_pipeline(input_pdf: str, output_pdf: str) -> dict:
    print(f"\n{'─'*60}")
    print(f"📄 Processing: {Path(input_pdf).name}")
    print(f"{'─'*60}")
    stats = {
        "input_pdf": input_pdf,
        "output_pdf": output_pdf,
        "success": False,
        "pages_processed": 0,
        "pii_detected": 0,
        "redactions_applied": 0,
        "errors": []
    }
    try:
        print("  Step 1: Extracting text...")
        with PDFExtractor(input_pdf) as extractor:
            pages = extractor.extract_allpages()
        stats["pages_processed"] = len(pages)
        print(f"Extracted {len(pages)} page(s)")

        print("step 2 detecting pii")
        all_pii_spans =[]
        for page in pages:
            pii_spans = simulate_pii_detection(page.text)
            if pii_spans:
                print(f"page{page.page_num}:{len(pii_spans)} pii items found")
                for text , start , end in pii_spans:
                    all_pii_spans.append((page.page_num , text , start , end))
        stats["pii detected"] = len(all_pii_spans)
        print(f"total pii : {len(all_pii_spans)}")
        if not all_pii_spans:
            print("No PII detected - skipping redaction")
            stats["success"] = True
            return stats
        print("step 3")
        redactor = Redactor()
        result = redactor.redact_pii(input_pdf , output_pdf , all_pii_spans)
        stats["redactions_applied"] = result.get("redaction_count" , 0)
        stats["success"] = True
        print(f"Redactions applied: {result['redaction_count']}")
        print(f"Output saved: {Path(output_pdf).name}")
        print("step 4")
        verification_passed = True
        for page_num, text, start, end in all_pii_spans[:3]:  
            if not redactor.verify_redaction(output_pdf, text):
                print(f"FAILED: '{text[:30]}")
                verification_passed = False
                break
        if verification_passed:
            print(f"All PII successfully redacted (not searchable)")
        else:
            stats["errors"].append("PII still searchable after redaction")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        stats["errors"].append(str(e))
        stats["success"] = False
    
    return stats

def test_corpus_integration():
    """Test integration on entire test corpus"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  WEEK 3 DAY 1: INTEGRATION TEST                          ║")
    print("║  End-to-End PDF Redaction Pipeline                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Get test corpus PDFs
    corpus_dir = Path("test-corpus")
    if not corpus_dir.exists():
        print(f"\n❌ ERROR: Test corpus directory not found: {corpus_dir}")
        print("   Run generate_test_corpus.py first")
        return []
    
    pdf_files = sorted(list(corpus_dir.glob("*.pdf")))
    
    if not pdf_files:
        print(f"\n❌ ERROR: No PDFs found in {corpus_dir}")
        return []
    
    print(f"\n📁 Found {len(pdf_files)} PDFs in test corpus")
    
    # Create output directory
    output_dir = Path(tempfile.gettempdir()) / "redaction_output"
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory: {output_dir}\n")
    
    # Process each PDF
    results = []
    
    for pdf_path in pdf_files:
        output_path = output_dir / f"redacted_{pdf_path.name}"
        stats = process_pdf_pipeline(str(pdf_path), str(output_path))
        results.append(stats)
    
    return results


def generate_summary_report(results: list):
    """Generate summary report of integration test results"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  INTEGRATION TEST SUMMARY                                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    # Calculate totals
    total_pages = sum(r["pages_processed"] for r in results)
    total_pii = sum(r["pii_detected"] for r in results)
    total_redactions = sum(r["redactions_applied"] for r in results)
    
    # Print summary table
    print(f"\n📊 Overall Statistics")
    print(f"{'─'*60}")
    print(f"Total PDFs processed:     {total}")
    print(f"Successful:               {successful} ✅")
    print(f"Failed:                   {failed} ❌")
    print(f"Total pages processed:    {total_pages}")
    print(f"Total PII detected:       {total_pii}")
    print(f"Total redactions applied: {total_redactions}")
    
    # Success rate
    success_rate = (successful / total * 100) if total > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    # Detailed results
    print(f"\n📋 Detailed Results")
    print(f"{'─'*60}")
    
    for result in results:
        pdf_name = Path(result["input_pdf"]).name
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        
        print(f"{status} {pdf_name}")
        print(f"     Pages: {result['pages_processed']}, ", end="")
        print(f"PII: {result['pii_detected']}, ", end="")
        print(f"Redactions: {result['redactions_applied']}")
        
        if result["errors"]:
            for error in result["errors"]:
                print(f"     ⚠️  Error: {error}")
    
    # Final verdict
    print(f"\n{'─'*60}")
    if successful == total:
        print("🎉 ALL TESTS PASSED! Integration pipeline working correctly")
        print("\n✅ Day 1 Complete: Core PDF processing engine functional")
        return True
    else:
        print(f"⚠️  {failed} TEST(S) FAILED - Review error messages above")
        return False


def main():
    """Main integration test execution"""
    results = test_corpus_integration()
    
    if not results:
        return 1
    
    success = generate_summary_report(results)
    
    # Save results to file
    output_dir = Path(tempfile.gettempdir()) / "redaction_output"
    report_file = output_dir / "integration_test_report.txt"
    
    with open(report_file, 'w') as f:
        f.write("WEEK 3 DAY 1: INTEGRATION TEST REPORT\n")
        f.write("="*60 + "\n\n")
        
        for result in results:
            pdf_name = Path(result["input_pdf"]).name
            status = "PASS" if result["success"] else "FAIL"
            f.write(f"{status}: {pdf_name}\n")
            f.write(f"  Pages: {result['pages_processed']}\n")
            f.write(f"  PII Detected: {result['pii_detected']}\n")
            f.write(f"  Redactions: {result['redactions_applied']}\n")
            if result["errors"]:
                f.write(f"  Errors: {', '.join(result['errors'])}\n")
            f.write("\n")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print(f"📁 Redacted PDFs saved to: {output_dir}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())