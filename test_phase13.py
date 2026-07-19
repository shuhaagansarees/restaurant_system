import requests
import sys
import codecs
import time
import os
import subprocess
import urllib.parse

subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python", "numpy", "Pillow"])
import cv2
import numpy as np
from PIL import Image
import io

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
BASE_URL = 'http://127.0.0.1:5000'

print("=== Testing Phase 13: Table Timer + UPI Option ===")

s = requests.Session()
s.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})

# 1. Place a dine-in order to occupy Table T-1
print("\n[Action] Placing dine-in order for T-1...")
order_resp = s.post(f"{BASE_URL}/api/place_order", json={
    'table_name': 'T-1',
    'order_type': 'dine-in',
    'items': [{'id': 2, 'quantity': 1, 'price': 350}] # Butter Chicken
})
if order_resp.status_code != 200:
    sys.exit("FAILED to place order")
order_id = order_resp.json()['order_id']
print(f"   ✓ Order #{order_id} placed.")

# 2. Verify Table Timer on Live Tables
print("\n[Action] Verifying Live Tables Timer...")
tables_resp = s.get(f"{BASE_URL}/admin/live_tables")
html = tables_resp.text
# Check if T-1 has data-start attribute
# The card for T-1 should have occupied class and timer div
if 'data-start="' not in html or 'timer-display' not in html:
    sys.exit("FAILED: Table Timer HTML elements not found in Live Tables.")
print("   ✓ Table timer logic (session_start_time) is present in HTML payload.")

# Wait a second to simulate time passing (though backend time is fixed at creation, front-end JS does the ticking)
time.sleep(1)

# 3. Generate UPI QR Code and decode it
print("\n[Action] Generating and decoding UPI QR code...")
qr_amount = 350.0 + (350.0 * 0.05) # Total with 5% GST = 367.5 -> rounded to 368
qr_resp = s.get(f"{BASE_URL}/api/generate_upi_qr?amount={qr_amount}")
if qr_resp.status_code != 200:
    sys.exit(f"FAILED to generate QR code. Status: {qr_resp.status_code}")

qr_bytes = qr_resp.content
image = Image.open(io.BytesIO(qr_bytes)).convert('RGB')
open_cv_image = np.array(image) 
open_cv_image = open_cv_image[:, :, ::-1].copy() # RGB to BGR

detector = cv2.QRCodeDetector()
data, bbox, straight_qrcode = detector.detectAndDecode(open_cv_image)

print(f"   Decoded QR Data: {data}")
expected_amount_str = f"{qr_amount:.2f}"
if not data.startswith("upi://pay"):
    sys.exit("FAILED: Decoded text does not start with upi://pay")
if f"am={expected_amount_str}" not in data:
    sys.exit(f"FAILED: Expected amount {expected_amount_str} not found in UPI string.")
print("   ✓ UPI QR Code successfully generated and decoded to correct intent URL!")

# 4. Settle Bill to Vacate Table
print("\n[Action] Settling Bill for T-1...")
# First, mark order as completed via DB hack or directly if possible, but actually settle_bill endpoint doesn't strictly check if order is 'completed' to settle, it just sums it. Let's try settling it directly.
settle_resp = s.post(f"{BASE_URL}/api/settle_bill", json={
    'order_ids': [order_id],
    'discount': 0,
    'payment_method': 'UPI'
})
if settle_resp.status_code != 200 or not settle_resp.json().get('success'):
    sys.exit("FAILED to settle bill")
print("   ✓ Bill settled.")

# 5. Verify Table is Vacant and Timer is removed
print("\n[Action] Verifying Table is vacant...")
tables_resp2 = s.get(f"{BASE_URL}/admin/live_tables")
html2 = tables_resp2.text
# Since T-1 is now vacant, there should be no data-start element for it (unless another table has it, but no other tables are active)
if 'data-start="' in html2:
    sys.exit("FAILED: Timer still present after table was vacated!")
print("   ✓ Timer successfully cleared and table vacated.")

print("\n=== ALL PHASE 13 TESTS PASSED ===")
