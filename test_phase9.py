import requests
import sys
import codecs
import time

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
BASE_URL = 'http://127.0.0.1:5000'

print("=== Testing Phase 9: Activity Log ===")

# 1. Staff Logins
print("\n1. Triggering Staff Logins...")
s_waiter = requests.Session()
s_waiter.post(f"{BASE_URL}/admin/login", data={'mobile': '7777777777', 'password': 'waiter123'})

s_admin = requests.Session()
s_admin.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})

s_cashier = requests.Session()
s_cashier.post(f"{BASE_URL}/admin/login", data={'mobile': '5555555555', 'password': 'cashier123'})

# 2. Waiter Action (Update Order Status)
print("2. Waiter creates and moves an order...")
# First create an order
r0 = s_waiter.post(f"{BASE_URL}/api/place_order", json={'table_id': 1, 'order_type': 'dine-in', 'items': [{'id': 1, 'quantity': 2, 'price': 100}]})
print("Create order:", r0.status_code, r0.text)
order_id = r0.json().get('order_id', 1)

# Waiter changes order to served
r1 = s_waiter.post(f"{BASE_URL}/api/update_order_status", json={'order_id': order_id, 'status': 'served'})
print("Waiter update:", r1.status_code, r1.text)

# 3. Admin Action (Toggle Item Availability)
print("3. Admin edits item...")
r2 = s_admin.post(f"{BASE_URL}/api/toggle_item", json={'item_id': 1, 'is_available': False})
print("Admin toggle:", r2.status_code, r2.text)

# 4. Cashier Action (Settle Bill)
print("4. Cashier settles a bill...")
# Need completed orders to settle... let's just make order completed first using Admin
s_admin.post(f"{BASE_URL}/api/update_order_status", json={'order_id': order_id, 'status': 'completed'})
# Now settle
r3 = s_cashier.post(f"{BASE_URL}/api/settle_bill", json={'order_ids': [order_id], 'payment_method': 'Cash', 'discount': 0})
print("Cashier settle:", r3.status_code, r3.text)

time.sleep(1) # wait for db

# 5. Check Activity Log
print("\n5. Checking Activity Logs (Admin only)...")
r_admin_log = s_admin.get(f"{BASE_URL}/admin/activity_log")
if r_admin_log.status_code != 200:
    sys.exit("Failed: Admin could not access /admin/activity_log")
    
html = r_admin_log.text

# We should see the names of the actors in the HTML
if 'Waiter User' in html and 'Admin User' in html and 'Cashier User' in html:
    print("   ✓ Logs successfully captured actions from multiple staff users!")
else:
    sys.exit("   Failed: Expected user names not found in the activity log HTML.")
    
if 'order_status_change' in html and 'item_availability_toggled' in html and 'bill_settled' in html:
    print("   ✓ Logs successfully captured various action types!")
else:
    sys.exit("   Failed: Expected action types not found in the activity log HTML.")

# 6. Check Role Protection on Activity Log
print("\n6. Checking Role Protection on /admin/activity_log...")
r_waiter_log = s_waiter.get(f"{BASE_URL}/admin/activity_log")
if r_waiter_log.status_code == 403:
    print("   ✓ Waiter correctly blocked with 403 Forbidden.")
else:
    sys.exit("   Failed: Waiter was not blocked!")

r_cashier_log = s_cashier.get(f"{BASE_URL}/admin/activity_log")
if r_cashier_log.status_code == 403:
    print("   ✓ Cashier correctly blocked with 403 Forbidden.")
else:
    sys.exit("   Failed: Cashier was not blocked!")

print("\n=== ALL ACTIVITY LOG TESTS PASSED ===")
