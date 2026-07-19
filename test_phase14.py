import requests
import sys
import codecs
import time

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
BASE_URL = 'http://127.0.0.1:5000'

print("=== Testing Phase 14: Production & E2E Validation ===")

s = requests.Session()

try:
    print("\n[Action] Logging in as Admin...")
    r = s.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})
    
    print("\n[Action] Accessing Live Orders dashboard...")
    live_orders_resp = s.get(f"{BASE_URL}/admin/live_orders")
    if live_orders_resp.status_code == 200:
        print("   ✓ Live Orders accessible.")
    else:
        sys.exit("FAILED to load live orders")

    print("\n[Action] Accessing Live Tables dashboard...")
    tables_resp = s.get(f"{BASE_URL}/admin/live_tables")
    if tables_resp.status_code == 200:
        print("   ✓ Live Tables accessible.")
    else:
        sys.exit("FAILED to load live tables")
        
    print("\n[Action] Accessing Customer Menu...")
    menu_resp = s.get(f"{BASE_URL}/menu")
    if menu_resp.status_code == 200:
        print("   ✓ Customer Menu accessible.")
    else:
        sys.exit("FAILED to load customer menu")
        
    print("\n=== ALL SYSTEM CHECKS PASSED (PRODUCTION MODE) ===")

except Exception as e:
    print(f"FAILED: {str(e)}")
    sys.exit(1)
