import fitz  
from typing import List, Tuple, Optional
from pathlib import Path
import tempfile
import os

class Redactor:
    def __init__(self):
        pass
    '''''
    def redact_pii(self , input_path : str , output_path : str , pii_spans: List[Tuple[int, str, int, int]],
        redact_color: Tuple[float, float, float] = (0, 0, 0)) -> dict:
        doc  =fitz.open(input_path)
        redaction_count = 0
        pages_with_redactions = set()
        spans_by_pages = {}
        for page_num , text , start , end in pii_spans:
            if page_num not in spans_by_pages:
                spans_by_pages[page_num] =[]
            spans_by_pages[page_num].append((text , start ,end))
        for page_num , spans in spans_by_pages.items():
            if page_num >= len(doc):
                continue
            page = doc[page_num]
            for text , start ,end in spans:
                quads = page.search_for(text)
                if quads:
                    for quad in quads:
                        page.add_redact_annot(quad , fill = redact_color)
                        redaction_count +=1
                    pages_with_redactions.add(page_num)
            page.apply_redactions()
        self._strip_metadata(doc)
        doc.save(
            output_path , garbage = 4 , deflate=True , clean=True
        )
        doc.close()
        return {
            "success": True,
            "redaction_count": redaction_count,
            "pages_redacted": len(pages_with_redactions),
            "output_path": output_path
        }
   '''
    def redact_pii(
    self,
    input_path: str,
    output_path: str,
    pii_spans: List[Tuple[int, str, int, int]],
    redact_color: Tuple[float, float, float] = (0, 0, 0)
    ) -> dict:
        
   
    # DEBUG: Print what we received
        print(f"    DEBUG: redact_pii called with {len(pii_spans)} PII span(s)")
        print(f"    DEBUG: First span: {pii_spans[0] if pii_spans else 'N/A'}")
    
    # Open PDF
        doc = fitz.open(input_path)
    
        redaction_count = 0
        pages_with_redactions = set()
    
    # Group PII spans by page
        spans_by_page = {}
        for page_num, text, start, end in pii_spans:
            if page_num not in spans_by_page:
                spans_by_page[page_num] = []
            spans_by_page[page_num].append((text, start, end))
    
    # Apply redactions per page
        for page_num, spans in spans_by_page.items():
            if page_num >= len(doc):
                continue
        
            page = doc[page_num]
        
        # Redact each PII span
            for text, start, end in spans:
            # Search for text and get rectangles
                quads = page.search_for(text)
            
                if quads:
                # Add redaction annotation for each rectangle
                    for quad in quads:
                        page.add_redact_annot(quad, fill=redact_color)
                        redaction_count += 1
                
                    pages_with_redactions.add(page_num)
        
        # Apply all redactions on this page
            page.apply_redactions()
    
    # Strip metadata
        self._strip_metadata(doc)
    
    # Save redacted PDF with compression
        doc.save(
            output_path,
            garbage=4,      # Remove unused objects
            deflate=True,   # Compress streams
            clean=True      # Clean up document structure
        )
        doc.close()
    
        return {
            "success": True,
            "redaction_count": redaction_count,
            "pages_redacted": len(pages_with_redactions),
            "output_path": output_path
        }
    

    
    def _strip_metadata(self,doc:fitz.Document) -> None:
        current_meta = doc.metadata.copy() if doc.metadata else {}
        pii_fields = ['author', 'creator', 'producer', 'title', 'subject', 'keywords']
        for field in pii_fields:
            if field in current_meta:
                current_meta[field] = ""
        STANDARD_KEYS = {
        'author', 'creator', 'producer', 
        'title', 'subject', 'keywords',
        'creationDate', 'modDate'  }     
        clean_metadata = {
        k: v for k, v in current_meta.items() 
        if k in STANDARD_KEYS 
        }   
        doc.set_metadata(clean_metadata)
        try:
            doc.del_xml_metadata()
        except Exception:
            pass

    def redact_save_to_tmp( self , input_path : str ,pii_spans: List[Tuple[int, str, int, int]]) -> str:
        temp_dir = tempfile.gettempdir()
        input_name = Path(input_path).stem
        output_path = os.path.join(temp_dir, f"{input_name}_redacted.pdf")
        self.redact_pii(input_path , output_path , pii_spans)
        return output_path
    
    def verify_redaction(self , pdf_path:str , original_text : str)->bool:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return original_text not in text
         
def demo_redaction():
    import tempfile
    from pathlib import Path
    demo_pdf = Path(tempfile.gettempdir()) / "demo_original.pdf"
    redacted_pdf = Path(tempfile.gettempdir()) / "demo_redacted.pdf"
    doc = fitz.open()
    page = doc.new_page()
    
    text = "Contact John Smith at john.smith83@gmail.com or call (415) 555-0192"
    page.insert_text((50, 100), text, fontsize=12)
    
    doc.save(str(demo_pdf))
    doc.close()
    
    print(f" Created demo PDF: {demo_pdf}")
    print(f"  Original text: {text}")
    
    redactor = Redactor()
    pii_spans = [
        (0, "John Smith", 0, 0),        
        (0, "john.smith83@gmail.com", 0, 0),
        (0, "(415) 555-0192", 0, 0)
    ]
    
    result = redactor.redact_pii(str(demo_pdf), str(redacted_pdf), pii_spans)
    
    print(f"\n Redaction applied:")
    print(f"   Redactions: {result['redaction_count']}")
    print(f"   Output: {redacted_pdf}")
    
    if redactor.verify_redaction(str(redacted_pdf), "John Smith"):
        print(f"\n SUCCESS: PII is not searchable in redacted PDF")
    else:
        print(f"\nFAILED: PII still searchable")
    
    return str(redacted_pdf)


if __name__ == "__main__":
    demo_redaction()
                                


        