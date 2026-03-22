import fitz
from dataclasses import dataclass
from typing import List , Dict , Any

@dataclass
class PageText:
    page_num :int
    text : str
    blocks : List[Dict[str , Any]]

class PDFExtractor:
    def __init__(self , pdf_path:str):
        self.pdf_path = pdf_path
        self.doc = None

    def __enter__(self):
        self.doc = fitz.open(self.pdf_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  
        if self.doc:
            self.doc.close()

    def extract_page(self,page_num:int) -> PageText:
        if page_num >= len(self.doc):
            raise ValueError(f"Page {page_num} out of range (document has {len(self.doc)} pages)")
        page = self.doc[page_num]
        text = page.get_text()
        blocks = page.get_text("dict")["blocks"]
        return PageText(page_num=page_num , text= text , blocks=blocks)
    
    def extract_allpages(self) -> List[PageText]:
        results =[]
        for page_num in range(len(self.doc)):
            results.append(self.extract_page(page_num))
        return results

    def get_pagecount(self) -> int:
        return len(self.doc) if self.doc else 0
        
