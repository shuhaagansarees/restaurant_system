import os
import shutil

# Remove DB to simulate fresh start
db_path = os.path.join('database', 'restaurant.db')
if os.path.exists(db_path):
    os.remove(db_path)

from app import app, db
from models import Order, MenuItem, Branch, OrderItem

client = app.test_client()

with app.app_context():
    print("--- Testing fresh DB order endpoints ---")
    # At this point, app.py executes its top-level code including db.create_all() and the migration try/except block.
    
    # Let's place an order to get a valid ID
    branch = Branch.query.first()
    item = MenuItem.query.first()
    
    order = Order(branch_id=branch.id, type='dine-in', status='new')
    db.session.add(order)
    db.session.flush()
    
    oi = OrderItem(order_id=order.id, menu_item_id=item.id, quantity=1, price_at_order=item.price)
    db.session.add(oi)
    db.session.commit()
    
    valid_id = order.id
    
    print(f"\n1. Fetching VALID order /order/{valid_id}")
    res = client.get(f'/order/{valid_id}')
    print(f"Status Code: {res.status_code}")
    print(f"Contains 'Order #{valid_id}': {'Order #'+str(valid_id) in res.data.decode('utf-8')}")
    
    print(f"\n2. Fetching VALID edit_order /admin/edit_order/{valid_id} (Requires Login)")
    # Must login first
    import re
    login_page = client.get('/admin/login').data.decode('utf-8')
    match = re.search(r'<meta name="csrf-token" content="([^"]+)">', login_page)
    if not match: match = re.search(r'<input type="hidden" name="csrf_token" value="([^"]+)"/>', login_page)
    csrf = match.group(1) if match else ''
    client.post('/admin/login', data={'mobile': '7999620244', 'password': 'shivshakti@2000', 'csrf_token': csrf})
    
    res2 = client.get(f'/admin/edit_order/{valid_id}')
    print(f"Status Code: {res2.status_code}")
    print(f"Contains 'Edit Order #{valid_id}': {'Edit Order #'+str(valid_id) in res2.data.decode('utf-8')}")
    
    print("\n3. Fetching INVALID order /order/9999")
    res3 = client.get('/order/9999')
    print(f"Status Code: {res3.status_code}")
    print(f"Title: {re.search(r'<title>(.*?)</title>', res3.data.decode('utf-8')).group(1)}")
    
    print("\n4. Fetching INVALID edit_order /admin/edit_order/9999")
    res4 = client.get('/admin/edit_order/9999')
    print(f"Status Code: {res4.status_code}")
    print(f"Title: {re.search(r'<title>(.*?)</title>', res4.data.decode('utf-8')).group(1)}")
