import requests
import sys
import codecs
import time
import os
import subprocess

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
BASE_URL = 'http://127.0.0.1:5000'

print("=== Testing Phase 12: Multi-Language Menu ===")

s = requests.Session()

# 1. Login Admin
s.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})

# 2. Add an item WITH translations
print("\n[Admin] Adding item with Hindi/Gujarati translations...")
resp1 = s.post(f"{BASE_URL}/admin/items", data={
    'name': 'Masala Dosa',
    'name_hi': 'मसाला डोसा',
    'name_gu': 'મસાલા ઢોસા',
    'category_id': 2, # Main Course
    'price': 150,
    'description': 'Crispy crepe',
    'desc_hi': 'क्रिस्पी क्रेप',
    'desc_gu': 'ક્રિસ્પી ક્રેપ'
})

# 3. Add an item WITHOUT translations
print("[Admin] Adding item without translations (English only)...")
resp2 = s.post(f"{BASE_URL}/admin/items", data={
    'name': 'Plain Dosa',
    'name_hi': '',
    'name_gu': '',
    'category_id': 2,
    'price': 100,
    'description': 'Simple crepe'
})

# 4. Fetch Customer Menu
print("\n[Customer] Fetching Menu...")
menu_resp = s.get(f"{BASE_URL}/menu")
html = menu_resp.text

# 5. Verify Data Attributes for JS Toggle
# For Masala Dosa, it should have the translations
if 'data-hi="मसाला डोसा"' not in html or 'data-gu="મસાલા ઢોસા"' not in html:
    sys.exit("FAILED: Translations for Masala Dosa not found in HTML data attributes.")
else:
    print("   ✓ Item 1 correctly has translated data attributes.")

# For Plain Dosa, it should fallback to English in the data attribute
if 'data-hi="Plain Dosa"' not in html or 'data-gu="Plain Dosa"' not in html:
    sys.exit("FAILED: Fallback to English for Plain Dosa not found in HTML data attributes.")
else:
    print("   ✓ Item 2 correctly falls back to English in data attributes.")

# 6. Place an order (simulating customer using Hindi)
# The frontend sends item ID. The translated text is just for customer UI.
print("\n[Customer] Placing order...")
# Find the ID of Masala Dosa
# It's difficult to parse ID from raw HTML without bs4, but we know it's newly inserted.
# We'll just fetch from DB or assume the POST place_order will use the item ID.
# Let's do a quick DB check to get ID.
from app import app, MenuItem, OrderItem
with app.app_context():
    masala_dosa = MenuItem.query.filter_by(name='Masala Dosa').first()
    item_id = masala_dosa.id

order_resp = s.post(f"{BASE_URL}/api/place_order", json={
    'table_name': 'T-1',
    'order_type': 'dine-in',
    'items': [{'id': item_id, 'quantity': 2, 'price': 150}]
})
if order_resp.status_code != 200:
    sys.exit("FAILED: Could not place order.")
print("   ✓ Order placed.")

# 7. Verify Admin sees English name
print("\n[Admin] Checking Live Orders...")
live_orders_resp = s.get(f"{BASE_URL}/admin/live_orders")
if 'Masala Dosa' in live_orders_resp.text:
    print("   ✓ Admin Live Orders correctly shows English name 'Masala Dosa'.")
else:
    sys.exit("FAILED: Admin Live Orders does not show the English name for the item.")

if 'मसाला डोसा' in live_orders_resp.text:
    sys.exit("FAILED: Admin Live Orders is showing the Hindi name, which violates staff consistency rule.")

print("\n=== ALL PHASE 12 TESTS PASSED ===")
