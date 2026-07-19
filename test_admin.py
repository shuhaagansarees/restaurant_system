import requests
import time
import sys

time.sleep(1) # Wait for server

session = requests.Session()
BASE_URL = 'http://127.0.0.1:5000'

try:
    print("1. Testing unauthenticated access to /admin/dashboard...")
    r1 = session.get(f"{BASE_URL}/admin/dashboard", allow_redirects=False)
    if r1.status_code == 302 and '/admin/login' in r1.headers.get('Location', ''):
        print("   Success: Redirected to login.")
    else:
        raise Exception(f"Failed to redirect. Status: {r1.status_code}")

    print("2. Testing invalid login...")
    r2 = session.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'wrongpassword'}, allow_redirects=True)
    if "Login - Restaurant Admin" in r2.text:
        print("   Success: Rejected invalid login and stayed on login page.")
    else:
        raise Exception("Failed to reject invalid login. Response text snippet: " + r2.text[:200])

    print("3. Testing valid login...")
    r3 = session.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'}, allow_redirects=True)
    if "Dashboard Overview" in r3.text and "Live Orders" in r3.text:
        print("   Success: Logged in and reached dashboard.")
    else:
        raise Exception("Failed to reach dashboard after valid login.")

    print("4. Testing dummy navigation link (/admin/live_orders)...")
    r4 = session.get(f"{BASE_URL}/admin/live_orders")
    if "Coming Soon" in r4.text:
        print("   Success: Dummy link rendered correctly.")
    else:
        raise Exception("Failed to render dummy link content.")

    print("5. Testing logout...")
    r5 = session.get(f"{BASE_URL}/admin/logout", allow_redirects=False)
    if r5.status_code == 302 and '/admin/login' in r5.headers.get('Location', ''):
        print("   Success: Logout redirected to login.")
    else:
        raise Exception("Failed to logout correctly.")

    print("All tests passed successfully!")

except Exception as e:
    print("Test failed:", e)
    sys.exit(1)
