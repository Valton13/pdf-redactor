import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from python.analyzer.hybrid_analyzer import HybridAnalyzer
from python.core.redactor import Redactor
from python.core.pdf_extractor import PDFExtractor
import tempfile

def detect_pii_with_hybrid_analyzer(text: str) -> list:
    analyzer = HybridAnalyzer(confidence_threshold=0.7)
    results = analyzer.analyze(text)
    return [(text[r.start:r.end], r.start, r.end) for r in results]

def process_pdf(input_pdf: str, output_pdf: str) -> dict:
    stats = {"success": False, "pii_detected": 0, "redactions": 0}
    try:
        with PDFExtractor(input_pdf) as extractor:
            pages = extractor.extract_allpages()
        all_pii = []
        for page in pages:
            pii_spans = detect_pii_with_hybrid_analyzer(page.text)
            for text , start , end in pii_spans:
                all_pii.append((page.page_num , text ,start,end))
        stats["pii detected"] = len(all_pii)
        if all_pii:
            redactor = Redactor()
            result = redactor.redact_pii(input_pdf,output_pdf  ,all_pii)
            stats["redactions"] = result.get("redaction_count" , 0)
        stats["success"] = True
        return stats
    except Exception as e:
        print(f"Error: {e}")
        return stats

def main():
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  INTEGRATION TEST: PDF REDACTION PIPELINE               ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    # Test on 3 representative PDFs
    test_pdfs = [
        "test-corpus/01-resume.pdf",
        "test-corpus/02-bank-statement.pdf",
        "test-corpus/05-w9-tax-form.pdf",
       # "test-corpus/SKGBWX_UPN_33748818.pdf"
    ]
    
    output_dir = Path(tempfile.gettempdir()) / "redaction_test"
    output_dir.mkdir(exist_ok=True)
    
    results = []
    for pdf_path in test_pdfs:
        if not Path(pdf_path).exists():
            continue
            
        print(f"📄 {Path(pdf_path).name}")
        output_path = output_dir / f"redacted_{Path(pdf_path).name}"
        stats = process_pdf(pdf_path, str(output_path))
        
        if stats["success"]:
            print(f"  ✅ PII: {stats['pii_detected']}, Redactions: {stats['redactions']}")
            results.append(True)
        else:
            print(f"  ❌ Failed")
            results.append(False)
    
    # Summary
    print(f"\n{'─'*60}")
    passed = sum(results)
    total = len(results)
    print(f"📊 Results: {passed}/{total} PDFs processed successfully")
    
    if passed == total:
        print("🎉 SUCCESS! Integration pipeline working")
        print(f"📁 Output: {output_dir}")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
