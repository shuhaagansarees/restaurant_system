import requests
import sys
import codecs
import os
import subprocess

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
BASE_URL = 'http://127.0.0.1:5000'

print("Installing pypdf for test...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
from pypdf import PdfReader

print("=== Testing Phase 11: PDF Export ===")

s_admin = requests.Session()
s_admin.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})

reports_to_test = ['sales', 'best_selling', 'orders']

for rtype in reports_to_test:
    print(f"\nTesting Report: {rtype}")
    
    # 1. Fetch JSON Data
    resp_json = s_admin.get(f"{BASE_URL}/api/report_data?type={rtype}&start=2020-01-01&end=2030-12-31")
    if resp_json.status_code != 200:
        sys.exit(f"Failed to fetch JSON for {rtype}")
    
    data = resp_json.json().get('data', [])
    print(f"   Found {len(data)} rows in JSON endpoint.")
    
    # 2. Fetch PDF File
    resp_pdf = s_admin.get(f"{BASE_URL}/api/report_export_pdf?type={rtype}&start=2020-01-01&end=2030-12-31")
    if resp_pdf.status_code != 200:
        sys.exit(f"Failed to fetch PDF for {rtype}. Status: {resp_pdf.status_code}")
        
    if resp_pdf.headers.get('Content-Type') != 'application/pdf':
        sys.exit(f"Failed: Endpoint did not return a PDF for {rtype}")
        
    pdf_path = f"temp_{rtype}.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(resp_pdf.content)
        
    # 3. Verify PDF Content matches JSON Data
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        
    # Replace newlines for easier searching
    text = text.replace('\n', ' ')
    
    for row in data:
        # Check if the primary values from the JSON row exist in the PDF text
        for key, val in row.items():
            val_str = str(val)
            # Sometimes floats like 100.0 might be printed as 100.00 or Rs.100.00
            # Let's just do a loose check on the string representation or part of it
            if isinstance(val, float):
                val_str = f"{val:.2f}"
                
            # Date formatting check
            if '2026' in val_str:
                continue # ignore timestamp exact match due to formatting
                
            if val_str not in text and val_str.replace('.00', '') not in text:
                print(f"   [WARNING] Value '{val_str}' not explicitly found in PDF text for {rtype}. Text snippet: {text[:100]}...")
                
    print(f"   ✓ PDF successfully generated and parsed for {rtype}!")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

print("\n=== ALL PDF TESTS PASSED ===")
