import socketio
import requests
import time
import sys

BASE_URL = 'http://127.0.0.1:5000'
sio_admin = socketio.Client()
sio_customer = socketio.Client()

admin_events = []
customer_events = []

@sio_admin.on('new_order')
def on_new_order(data):
    print("ADMIN RECEIVED new_order:", data)
    admin_events.append(data)

@sio_customer.on('order_status_update')
def on_order_status(data):
    print("CUSTOMER RECEIVED order_status_update:", data)
    customer_events.append(data)

print("Connecting Admin WebSocket...")
sio_admin.connect(BASE_URL)

print("Customer places a new order via API...")
payload = {
    "table_name": "T-1",
    "order_type": "dine-in",
    "customer_name": "WebSocket Tester",
    "customer_mobile": "9998887776",
    "items": [{"id": 1, "quantity": 1, "price": 250.0}]
}
r1 = requests.post(f"{BASE_URL}/api/place_order", json=payload)
order_id = r1.json()['order_id']
print(f"Order Placed! ID: {order_id}")

print("Waiting for Admin WebSocket to receive the event...")
time.sleep(2)

if not admin_events or admin_events[-1]['order_id'] != order_id:
    print("FAILED: Admin did not receive new_order via WebSocket.")
    sys.exit(1)

print("Success: Admin received the new_order WebSocket event instantly.")

print("\nConnecting Customer WebSocket...")
sio_customer.connect(BASE_URL)

print("Admin marks order as 'preparing' via API...")
session = requests.Session()
# Need to login to call admin API
session.post(f"{BASE_URL}/admin/login", data={'mobile': '9999999999', 'password': 'admin123'})

r2 = session.post(f"{BASE_URL}/api/update_order_status", json={"order_id": order_id, "status": "preparing"})
print("Admin update response:", r2.json())

print("Waiting for Customer WebSocket to receive the event...")
time.sleep(2)

if not customer_events or customer_events[-1]['status'] != 'preparing':
    print("FAILED: Customer did not receive order_status_update via WebSocket.")
    sys.exit(1)

print("Success: Customer received the status update WebSocket event instantly.")

sio_admin.disconnect()
sio_customer.disconnect()
print("\nAll Real-Time Sync Tests Passed Successfully!")
