#!/usr/bin/env python3
"""
Generates 10 diverse PDFs with realistic fake PII for redaction testing.
Uses ONLY standard libraries + reportlab (no external APIs).
"""
import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime, timedelta
import random

# Create output directory
Path("test-corpus").mkdir(exist_ok=True)

# Fake data generator (no external dependencies)
class FakeData:
    names = ["John Smith", "Sarah Chen", "Miguel Rodriguez", "Aisha Patel", "David Kim"]
    emails = ["john.smith83@gmail.com", "s.chen@outlook.com", "mrodriguez99@yahoo.com", "aisha.patel22@protonmail.com", "dkim.tech@gmail.com"]
    phones = ["(415) 555-0192", "(212) 555-0178", "(312) 555-0144", "(713) 555-0163", "(617) 555-0129"]
    addresses = [
        "123 Main St, Apt 4B, San Francisco, CA 94105",
        "456 Oak Ave, Seattle, WA 98101",
        "789 Maple Dr, Chicago, IL 60601",
        "321 Pine Rd, Houston, TX 77002",
        "654 Elm Blvd, Boston, MA 02108"
    ]
    ssn = ["123-45-6789", "234-56-7890", "345-67-8901", "456-78-9012", "567-89-0123"]
    account_numbers = ["**** **** **** 4321", "**** **** **** 8765", "**** **** **** 2109", "**** **** **** 6543", "**** **** **** 0987"]
    routing_numbers = ["021000021", "026009593", "071000013", "111000025", "011401533"]
    
    @staticmethod
    def random_choice(lst):
        return random.choice(lst)

# PDF generator base class
def create_pdf(filename, elements):
    doc = SimpleDocTemplate(
        f"test-corpus/{filename}",
        pagesize=letter,
        topMargin=50,
        bottomMargin=50
    )
    styles = getSampleStyleSheet()
    doc.build(elements)

# 1. Resume
def generate_resume():
    styles = getSampleStyleSheet()
    name = FakeData.random_choice(FakeData.names)
    email = FakeData.random_choice(FakeData.emails)
    phone = FakeData.random_choice(FakeData.phones)
    address = FakeData.random_choice(FakeData.addresses)
    
    elements = [
        Paragraph(f"<font size=16><b>{name}</b></font>", styles["Normal"]),
        Paragraph(f"{address} | {phone} | {email}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>PROFESSIONAL EXPERIENCE</b>", styles["Heading2"]),
        Paragraph("Senior Software Engineer", styles["Normal"]),
        Paragraph("TechCorp Inc., San Francisco, CA", styles["Normal"]),
        Paragraph("Jan 2020 – Present", styles["Normal"]),
        Spacer(1, 10),
        Paragraph("• Led development of low-latency trading infrastructure", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>EDUCATION</b>", styles["Heading2"]),
        Paragraph("M.S. Computer Science", styles["Normal"]),
        Paragraph("Stanford University, Stanford, CA", styles["Normal"]),
        Paragraph("GPA: 3.8/4.0", styles["Normal"]),
    ]
    create_pdf("01-resume.pdf", elements)

# 2. Bank Statement
def generate_bank_statement():
    styles = getSampleStyleSheet()
    name = FakeData.random_choice(FakeData.names)
    account = FakeData.random_choice(FakeData.account_numbers)
    routing = FakeData.random_choice(FakeData.routing_numbers)
    
    elements = [
        Paragraph("<font size=14><b>ACME BANK</b></font>", styles["Normal"]),
        Paragraph("123 Finance Ave, New York, NY 10001", styles["Normal"]),
        Spacer(1, 20),
        Paragraph(f"<b>Account Holder:</b> {name}", styles["Normal"]),
        Paragraph(f"<b>Account Number:</b> {account}", styles["Normal"]),
        Paragraph(f"<b>Routing Number:</b> {routing}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>TRANSACTION HISTORY</b>", styles["Heading2"]),
        Table([
            ["Date", "Description", "Amount"],
            ["2024-02-01", "GROCERY STORE #456", "$87.42"],
            ["2024-02-03", "AMAZON.COM", "$124.99"],
            ["2024-02-05", "SALARY DEPOSIT", "$5,240.00"],
        ], style=TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ])),
    ]
    create_pdf("02-bank-statement.pdf", elements)

# 3. Medical Form (HIPAA)
def generate_medical_form():
    styles = getSampleStyleSheet()
    name = FakeData.random_choice(FakeData.names)
    ssn = FakeData.random_choice(FakeData.ssn)
    dob = "08/14/1985"
    
    elements = [
        Paragraph("<font size=14><b>HEALTHCARE PROVIDERS ASSOCIATION</b></font>", styles["Normal"]),
        Paragraph("<b>PATIENT INFORMATION FORM (HIPAA COMPLIANT)</b>", styles["Heading2"]),
        Spacer(1, 20),
        Paragraph(f"<b>Patient Name:</b> {name}", styles["Normal"]),
        Paragraph(f"<b>Date of Birth:</b> {dob}", styles["Normal"]),
        Paragraph(f"<b>Social Security Number:</b> {ssn}", styles["Normal"]),
        Paragraph("<b>Medical Record Number:</b> MRN-77889900", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>Diagnosis Codes:</b> ICD-10: E11.9 (Type 2 Diabetes)", styles["Normal"]),
        Paragraph("<b>Prescription:</b> Metformin 500mg, twice daily", styles["Normal"]),
    ]
    create_pdf("03-medical-form.pdf", elements)

# 4. Lease Agreement
def generate_lease():
    styles = getSampleStyleSheet()
    tenant = FakeData.random_choice(FakeData.names)
    landlord = "Premier Properties LLC"
    address = FakeData.random_choice(FakeData.addresses)
    
    elements = [
        Paragraph("<font size=14><b>RESIDENTIAL LEASE AGREEMENT</b></font>", styles["Normal"]),
        Spacer(1, 20),
        Paragraph(f"<b>Tenant:</b> {tenant}", styles["Normal"]),
        Paragraph(f"<b>Landlord:</b> {landlord}", styles["Normal"]),
        Paragraph(f"<b>Property Address:</b> {address}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>Lease Term:</b> 12 months starting March 1, 2024", styles["Normal"]),
        Paragraph("<b>Rent:</b> $2,450.00/month due on 1st of each month", styles["Normal"]),
        Paragraph("<b>Security Deposit:</b> $2,450.00 (refundable)", styles["Normal"]),
    ]
    create_pdf("04-lease-agreement.pdf", elements)

# 5. W-9 Tax Form
def generate_w9():
    styles = getSampleStyleSheet()
    name = FakeData.random_choice(FakeData.names)
    ssn = FakeData.random_choice(FakeData.ssn)
    
    elements = [
        Paragraph("<font size=14><b>IRS FORM W-9</b></font>", styles["Normal"]),
        Paragraph("(Rev. October 2023)", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>Request for Taxpayer Identification Number</b>", styles["Normal"]),
        Spacer(1, 20),
        Paragraph(f"1. Name (as shown on your income tax return): <b>{name}</b>", styles["Normal"]),
        Paragraph(f"2. Social Security Number: <b>{ssn}</b>", styles["Normal"]),
        Spacer(1, 10),
        Paragraph("3. Address:", styles["Normal"]),
        Paragraph(FakeData.random_choice(FakeData.addresses), styles["Normal"]),
        Spacer(1, 20),
        Paragraph("Under penalties of perjury, I certify that...", styles["Normal"]),
    ]
    create_pdf("05-w9-tax-form.pdf", elements)

# 6. Passport Scan (Image-based PII)
def generate_passport():
    styles = getSampleStyleSheet()
    name = FakeData.random_choice(FakeData.names).upper()
    passport_num = f"P12345678"
    dob = "14 AUG 1985"
    issue = "15 MAR 2020"
    expiry = "14 MAR 2030"
    
    elements = [
        Paragraph("<font size=14><b>UNITED STATES OF AMERICA</b></font>", styles["Normal"]),
        Paragraph("<b>PASSPORT</b>", styles["Heading1"]),
        Spacer(1, 20),
        Paragraph(f"<b>Passport No:</b> {passport_num}", styles["Normal"]),
        Paragraph(f"<b>Name:</b> {name}", styles["Normal"]),
        Paragraph(f"<b>Date of Birth:</b> {dob}", styles["Normal"]),
        Paragraph(f"<b>Place of Birth:</b> NEW YORK, NY", styles["Normal"]),
        Paragraph(f"<b>Date of Issue:</b> {issue}", styles["Normal"]),
        Paragraph(f"<b>Date of Expiry:</b> {expiry}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<i>[PASSPORT PHOTO AREA]</i>", styles["Italic"]),
    ]
    create_pdf("06-passport-scan.pdf", elements)

# 7. Credit Card Statement
def generate_credit_card():
    styles = getSampleStyleSheet()
    name = FakeData.random_choice(FakeData.names)
    card_num = "**** **** **** 1234"
    
    elements = [
        Paragraph("<font size=14><b>GLOBAL CREDIT UNION</b></font>", styles["Normal"]),
        Spacer(1, 20),
        Paragraph(f"<b>Cardholder:</b> {name}", styles["Normal"]),
        Paragraph(f"<b>Account Number:</b> {card_num}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>STATEMENT PERIOD:</b> Jan 15 – Feb 14, 2024", styles["Normal"]),
        Spacer(1, 10),
        Table([
            ["Date", "Description", "Amount"],
            ["02/01", "STARBUCKS #12345", "$7.85"],
            ["02/03", "UBER *RIDE", "$18.50"],
            ["02/10", "AMAZON MKTPLACE", "$42.99"],
            ["02/14", "TOTAL DUE", "$69.34"],
        ], style=TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ])),
    ]
    create_pdf("07-credit-card-statement.pdf", elements)

# 8. Academic Transcript
def generate_transcript():
    styles = getSampleStyleSheet()
    name = FakeData.random_choice(FakeData.names)
    student_id = f"S{random.randint(100000, 999999)}"
    
    elements = [
        Paragraph("<font size=14><b>STANFORD UNIVERSITY</b></font>", styles["Normal"]),
        Paragraph("<b>OFFICIAL ACADEMIC TRANSCRIPT</b>", styles["Heading2"]),
        Spacer(1, 20),
        Paragraph(f"<b>Student Name:</b> {name}", styles["Normal"]),
        Paragraph(f"<b>Student ID:</b> {student_id}", styles["Normal"]),
        Paragraph("<b>Degree:</b> Master of Science, Computer Science", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>COURSEWORK</b>", styles["Heading2"]),
        Table([
            ["Course", "Term", "Grade", "Units"],
            ["CS229", "Fall 2022", "A", "4"],
            ["CS224N", "Winter 2023", "A-", "4"],
            ["CS231N", "Spring 2023", "A", "4"],
        ], style=TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ])),
        Spacer(1, 20),
        Paragraph("<b>Cumulative GPA:</b> 3.87/4.00", styles["Normal"]),
    ]
    create_pdf("08-academic-transcript.pdf", elements)

# 9. Insurance Claim Form
def generate_insurance_claim():
    styles = getSampleStyleSheet()
    claimant = FakeData.random_choice(FakeData.names)
    policy_num = f"POL-{random.randint(1000000, 9999999)}"
    date_of_loss = "2024-01-28"
    
    elements = [
        Paragraph("<font size=14><b>NATIONWIDE INSURANCE</b></font>", styles["Normal"]),
        Paragraph("<b>PROPERTY DAMAGE CLAIM FORM</b>", styles["Heading2"]),
        Spacer(1, 20),
        Paragraph(f"<b>Claimant Name:</b> {claimant}", styles["Normal"]),
        Paragraph(f"<b>Policy Number:</b> {policy_num}", styles["Normal"]),
        Paragraph(f"<b>Date of Loss:</b> {date_of_loss}", styles["Normal"]),
        Paragraph(f"<b>Loss Location:</b> {FakeData.random_choice(FakeData.addresses)}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>Description of Loss:</b>", styles["Normal"]),
        Paragraph("Vehicle collision at intersection of Market St & 5th Ave. Front bumper damage estimated at $3,200.", styles["Normal"]),
    ]
    create_pdf("09-insurance-claim.pdf", elements)

# 10. Employment Application
def generate_employment_app():
    styles = getSampleStyleSheet()
    applicant = FakeData.random_choice(FakeData.names)
    ssn = FakeData.random_choice(FakeData.ssn)
    
    elements = [
        Paragraph("<font size=14><b>TECH INNOVATIONS INC.</b></font>", styles["Normal"]),
        Paragraph("<b>EMPLOYMENT APPLICATION</b>", styles["Heading2"]),
        Spacer(1, 20),
        Paragraph(f"<b>Full Legal Name:</b> {applicant}", styles["Normal"]),
        Paragraph(f"<b>Social Security Number:</b> {ssn}", styles["Normal"]),
        Paragraph(f"<b>Date of Birth:</b> 08/14/1985", styles["Normal"]),
        Paragraph(f"<b>Address:</b> {FakeData.random_choice(FakeData.addresses)}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>Emergency Contact:</b>", styles["Normal"]),
        Paragraph("Maria Rodriguez, (415) 555-0199, mother", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>Authorization:</b> I authorize investigation of my background...", styles["Normal"]),
    ]
    create_pdf("10-employment-application.pdf", elements)

# Generate all PDFs
if __name__ == "__main__":
    print("Generating 10-PDF test corpus with realistic fake PII...")
    generate_resume()
    generate_bank_statement()
    generate_medical_form()
    generate_lease()
    generate_w9()
    generate_passport()
    generate_credit_card()
    generate_transcript()
    generate_insurance_claim()
    generate_employment_app()
    print("\n✅ SUCCESS: All 10 PDFs created in 'test-corpus/' folder")
    print("\n📁 Files generated:")
    for i in range(1, 11):
        print(f"   test-corpus/0{i}-*.pdf")
    print("\n⚠️  WARNING: These contain SYNTHETIC PII for testing ONLY.")
    print("   Never use real personal data for development/testing.")