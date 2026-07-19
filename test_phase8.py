import requests
import sys
import codecs

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
BASE_URL = 'http://127.0.0.1:5000'

print("=== Testing Phase 8: Role-Based Permissions ===")

# 1. Test Waiter Access
print("\n1. Testing Waiter Permissions...")
s_waiter = requests.Session()
r = s_waiter.post(f"{BASE_URL}/admin/login", data={'mobile': '7777777777', 'password': 'waiter123'})

if "Dashboard Overview" not in r.text: sys.exit("Failed Waiter Login")

# Waiter SHOULD access Live Orders
r_allowed = s_waiter.get(f"{BASE_URL}/admin/live_orders")
if r_allowed.status_code == 200:
    print("   ✓ Waiter CAN access /admin/live_orders")
else:
    sys.exit("   Failed: Waiter blocked from Live Orders")

# Waiter SHOULD NOT access Billing
r_denied = s_waiter.get(f"{BASE_URL}/admin/billing")
if r_denied.status_code == 403:
    print("   ✓ Waiter BLOCKED from /admin/billing (403 Forbidden)")
else:
    sys.exit(f"   Failed: Waiter got status {r_denied.status_code} on Billing instead of 403!")

# 2. Test Cashier Access
print("\n2. Testing Cashier Permissions...")
s_cashier = requests.Session()
s_cashier.post(f"{BASE_URL}/admin/login", data={'mobile': '5555555555', 'password': 'cashier123'})

# Cashier SHOULD access Billing
r_allowed_c = s_cashier.get(f"{BASE_URL}/admin/billing")
if r_allowed_c.status_code == 200:
    print("   ✓ Cashier CAN access /admin/billing")
else:
    sys.exit("   Failed: Cashier blocked from Billing")
    
# Cashier SHOULD NOT access Categories
r_denied_c = s_cashier.get(f"{BASE_URL}/admin/categories")
if r_denied_c.status_code == 403:
    print("   ✓ Cashier BLOCKED from /admin/categories (403 Forbidden)")
else:
    sys.exit(f"   Failed: Cashier got status {r_denied_c.status_code} on Categories instead of 403!")

# 3. Test Admin Access
print("\n3. Testing Admin Permissions...")
s_admin = requests.Session()
s_admin.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})

# Admin SHOULD access Staff Management
r_staff = s_admin.get(f"{BASE_URL}/admin/staff")
if r_staff.status_code == 200 and "Staff Accounts" in r_staff.text:
    print("   ✓ Admin CAN access /admin/staff")
else:
    sys.exit("   Failed: Admin blocked from Staff Management")

# Waiter SHOULD NOT access Staff Management
if s_waiter.get(f"{BASE_URL}/admin/staff").status_code == 403:
    print("   ✓ Waiter BLOCKED from /admin/staff (403 Forbidden)")
else:
    sys.exit("   Failed: Waiter accessed Staff Management!")

print("\n=== ALL ROLE-BASED TESTS PASSED ===")
