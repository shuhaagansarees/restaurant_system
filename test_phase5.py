import socketio
import requests
import time
import sys

BASE_URL = 'http://127.0.0.1:5000'

print("=== Starting Phase 5 Tests ===")

session = requests.Session()
# Login first
r_login = session.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'}, allow_redirects=True)
if "Dashboard Overview" not in r_login.text:
    print("Failed to login!")
    sys.exit(1)

# 1. Test Tables Management (Create Table)
print("\n1. Testing Tables Management (Create Table)...")
r_table = session.post(f"{BASE_URL}/admin/tables", data={'name': 'VIP-1', 'capacity': '4'})
r_tables_get = session.get(f"{BASE_URL}/admin/tables")
if "VIP-1" in r_tables_get.text:
    print("   Success: Table VIP-1 created.")
else:
    print("   Failed to create table.")
    sys.exit(1)

# 2. Test QR Generation
print("\n2. Testing QR Code Generation...")
# Assuming VIP-1 got an ID, let's just test ID 1 (T-1) which exists from seed
r_qr = session.get(f"{BASE_URL}/admin/qr/1")
if r_qr.status_code == 200 and r_qr.headers.get('Content-Type') == 'image/png':
    print("   Success: QR code generated as valid PNG.")
else:
    print("   Failed to generate QR code.")
    sys.exit(1)

# 3. Test Live Tables Status Update
print("\n3. Testing Live Tables Status Update...")
r_status = session.post(f"{BASE_URL}/api/update_table_status", json={'table_id': 1, 'status': 'occupied'})
if r_status.json().get('success'):
    print("   Success: Table 1 status updated to occupied.")
else:
    print("   Failed to update table status.")
    sys.exit(1)

# 4. Test New Parcel -> Live Orders & KDS Websocket Sync
print("\n4. Testing New Parcel & KDS Sync...")
sio_admin = socketio.Client()
sio_kds = socketio.Client()

admin_received = False
kds_received = False

@sio_admin.on('new_order')
def admin_on_new(data):
    global admin_received
    print("   ADMIN WS received new_order")
    admin_received = True

@sio_kds.on('new_order')
def kds_on_new(data):
    global kds_received
    print("   KDS WS received new_order")
    kds_received = True

sio_admin.connect(BASE_URL)
sio_kds.connect(BASE_URL)

time.sleep(1)

# Simulate New Parcel POST (same as what JS does)
payload = {
    "order_type": "parcel",
    "customer_name": "Test Parcel Guy",
    "customer_mobile": "1231231234",
    "items": [{"id": 2, "quantity": 2, "price": 100.0}]
}
r_parcel = session.post(f"{BASE_URL}/api/place_order", json=payload)
if r_parcel.status_code == 200 and r_parcel.json().get('success'):
    print(f"   Success: Parcel Order Placed via API (Order ID: {r_parcel.json().get('order_id')})")
else:
    print("   Failed to place parcel order.")
    sys.exit(1)

time.sleep(2)

if admin_received and kds_received:
    print("   Success: Both Admin and Kitchen received the socket event instantly!")
else:
    print("   Failed: WebSockets did not receive the events.")
    sys.exit(1)

sio_admin.disconnect()
sio_kds.disconnect()

print("\n=== All Phase 5 Tests Passed Successfully! ===")
