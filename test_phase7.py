import requests
import sys
import sqlite3
import codecs

# Fix terminal encoding for ₹ symbol in Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

BASE_URL = 'http://127.0.0.1:5000'

print("=== Starting Phase 7 Tests ===")

session = requests.Session()
r_login = session.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'}, allow_redirects=True)
if "Dashboard Overview" not in r_login.text:
    print("Failed to login!")
    sys.exit(1)

# 1. Test Menu Reorder
print("\n1. Testing Category Reordering...")
# Get current categories from DB
conn = sqlite3.connect('database/restaurant.db')
c = conn.cursor()
c.execute("SELECT id, name FROM categories ORDER BY sort_order ASC")
cats = c.fetchall()

if len(cats) >= 2:
    original_order = [cat[0] for cat in cats]
    reversed_order = list(reversed(original_order))
    
    # Reverse it
    r_reorder = session.post(f"{BASE_URL}/api/reorder_categories", json={"order": reversed_order})
    if r_reorder.json().get('success'):
        # Check /menu
        r_menu = session.get(f"{BASE_URL}/menu")
        # Extract the order they appear in the HTML
        menu_html = r_menu.text
        idx1 = menu_html.find(cats[-1][1]) # The original LAST item should now be FIRST
        idx2 = menu_html.find(cats[0][1])  # The original FIRST item should now be LAST
        
        if idx1 < idx2:
            print(f"   Success: Category order reversed. ({cats[-1][1]} is now before {cats[0][1]})")
        else:
            print("   Failed: /menu did not reflect the new category order.")
            sys.exit(1)
    else:
        print("   Failed API call to reorder.")
        sys.exit(1)
else:
    print("   Not enough categories to test reorder. Skipping.")

# 2. Test Item Availability Toggle
print("\n2. Testing Item Visibility Toggle...")
c.execute("SELECT id, name FROM menu_items LIMIT 1")
item = c.fetchone()
item_id = item[0]
item_name = item[1]

# Hide it
r_toggle = session.post(f"{BASE_URL}/api/toggle_item", json={"item_id": item_id, "is_available": False})
r_menu_hide = session.get(f"{BASE_URL}/menu")
if item_name not in r_menu_hide.text:
    print(f"   Success: Item '{item_name}' successfully hidden from /menu.")
else:
    print(f"   Failed: Item '{item_name}' is still visible on /menu!")
    sys.exit(1)

# Show it again for future tests
session.post(f"{BASE_URL}/api/toggle_item", json={"item_id": item_id, "is_available": True})

# 3. Test Reports Math
print("\n3. Testing Reports Calculations...")

# Calculate expected total sales directly from DB
c.execute("SELECT sum(total) FROM invoices")
expected_sales = c.fetchone()[0] or 0.0

r_sales = session.get(f"{BASE_URL}/api/report_data?type=sales")
sales_data = r_sales.json().get('data', [])
api_total = sum(row.get('Total', 0) for row in sales_data)

if abs(expected_sales - api_total) < 0.01:
    print(f"   Success: Sales Report Total (Rs.{api_total}) matches exact DB sum.")
else:
    print(f"   Failed: Sales Report (Rs.{api_total}) mismatch with DB (Rs.{expected_sales})")
    sys.exit(1)
    
# Best selling math
r_best = session.get(f"{BASE_URL}/api/report_data?type=best_selling")
best_data = r_best.json().get('data', [])
if best_data:
    first_item_qty = best_data[0].get('Qty Sold', 0)
    if len(best_data) > 1:
        second_item_qty = best_data[1].get('Qty Sold', 0)
        if first_item_qty >= second_item_qty:
            print(f"   Success: Best selling report correctly sorted descending (Top: {best_data[0].get('Item')} with {first_item_qty} sold).")
        else:
            print("   Failed: Best selling report is not sorted correctly.")
            sys.exit(1)
else:
    print("   No items sold yet, skipping best seller check.")

conn.close()

print("\n=== All Phase 7 Tests Passed Successfully! ===")
