import requests
import time
import sys

time.sleep(1) # wait for server
try:
    print("Fetching /menu...")
    r1 = requests.get('http://127.0.0.1:5000/menu?table=T-1')
    print("Menu status:", r1.status_code)

    print("Placing order...")
    payload = {
        "table_name": "T-1",
        "order_type": "dine-in",
        "customer_name": "Test User",
        "customer_mobile": "1234567890",
        "items": [
            {"id": 1, "quantity": 2, "price": 250.0},
            {"id": 2, "quantity": 1, "price": 350.0}
        ]
    }
    r2 = requests.post('http://127.0.0.1:5000/api/place_order', json=payload)
    print("Order place status:", r2.status_code)
    print("Response:", r2.json())

    order_id = r2.json()['order_id']
    print("Fetching /order/" + str(order_id) + "...")
    r3 = requests.get('http://127.0.0.1:5000/order/' + str(order_id))
    print("Order status page:", r3.status_code)
    
    # Check if total is calculated correctly (250*2 + 350*1 = 850)
    if "850.0" in r3.text:
        print("Page rendered successfully with correct total!")
    else:
        print("Total calculation might be wrong")
except Exception as e:
    print("Test failed:", e)
    sys.exit(1)
