import requests
import sys
import sqlite3
import codecs

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
BASE_URL = 'http://127.0.0.1:5000'

print("=== Testing 4 New Reports ===")

session = requests.Session()
session.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'}, allow_redirects=True)

# Helper to fetch report
def get_report(rtype):
    return session.get(f"{BASE_URL}/api/report_data?type={rtype}").json().get('data', [])

# 1. AOV
print("\n1. Testing Average Order Value Report...")
aov_data = get_report('aov')
conn = sqlite3.connect('database/restaurant.db')
c = conn.cursor()
c.execute("SELECT sum(total), count(id) FROM invoices")
inv_sum, inv_count = c.fetchone()
expected_aov = inv_sum / inv_count if inv_count else 0
if aov_data:
    api_aov = aov_data[0].get('Average Order Value', 0) # Assuming 1 day for all test data
    if abs(expected_aov - float(api_aov)) < 0.01:
        print(f"   Success: AOV mathematically matches DB (Rs.{expected_aov})")
    else:
        print(f"   Failed: AOV mismatch API: {api_aov} vs DB: {expected_aov}")
        sys.exit(1)
else:
    print("   No invoice data.")

# 2. Order history
print("\n2. Testing Order History Report...")
orders_data = get_report('orders')
c.execute("SELECT count(id) FROM orders")
db_order_count = c.fetchone()[0]
if len(orders_data) == db_order_count:
    print(f"   Success: Total orders pulled matches exact DB count ({db_order_count})")
else:
    print("   Failed: Order count mismatch.")
    sys.exit(1)

# 3. Customers (New vs Returning)
print("\n3. Testing Customers Insight...")
cust_data = get_report('customers')
c.execute("SELECT count(DISTINCT customer_mobile) FROM orders WHERE customer_mobile IS NOT NULL AND customer_mobile != ''")
db_cust_count = c.fetchone()[0]
if len(cust_data) == db_cust_count:
    print(f"   Success: Extracted exact number of unique mobile customers ({db_cust_count}).")
    for cust in cust_data:
        print(f"      - {cust.get('Mobile')} ({cust.get('Status')} - {cust.get('Total Orders (Visits)')} visits, LTV: Rs.{cust.get('Lifetime Value')})")
else:
    print(f"   Failed: Unique mobile count mismatch API:{len(cust_data)} DB:{db_cust_count}.")
    sys.exit(1)

# 4. Cancellations
print("\n4. Testing Cancellations Report...")
canc_data = get_report('cancellations')
if canc_data:
    api_canc = sum(row.get('Cancelled Orders', 0) for row in canc_data)
    c.execute("SELECT count(id) FROM orders WHERE status = 'cancelled'")
    db_canc = c.fetchone()[0]
    if api_canc == db_canc:
        print(f"   Success: Cancellations match DB perfectly ({api_canc}).")
    else:
        print(f"   Failed: Cancellation mismatch API:{api_canc} DB:{db_canc}")
        sys.exit(1)
else:
    print("   No orders data.")

conn.close()
print("\n=== ALL REPORT TESTS PASSED ===")
