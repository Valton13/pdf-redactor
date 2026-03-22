from typing import List , Tuple ,Optional , Dict , Any
import fitz
import re

class CoordinateMapper:
    def __init__(self , case_sensitive:bool = False , normalize_whitespace :bool = True):
        self.case_sensitive = case_sensitive
        self.normalize_whitespace = normalize_whitespace
    
    def map_text_to_rects(self , page:fitz.Page , text_span  :str , context_window : int = 20) -> List[fitz.Rect]:
        if not text_span or not text_span.strip():
            return []
        search_text = self._normalize_text(text_span)
        rects = self._direct_search(page , search_text)
        if rects :
            return rects
        rects = self._context_search(page , search_text , context_window)
        if rects :
            return rects
        rects = self._fuzzy_search(page,search_text)
        return rects
    
    def _normalize_text(self,text:str)->str:
        if not text:
            return ""
        if self.normalize_whitespace:
            text = re.sub(r'\s+' , ' ' , text).strip()
        if not self.case_sensitive:
            text = text.lower()
        return text 

    def _direct_search(self , page:fitz.Page , text : str) -> List[fitz.Rect]:
        try:
            quads = page.search_for(text)
            if quads:
                return quads
            if self.case_sensitive:
                quads = page.search_for(text.lower())
                if quads:
                    return quads
            return []
        except Exception:
            return []

    def _context_search(self , page : fitz.Page , text : str , context_window  :int = 20) -> List[fitz.Rect]:
        page_text = page.get_text()
        if not page_text:
            return []
        norm_page_text = self._normalize_text(page_text)
        norm_search_text = self._normalize_text(text)
        positions =[]
        start =0
        while True:
            pos = norm_page_text.find(norm_search_text , start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + len(norm_search_text)
        if not positions:
            return []    
        all_rects =[]
        for pos in positions:
            start_idx = max(0, pos - context_window)
            end_idx = min(len(norm_page_text), pos + len(norm_search_text) + context_window)
            context_text = norm_page_text[start_idx:end_idx]
            quads = page.search_for(context_text)
            if quads:
                text_quads = page.search_for(text)
                if text_quads:
                    all_rects.extend(text_quads)
        return all_rects
    
    def _fuzzy_search(self , page:fitz.Page , text : str)-> List[fitz.Rect]:
        blocks = page.get_text("dict")["blocks"]
        all_rects =[]
        norm_search = self._normalize_text(text)
        for block in blocks:
            if block.get("type") != 0:  
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if not span_text:
                        continue
                    norm_span = self._normalize_text(span_text)
                    if norm_search in norm_span:
                        bbox = span.get("bbox")
                        if bbox:
                            rect = fitz.Rect(bbox)
                            all_rects.append(rect)
        return all_rects
    def map_pii_spans(self , page:fitz.Page , pii_spans :List[Tuple[str, int, int]], min_confidence: float = 0.7)-> List[Tuple[str, List[fitz.Rect], float]]:
        results =[]
        for text ,start , end in pii_spans:
            if not text or not text.strip():
                continue
            rects = self.map_text_to_rects(page , text)
            confidence = self._calculate_condfidence(text , rects , page)
            if confidence >= min_confidence:
                results.append((text , rects , confidence))
        return results

    def _calculate_condfidence(self , text:str , rects  :List[fitz.Rect]  ,page:fitz.Page) ->float:
        if not rects:
            return 0.0
        confidence = 0.8

        if len(rects)  >1:
            confidence += 0.1
        avg_area = sum(r.get_area() for r in rects)/len(rects)
        if 10  < avg_area < 100000:
            confidence += 0.05
        return min(1.0 , confidence)

    def get_text_at_rect(self,page:fitz.Page , rect:fitz.Rect)-> str:
        try:
            text = page.get_text("text" , clip=rect)
            return text.strip()
        except Exception:
            return ""
        
def demo_coordinate_mapping():
    """Demo function showing coordinate mapping in action"""
    import tempfile
    from pathlib import Path
    
    # Create demo PDF
    demo_pdf = Path(tempfile.gettempdir()) / "demo_coords.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    
    # Add multi-line text
    text = """Contact Information:
    Name: John Smith
    Email: john.smith83@gmail.com
    Phone: (415) 555-0192
    Address: 123 Main St, San Francisco, CA 94105"""
    
    page.insert_text((50, 100), text, fontsize=11)
    doc.save(str(demo_pdf))
    doc.close()
    
    print(f"📄 Created demo PDF: {demo_pdf}")
    
    # Map coordinates
    doc = fitz.open(str(demo_pdf))
    page = doc[0]
    
    mapper = CoordinateMapper(case_sensitive=False)
    
    test_cases = [
        "John Smith",
        "john.smith83@gmail.com",
        "123 Main St, San Francisco, CA 94105",
        "Phone: (415) 555-0192"
    ]
    
    print("\n📍 Coordinate Mapping Results:")
    print("-" * 60)
    
    for text in test_cases:
        rects = mapper.map_text_to_rects(page, text)
        status = "✅ Found" if rects else "❌ Not found"
        rect_count = len(rects)
        print(f"{status} '{text[:30]}{'...' if len(text) > 30 else ''}' → {rect_count} rect(s)")
        
        if rects:
            for i, rect in enumerate(rects[:2], 1):  # Show first 2 rects
                print(f"   Rect {i}: x0={rect.x0:.1f}, y0={rect.y0:.1f}, x1={rect.x1:.1f}, y1={rect.y1:.1f}")
    
    doc.close()
    
    print("\n✅ Coordinate mapping demo complete!")


if __name__ == "__main__":
    demo_coordinate_mapping()   

              




        


