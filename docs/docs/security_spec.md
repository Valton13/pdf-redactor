# Secure Redaction Specification v1.0

## Core Principle
> Redaction = **permanent content destruction**, not visual obscuration.  
> If data can be extracted via *any* method (copy-paste, metadata, OCR), redaction FAILED.

## Mandatory Requirements (ALL must PASS)

### 1. Content Layer Destruction
- [ ] **Text stream removal**: Original PII text *physically removed* from PDF content stream
  - Validation: `pdftotext redacted.pdf - | grep "gmail"` → **0 results**
  - Validation: Select text under redaction box → copies `XXXX` or nothing (not original PII)
- [ ] **Image layer sanitization**: Scanned/image-based PII requires OCR-aware redaction
  - Validation: Run Tesseract OCR on redacted PDF → no PII in output

### 2. Metadata Annihilation
- [ ] **Document Properties**: Author/Creator/Producer fields = blank or "Anonymous"
  - Validation: `exiftool redacted.pdf | grep -i "author\|creator"` → **no PII**
- [ ] **XMP Metadata**: All XML metadata stripped
  - Validation: `pdfinfo -meta redacted.pdf` → empty metadata section
- [ ] **Hidden annotations**: Comments/forms/attachments removed
  - Validation: Adobe Acrobat → Comments panel → **0 items**

### 3. Ephemeral Processing
- [ ] **Zero persistent storage**: Files exist ONLY in RAM/tmpfs during processing
  - Validation: `find / -name "*.pdf" 2>/dev/null` post-processing → **no user PDFs found**
- [ ] **Auto-delete guarantee**: All artifacts deleted within 5 minutes of job completion
  - Validation: Monitor `/tmp` → files vanish after TTL expiry

### 4. PII Detection Rigor
- [ ] **Confidence threshold**: Only redact entities with Presidio score ≥ 0.7
  - Rationale: Prevent over-redaction of false positives (e.g., "Apple" as company vs fruit)
- [ ] **Context-aware detection**: Distinguish "John" (name) vs "John" in "John Deere" (brand)
  - Validation: Test corpus item #4 (lease agreement) → "Premier Properties" NOT redacted

### 5. Attack Surface Hardening
- [ ] **File validation**: Reject non-PDFs via magic bytes (`%PDF-` header check)
  - Validation: Upload `.exe` renamed to `.pdf` → **rejected with 400 error**
- [ ] **Size enforcement**: Max 10MB per file (configurable)
  - Validation: Upload 11MB PDF → **rejected with 413 error**
- [ ] **Timeout enforcement**: 30-second max processing time per PDF
  - Validation: Malicious 1000-page PDF → **aborted after 30s with 408 error**

## ❌ Explicitly Out of Scope (v1.0)
- [ ] Handwritten document redaction (requires specialized OCR)
- [ ] Multi-language PII detection beyond English (Phase 2)
- [ ] Watermark removal (separate threat model)

## Validation Protocol
Every commit must pass:
```bash
./validate_redaction.sh test-corpus/01-resume.pdf