import fitz
import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract

EDGE_CASE_PDFS =  [
    "test-corpus/06-passport-scan.pdf",      # Scanned/image-heavy
    "test-corpus/09-insurance-claim.pdf",    # Multi-column layout
    "test-corpus/02-bank-statement.pdf", 
    "test-corpus/passport.pdf"
]

def test_library(name , test_func):
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"{'='*60}")
    for pdf_path in EDGE_CASE_PDFS:
        print(f"\n  {pdf_path.split('/')[-1]}:")
        try:
            result = test_func(pdf_path)
            print(f"    ✅ Success - {result}")
        except Exception as e:
            print(f"    ❌ Failed - {str(e)[:50]}")

def test_pymupdf(pdf_path): 
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return f"{len(text)} char extracted"

def test_pdfplumber(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
    return f"{len(text)} chars extracted"

def test_pdfminer(pdf_path):
    text = pdfminer_extract(pdf_path)
    return f"{len(text)} chars extracted"

if __name__ == "__main__":
    print("\n edge case testing")
    print("=" *60)
    test_library("PyMuPDF", test_pymupdf)
    test_library("pdfplumber", test_pdfplumber)
    test_library("pdfminer.six", test_pdfminer)
