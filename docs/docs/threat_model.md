
---

### 🛡️ Deliverable 2: `docs/threat_model.md` (25 mins)

Create this file using **STRIDE framework** — Microsoft's industry-standard threat modeling method:

```markdown
# Threat Model: Smart Document Redactor (STRIDE Analysis)

| Threat ID | STRIDE Category | Threat Scenario | Impact | Mitigation | Verification |
|-----------|-----------------|-----------------|--------|------------|--------------|
| **T01** | **S**poofing | Attacker uploads malware disguised as PDF | High (RCE) | Magic bytes validation (`%PDF-` header) + file extension check | Fuzz test with `.exe` renamed to `.pdf` |
| **T02** | **T**ampering | Attacker modifies PDF to bypass redaction (e.g., hidden layers) | Critical (PII leak) | Parse ALL PDF objects (not just visible layers) using PyMuPDF | Test with PDF containing hidden text layers |
| **T03** | **R**epudiation | User claims "you stored my data" after redaction | Medium (legal) | Zero persistent storage + audit log (job_id only, no content) | Log analysis: verify no PII in logs |
| **T04** | **I**nformation Disclosure | PII leakage via:<br>• Metadata (XMP/Properties)<br>• Hidden text streams<br>• Temporary files | Critical (GDPR fine) | 1. Strip ALL metadata<br>2. Cryptographic redaction (`redact=True`)<br>3. tmpfs-only storage | Forensic analysis with `pdfid.py` + `exiftool` |
| **T05** | **D**enial of Service | 100MB PDF or 1000-page PDF crashes worker | Medium (availability) | 1. 10MB size limit<br>2. 30s timeout per job<br>3. Worker isolation (1 job/worker) | Load test with oversized PDFs |
| **T06** | **E**levation of Privilege | Path traversal via filename (`../../../etc/passwd`) | High (data breach) | Sanitize filenames → UUID only (`job_abc123.pdf`) | Test upload with `../../malicious.pdf` filename |

## Critical Threats Requiring Architectural Mitigation
| Threat | Why Standard Libraries Fail | Our Solution |
|--------|----------------------------|--------------|
| **T04 (Metadata leak)** | PyPDF2/pdfplumber preserve metadata by default | PyMuPDF: `doc.set_metadata({})` + `doc.del_xml_metadata()` |
| **T02 (Hidden layers)** | Simple text extractors miss occluded content | PyMuPDF: `page.get_text("dict")` parses ALL text objects |
| **T05 (DoS)** | No timeout → worker starvation | Celery task timeout + Redis queue depth monitoring |

## Residual Risk Acceptance
| Risk | Acceptance Rationale | Owner |
|------|----------------------|-------|
| Image-based PII (scanned docs) | OCR redaction requires separate pipeline; out of scope v1.0 | Product |
| Non-English PII | Presidio English model covers 95% of use cases; multi-lang Phase 2 | Engineering |