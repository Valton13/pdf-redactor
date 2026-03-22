import time
import fitz
import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract
from  tabulate import tabulate
import sys

PDFS =[
    "test-corpus/01-resume.pdf",
    "test-corpus/02-bank-statement.pdf",
    "test-corpus/03-medical-form.pdf",
    "test-corpus/04-lease-agreement.pdf", 
    "test-corpus/05-w9-tax-form.pdf",
]

def benchmark_pymupdf(pdf_path):
    try:
        start = time.time()
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        elapsed  = time.time() - start
        doc.close()
        return len(text) , elapsed ,True
    except Exception as e:
        return 0,0,False
    
def benchmark_pdfplumber(pdf_path):
    try:
        start = time.time()
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
        elapsed = time.time() - start
        return len(text) , elapsed , True
    except Exception as e:
        return 0,0,False

def benchmark_pdfminer(pdf_path):
    try:
        start = time.time()
        text = pdfminer_extract(pdf_path)
        elapsed = time.time() - start
        return len(text) , elapsed ,True
    except Exception as e:
        return 0,0,False

def run_benchmarks():
    results = []
    total_pymupdf_time = 0
    total_pdfplumber_time = 0
    total_pdfminer_time = 0
    print("=" * 100)
    print("PDF LIBRARY BENCHMARK")
    print("=" * 100)
    for pdf_path in PDFS:
        print(f"\nTesting : {pdf_path}")
        pymupdf_chars, pymupdf_time, pymupdf_success = benchmark_pymupdf(pdf_path)
        total_pymupdf_time += pymupdf_time
        pdfplumber_chars, pdfplumber_time, pdfplumber_success = benchmark_pdfplumber(pdf_path)
        total_pdfplumber_time += pdfplumber_time
        pdfminer_chars, pdfminer_time, pdfminer_success = benchmark_pdfminer(pdf_path)
        total_pdfminer_time += pdfminer_time
        pymupdf_result = f"{pymupdf_chars:,} chars / {pymupdf_time:.3f}s" if pymupdf_success else "❌ FAIL"
        pdfplumber_result = f"{pdfplumber_chars:,} chars / {pdfplumber_time:.3f}s" if pdfplumber_success else "❌ FAIL"
        pdfminer_result = f"{pdfminer_chars:,} chars / {pdfminer_time:.3f}s" if pdfminer_success else "❌ FAIL"
        
        results.append([
            pdf_path.split("/")[-1],
            pymupdf_result,
            pdfplumber_result,
            pdfminer_result
        ])
    print("\n" + "=" * 100)
    print("BENCHMARK RESULTS")
    print("=" * 100)
    print(tabulate(results, headers=[
        "PDF File",
        "PyMuPDF (fitz)",
        "pdfplumber",
        "pdfminer.six"
    ], tablefmt="grid"))
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"PyMuPDF total time: {total_pymupdf_time:.3f}s")
    print(f"pdfplumber total time: {total_pdfplumber_time:.3f}s")
    print(f"pdfminer.six total time: {total_pdfminer_time:.3f}s")
    print(f"\nPyMuPDF is {total_pdfplumber_time/total_pymupdf_time:.1f}x faster than pdfplumber")
    print(f"PyMuPDF is {total_pdfminer_time/total_pymupdf_time:.1f}x faster than pdfminer.six")
    print("=" * 100) 
    return results
if __name__ == "__main__":
    results = run_benchmarks()
