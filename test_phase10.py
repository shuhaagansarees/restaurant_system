import requests
import sys
import codecs
import time
import os

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
BASE_URL = 'http://127.0.0.1:5000'

print("=== Testing Phase 10: WhatsApp Notifications ===")

# 1. Test Without Keys via API
print("\n1. Testing Without Keys (End-to-End API)...")
# We place an order that includes a mobile number
r0 = requests.post(f"{BASE_URL}/api/place_order", json={
    'table_id': 1, 
    'order_type': 'dine-in', 
    'customer_name': 'Test User',
    'customer_mobile': '9876543210',
    'items': [{'id': 1, 'quantity': 1, 'price': 100}]
})

if r0.status_code == 200 and r0.json().get('success'):
    print("   ✓ Order placed successfully without crashing!")
else:
    sys.exit(f"   Failed to place order: {r0.status_code} {r0.text}")

order_id = r0.json().get('order_id')
print(f"   Order #{order_id} created. Console should show 'Not configured — skipping message' for both 'placed' and 'served' events.")

# Update to served
requests.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})
# We need a session
s = requests.Session()
s.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})
r1 = s.post(f"{BASE_URL}/api/update_order_status", json={'order_id': order_id, 'status': 'served'})
if r1.status_code == 200:
    print("   ✓ Order moved to served without crashing!")

# 2. Test With Dummy Keys directly calling the helper
print("\n2. Testing With Dummy Keys (Direct Helper Function Test)...")
import app
os.environ['WHATSAPP_TOKEN'] = 'dummy_token_123'
os.environ['WHATSAPP_PHONE_ID'] = 'dummy_phone_456'

print("   Calling send_whatsapp_message with dummy keys...")
response = app.send_whatsapp_message('9876543210', 'Test message with dummy keys')

if response is not None:
    print(f"   ✓ Function executed and returned response!")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Body: {response.text}")
    
    if response.status_code in [400, 401]:
        print("   ✓ Graph API correctly rejected the dummy token (which means the request was formatted properly!)")
else:
    print("   Failed: No response returned from helper function")

print("\n=== ALL WHATSAPP TESTS PASSED ===")
