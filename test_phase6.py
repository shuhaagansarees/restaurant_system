import requests
import time
import sys
import sqlite3

BASE_URL = 'http://127.0.0.1:5000'

print("=== Starting Phase 6 E2E Test ===")

session = requests.Session()
r_login = session.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'}, allow_redirects=True)
if "Dashboard Overview" not in r_login.text:
    print("Failed to login!")
    sys.exit(1)

# 1. Place 2 Orders
print("\n1. Placing 2 Orders...")
payload_table = {
    "order_type": "dine-in",
    "table_name": "VIP-1",
    "items": [{"id": 1, "quantity": 1, "price": 100.0}] # Assume item 1 exists
}
payload_parcel = {
    "order_type": "parcel",
    "customer_name": "Credit Customer",
    "customer_mobile": "9876543210",
    "items": [{"id": 2, "quantity": 1, "price": 200.0}]
}

r1 = session.post(f"{BASE_URL}/api/place_order", json=payload_table)
r2 = session.post(f"{BASE_URL}/api/place_order", json=payload_parcel)

if r1.status_code == 200 and r2.status_code == 200:
    order1_id = r1.json().get('order_id')
    order2_id = r2.json().get('order_id')
    print(f"   Success: Created Order {order1_id} (Dine-in) and Order {order2_id} (Parcel)")
else:
    print("   Failed to place orders.")
    sys.exit(1)

# 2. Mark as Completed
print("\n2. Marking Orders as Completed...")
session.post(f"{BASE_URL}/api/update_order_status", json={"order_id": order1_id, "status": "completed"})
session.post(f"{BASE_URL}/api/update_order_status", json={"order_id": order2_id, "status": "completed"})
print("   Success.")

# 3. Check Billing Page
print("\n3. Checking Billing Page...")
r_billing = session.get(f"{BASE_URL}/admin/billing")
if "VIP-1" in r_billing.text and "Credit Customer" in r_billing.text:
    print("   Success: Both sessions visible on billing page.")
else:
    print("   Failed: Missing sessions in billing page.")
    sys.exit(1)

# 4. Settle Bills (Cash & Credit)
print("\n4. Settling Bills...")
# Order 1 -> Cash
r_settle1 = session.post(f"{BASE_URL}/api/settle_bill", json={"order_ids": [order1_id], "discount": 0, "payment_method": "Cash"})
inv1_id = r_settle1.json().get('invoice_id')
# Order 2 -> Credit
r_settle2 = session.post(f"{BASE_URL}/api/settle_bill", json={"order_ids": [order2_id], "discount": 10, "payment_method": "Credit/Udhar"})
inv2_id = r_settle2.json().get('invoice_id')

if inv1_id and inv2_id:
    print(f"   Success: Settled into Invoice {inv1_id} and {inv2_id}")
else:
    print("   Failed to settle bills.")
    sys.exit(1)

# 5. Check Print Layout
print("\n5. Checking Print Views...")
r_print1 = session.get(f"{BASE_URL}/admin/invoices/print/{inv1_id}")
if "TAX INVOICE" in r_print1.text:
    print("   Success: Print view renders correctly.")
else:
    print("   Failed: Print view missing elements.")
    sys.exit(1)

# 6. Check Credit Ledger
print("\n6. Checking Credit / Udhar Screen...")
r_credit = session.get(f"{BASE_URL}/admin/credit")
if "Credit Customer" in r_credit.text and "9876543210" in r_credit.text:
    print("   Success: Credit entry found for customer.")
else:
    print("   Failed: Credit ledger entry missing.")
    sys.exit(1)

# Get actual invoice number for refund from DB
conn = sqlite3.connect('database/restaurant.db')
c = conn.cursor()
c.execute("SELECT invoice_number, total FROM invoices WHERE id = ?", (inv2_id,))
inv2_data = c.fetchone()
inv2_number = inv2_data[0]
inv2_original_total = inv2_data[1]

# 7. Add Refund
print("\n7. Recording Refund...")
r_refund = session.post(f"{BASE_URL}/admin/refunds", data={
    "invoice_no": inv2_number,
    "amount": "50.0",
    "reason": "Customer Complaint",
    "returned_via": "Cash",
    "status": "completed",
    "note": "Test"
}, allow_redirects=True)
if "Refund recorded successfully" in r_refund.text:
    print("   Success: Refund recorded.")
else:
    print("   Failed to record refund.")
    sys.exit(1)

# 8. Verify Original Invoice Total Unchanged
print("\n8. Verifying Original Invoice is Unchanged...")
c.execute("SELECT total FROM invoices WHERE id = ?", (inv2_id,))
inv2_new_total = c.fetchone()[0]
conn.close()

if inv2_original_total == inv2_new_total:
    print(f"   Success: Original invoice total remained Rs.{inv2_original_total}")
else:
    print(f"   Failed: Original invoice total changed from Rs.{inv2_original_total} to Rs.{inv2_new_total}!")
    sys.exit(1)

print("\n=== All Phase 6 Tests Passed Successfully! ===")
