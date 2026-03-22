from presidio_analyzer import PatternRecognizer
EMPLOYEE_NAMES = [
    "John Smith",
    "Sarah Chen",
    "Miguel Rodriguez",
    "Aisha Patel",
    "David Kim",
    "Maria Rodriguez",  
    "James Wilson",   
    "Emily Johnson",   
]

employee_recognizer = PatternRecognizer(
    supported_entity="EMPLOYEE_NAME",
    deny_list=EMPLOYEE_NAMES,
    supported_language="en",
    context=[
        "employee", "staff", "team member", "colleague",
        "contact", "emergency contact", "manager", "supervisor",
        "hr", "human resources", "directory", "roster"
    ]
)
'''''
COMMON_FIRST_NAMES = [
    "John", "Jane", "Michael", "Sarah", "David",
    "Emily", "James", "Maria", "Robert", "Jennifer",
    "William", "Lisa", "Richard", "Patricia", "Thomas"
]

common_name_recognizer = PatternRecognizer(
    supported_entity="COMMON_NAME",
    deny_list=COMMON_FIRST_NAMES,
    score=0.75,  
    supported_language="en",
    context=[
        "name", "contact", "person", "individual",
        "applicant", "candidate", "patient", "client"
    ]
)'''

def demo_employee_recognition():
    from presidio_analyzer import AnalyzerEngine
    print("\n" + "="*70)
    print("EMPLOYEE NAME RECOGNIZER DEMO")
    print("="*70)
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(employee_recognizer)
    #analyzer.registry.add_recognizer(common_name_recognizer)
    test_cases = [
        "Contact John Smith for project details",
        "Sarah Chen is the team lead",
        "Emergency contact: Maria Rodriguez",
        "James Wilson submitted the report",
        "Emily Johnson attended the meeting",
        "Contact support at help@company.com",  
        "The project deadline is next Friday",  
    ]    
    print("\n Testing Employee Name Detection:")
    print("-"*70)
    for i , text in enumerate(test_cases ,1):
        results = analyzer.analyze(text = text , language="en")
        print(f"\nTest {i}: '{text}'")
        if results:
            for result in results:
                entity_text = text[result.start:result.end]
                confidence  = "good" if result.score >= 0.9 else "avg" if result.score >= 0.8 else "bad"
                print(f"pass {result.entity_type}:'{entity_text}' {confidence} (confidence : {result.score:.2f})")
        else:
            print("no employee")
    print("\n" + "="*70)
    print("Employee name recognizer working correctly!")
    print("="*70)
    print("\nCurrent Employee Denylist:")
    print("-"*70)
    for i, name in enumerate(EMPLOYEE_NAMES, 1):
        print(f"  {i}.{name}")
    print(f"\nTotal names in denylist: {len(EMPLOYEE_NAMES)}")

def add_employee_to_denylist(employee_name:str):
    if employee_name not in EMPLOYEE_NAMES:
        EMPLOYEE_NAMES.append(employee_name)
        print(f"added{employee_name}")
    else:
        print(f"{employee_name} already in list")

def remove_employee_to_denylist(emplyee_name : str):
    if emplyee_name in EMPLOYEE_NAMES:
        EMPLOYEE_NAMES.remove(emplyee_name)
        print(f"{emplyee_name} removed") 
    else:
        print(f"{emplyee_name} not in list")       

if __name__ == "__main__":
    demo_employee_recognition()
    '''''
    print("\n" + "="*70)
    print("DENYLIST MANAGEMENT EXAMPLE")
    print("="*70)    
    add_employee_to_denylist("New Employee")
    print(f"\nUpdated denylist count: {len(EMPLOYEE_NAMES)}")   
    remove_employee_to_denylist("New Employee")
    print(f"Final denylist count: {len(EMPLOYEE_NAMES)}")              
    '''
