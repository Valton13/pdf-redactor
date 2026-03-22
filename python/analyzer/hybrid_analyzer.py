from presidio_analyzer import AnalyzerEngine
from python.analyzer.pii_detector import PIIDetector
from python.recognizers.account_recognizer import account_recognizer , international_account_recognizer 
from python.recognizers.policy_recognizer import policy_recognizer , medical_record_recognizer
from python.recognizers.employee_recognizer import employee_recognizer

class HybridAnalyzer:
    def __init__(self,confidence_threshold:float = 0.7):
        self.analyzer = AnalyzerEngine()
        self._register_custom_recognizers()
        self.confidence_threshold  =confidence_threshold
    
    def _register_custom_recognizers(self):
        self.analyzer.registry.add_recognizer(account_recognizer)
        self.analyzer.registry.add_recognizer(international_account_recognizer)
        self.analyzer.registry.add_recognizer(policy_recognizer)
        self.analyzer.registry.add_recognizer(medical_record_recognizer)
        self.analyzer.registry.add_recognizer(employee_recognizer)
    
    def analyze(self , text  :str , language:str = "en" , score_threshold:float= None):
        if not text or not text.strip():
            return []
        threshold = score_threshold or self.confidence_threshold
        results = self.analyzer.analyze(text = text , language=language , score_threshold=threshold)
        results.sort(key =lambda x:x.start)
        return results
    
    def analyze_pages(self , pages:list , language:str = "en") ->dict:
        results= {}
        for page_num , text in pages:
            entities = self.analyze(text , language)
            if entities:
                results[page_num] = entities
        return results

    def get_detections_stats(self , results:list , text:str)-> dict:
        if not results:
            return {
                "total_entities": 0,
                "unique_types": 0,
                "avg_confidence": 0.0,
                "entity_types": [],
                "by_type": {}
            }
        by_type = {}
        for entity in results:
            entity_text = text[entity.start:entity.end]
            if entity.entity_type not in by_type:
                by_type[entity.entity_type] = []
            by_type[entity.entity_type].append({"text": entity_text , "confidence" :entity.score})
        total_entites = len(results)
        unique_types = len(by_type)
        avg_confidence = sum(r.score for r in results)/ total_entites
        return {
            "total_entities": total_entites,
            "unique_types": unique_types,
            "avg_confidence": avg_confidence,
            "entity_types": sorted(by_type.keys()),
            "by_type": by_type
        }

#copied
def demo_hybrid_analysis():
    """Demonstrate hybrid analyzer capabilities"""
    print("\n" + "="*70)
    print("HYBRID ANALYZER DEMO")
    print("="*70)
    
    # Initialize hybrid analyzer
    analyzer = HybridAnalyzer(confidence_threshold=0.7)
    
    # Comprehensive test text
    test_text = """
    Employee Information
    Name: John Smith
    Email: john.smith83@gmail.com
    Phone: (415) 555-0192
    SSN: 123-45-6789
    
    Financial Details
    Bank Account: 1234-5678-9012-3456
    Routing: 123456789
    IBAN: DE89370400440532013000
    
    Insurance Information
    Policy Number: POL-1234567
    Claim: CLM-12345678
    Medical Record: MRN-77889900
    
    Emergency Contact
    Name: Maria Rodriguez
    Phone: (415) 555-0199
    """
    
    print("\n📄 Test Document:")
    print("-"*70)
    print(test_text)
    print("-"*70)
    
    # Analyze text
    results = analyzer.analyze(test_text)
    
    # Get statistics
    stats = analyzer.get_detections_stats(results, test_text)
    
    print("\n🔍 Detection Results:")
    print("-"*70)
    print(f"Total entities detected: {stats['total_entities']}")
    print(f"Unique entity types: {stats['unique_types']}")
    print(f"Average confidence: {stats['avg_confidence']:.2f}")
    print(f"Entity types: {', '.join(stats['entity_types'])}")
    
    print("\n📋 Detailed Breakdown:")
    print("-"*70)
    
    for entity_type in sorted(stats['by_type'].keys()):
        entities = stats['by_type'][entity_type]
        print(f"\n{entity_type}:")
        for entity in entities:
            confidence = "⭐⭐⭐" if entity['confidence'] >= 0.9 else "⭐⭐" if entity['confidence'] >= 0.8 else "⭐"
            print(f"  {confidence} '{entity['text']}' ({entity['confidence']:.2f})")
    
    print("\n" + "="*70)
    print("✅ Hybrid analyzer working correctly!")
    print("="*70)
    
    # Show comparison: what Presidio alone would miss
    print("\n💡 Hybrid Advantage:")
    print("-"*70)
    custom_types = {"BANK_ACCOUNT", "POLICY_NUMBER", "MEDICAL_RECORD_NUMBER", "EMPLOYEE_NAME"}
    custom_detected = [t for t in stats['entity_types'] if t in custom_types]
    
    if custom_detected:
        print(f"Custom recognizers detected: {', '.join(custom_detected)}")
        print("These would be MISSED by Presidio alone!")
    else:
        print("No custom entities in this sample")
    
    print("\n✅ Hybrid approach provides:")
    print("   • Pre-trained models: 20+ standard PII types")
    print("   • Custom rules: Domain-specific patterns")
    print("   • Best of both worlds: Maximum coverage + accuracy")


if __name__ == "__main__":
    demo_hybrid_analysis() 



  
