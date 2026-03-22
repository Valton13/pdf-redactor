import sys
from pathlib import Path
project_root = Path(__file__).parent.parent  
sys.path.insert(0, str(project_root))


from python.core.pdf_extractor import PDFExtractor


def test_single_pdf(pdf_path: str):
    """Test extraction on a single PDF"""
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_path}")
    print(f"{'='*60}")
    
    try:
        with PDFExtractor(pdf_path) as extractor:                                  
            page_count = extractor.get_pagecount()
            print(f" PDF opened successfully")
            print(f"Total pages: {page_count}")
            pages = extractor.extract_allpages()
            print(f" Extracted {len(pages)} pages")
            if pages:
                first_page = pages[0]
                print(f"\n--- Page {first_page.page_num} Preview ---")
                print(f"Text length: {len(first_page.text)} characters")
                print(f"First 200 characters:\n{first_page.text[:200]}")
                block_count = len(first_page.blocks)
                print(f"\n Block data extracted: {block_count} blocks")
                if block_count > 0 and 'lines' in first_page.blocks[0]:
                    first_block = first_page.blocks[0]
                    print(f"First block type: {first_block.get('type', 'unknown')}")
                    if 'lines' in first_block and len(first_block['lines']) > 0:
                        first_line = first_block['lines'][0]
                        if 'spans' in first_line and len(first_line['spans']) > 0:
                            span_text = first_line['spans'][0].get('text', '')[:50]
                            print(f"First text span: '{span_text}...'")
            
            return True
            
    except Exception as e:
        print(f" Error: {str(e)}")
        return False


def main():
    test_pdfs = [
        "test-corpus/01-resume.pdf",
        "test-corpus/02-bank-statement.pdf",
        "test-corpus/05-w9-tax-form.pdf",
    ]
    
    results = []
    
    for pdf_path in test_pdfs:
        if Path(pdf_path).exists():
            success = test_single_pdf(pdf_path)
            results.append((pdf_path, success))
        else:
            print(f"\n  File not found: {pdf_path}")
            results.append((pdf_path, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for pdf, success in results:
        status = " PASS" if success else " FAIL"
        print(f"{status}: {pdf.split('/')[-1]}")
    
    print(f"\n Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n SUCCESS! PDF extraction engine working correctly")
        return 0
    else:
        print("\n  Some tests failed - check error messages above")
        return 1


if __name__ == "__main__":
    sys.exit(main())