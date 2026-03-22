#!/usr/bin/env python3
"""Verify all libraries installed correctly after PC reset"""

def verify():
    checks = [
        ("PyMuPDF", "import fitz"),
        ("pdfplumber", "import pdfplumber"),
        ("pdfminer.six", "from pdfminer.high_level import extract_text"),
        ("tabulate", "import tabulate"),
        ("Presidio", "from presidio_analyzer import AnalyzerEngine"),
        ("spaCy", "import spacy; spacy.load('en_core_web_lg')"),
        ("FastAPI", "import fastapi"),
        ("Uvicorn", "import uvicorn"),
        ("Pydantic", "import pydantic"),
        ("Celery", "import celery"),
        ("Redis", "import redis"),
        ("Requests", "import requests"),
        ("Pytest", "import pytest"),
        ("Structlog", "import structlog"),
        ("ReportLab", "import reportlab"),
    ]
    
    print("\n" + "="*70)
    print("POST-RESET INSTALLATION VERIFICATION")
    print("="*70 + "\n")
    
    all_ok = True
    for name, stmt in checks:
        try:
            exec(stmt)
            print(f"✅ {name:25s} OK")
        except Exception as e:
            print(f"❌ {name:25s} FAILED: {type(e).__name__}")
            all_ok = False
    
    print("\n" + "="*70)
    if all_ok:
        print("🎉 SUCCESS! All libraries installed correctly")
        print("\n✅ Next steps:")
        print("   1. Configure Upstash Redis URL in python/worker/config.py")
        print("   2. Run: python test_install.py (optional verification)")
        print("   3. Start services:")
        print("      • Terminal 1: uvicorn python.api.main:app --reload")
        print("      • Terminal 2: celery -A python.worker.tasks worker --loglevel=info --pool=solo")
    else:
        print("⚠️  SOME LIBRARIES FAILED - Reinstall missing packages")
    print("="*70 + "\n")
    
    return all_ok

if __name__ == "__main__":
    import sys
    sys.exit(0 if verify() else 1)