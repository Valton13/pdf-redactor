"""
PII Detection Module
Integrates Microsoft Presidio for pre-trained PII detection
"""
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from typing import List, Dict, Optional, Tuple
import re


class PIIDetector:
    def __init__(self, confidence_threshold: float = 0.7):
        self.analyzer = AnalyzerEngine()
        self.confidence_threshold = confidence_threshold
    
    def analyze_text(
        self,
        text: str,
        language: str = "en"
    ) -> List[RecognizerResult]:
        if not text or not text.strip():
            return []
        results = self.analyzer.analyze(
            text=text,
            language=language,
            score_threshold=self.confidence_threshold
        )
        results.sort(key=lambda x: x.start)        
        return results
    
    def analyze_pages(
        self,
        pages: List[Tuple[int, str]],
        language: str = "en"
    ) -> Dict[int, List[RecognizerResult]]:
        results = {}       
        for page_num, text in pages:
            entities = self.analyze_text(text, language)
            if entities:
                results[page_num] = entities        
        return results
    
    def get_supported_entities(self) -> List[str]:
        return self.analyzer.get_supported_entities(language="en")
    
    def extract_entity_text(
        self,
        text: str,
        entity: RecognizerResult
    ) -> str:
        return text[entity.start:entity.end]
    
    def filter_by_entity_types(
        self,
        results: List[RecognizerResult],
        entity_types: Optional[List[str]] = None
    ) -> List[RecognizerResult]:
        if not entity_types:
            return results        
        entity_types_upper = [et.upper() for et in entity_types]
        return [r for r in results if r.entity_type in entity_types_upper]
def demo_pii_detection():
    """Demonstrate PII detection capabilities"""
    print("\n" + "="*70)
    print("PRESCRIPTO PII DETECTION DEMO")
    print("="*70)
    sample_text = """
    Patient Information:
    Name: John Smith
    DOB: August 14, 1985
    SSN: 123-45-6789
    Email: john.smith83@gmail.com
    Phone: (415) 555-0192
    Address: 123 Main St, San Francisco, CA 94105
    Account: 1234-5678-9012-3456
    Policy: POL-1234567
    Medical Record: MRN-77889900
    """
    
    print("\n Sample Text:")
    print("-"*70)
    print(sample_text)
    print("-"*70)
    detector = PIIDetector(confidence_threshold=0.7)
    results = detector.analyze_text(sample_text)
    print("\n Detected PII Entities:")
    print("-"*70)
    if not results:
        print("No PII detected (confidence threshold may be too high)")
        return
    entities_by_type = {}
    for entity in results:
        entity_text = detector.extract_entity_text(sample_text, entity)
        if entity.entity_type not in entities_by_type:
            entities_by_type[entity.entity_type] = []
        entities_by_type[entity.entity_type].append((entity_text, entity.score))
    for entity_type, items in sorted(entities_by_type.items()):
        print(f"\n{entity_type}:")
        for text, score in items:
            confidence = "good" if score >= 0.9 else "avg" if score >= 0.8 else "bad"
            print(f"  {confidence} '{text}' (confidence: {score:.2f})")
    print("\n" + "-"*70)
    print(" Summary:")
    print(f"  Total PII entities detected: {len(results)}")
    print(f"  Unique entity types: {len(entities_by_type)}")
    print(f"  Average confidence: {sum(r.score for r in results)/len(results):.2f}")
    print(f"  Entity types: {', '.join(sorted(entities_by_type.keys()))}")
    print("\nSupportedContent Entity Types (20+):")
    supported = detector.get_supported_entities()
    print(f"  {', '.join(sorted(supported))[:150]}...")
    print("="*70)
    print("Presidio detection working correctly!")
    print("="*70)


if __name__ == "__main__":
    demo_pii_detection()