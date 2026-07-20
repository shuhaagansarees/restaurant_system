import re
from app import app, db
from models import Order, MenuItem, Table, Branch, OrderItem

def get_csrf(client, url):
    page = client.get(url).data.decode('utf-8')
    match = re.search(r'<meta name="csrf-token" content="([^"]+)">', page)
    if not match:
        match = re.search(r'<input type="hidden" name="csrf_token" value="([^"]+)"/>', page)
    return match.group(1) if match else ''

def run_test():
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['TESTING'] = True
    client = app.test_client()
    
    with app.app_context():
        # Setup initial login
        csrf = get_csrf(client, '/admin/login')
        client.post('/admin/login', data={'mobile': '7999620244', 'password': 'shivshakti@2000', 'csrf_token': csrf})
        
        csrf = get_csrf(client, '/admin/live_orders')
        
        branch = Branch.query.first()
        menu_items = MenuItem.query.limit(2).all()
        item1, item2 = menu_items[0], menu_items[1]
        
        # 1. Place order -> Preparing
        order = Order(branch_id=branch.id, type='dine-in', status='preparing', customer_name='FlowTest')
        db.session.add(order)
        db.session.flush()
        
        oi1 = OrderItem(order_id=order.id, menu_item_id=item1.id, quantity=2, price_at_order=item1.price)
        db.session.add(oi1)
        db.session.commit()
        
        order_id = order.id
        print(f"--- Step 1: Order #{order_id} placed, status 'preparing'")
        
        # Original Total
        total_before = sum(i.quantity * i.price_at_order for i in Order.query.get(order_id).items)
        print(f"Total before edit: Rs {total_before}")
        
        # 2. Edit Order API
        print(f"--- Step 2: Editing order (Changing qty of '{item1.name}' to 1, adding '{item2.name}' qty 1)")
        res = client.post('/api/update_order', json={
            'order_id': order_id,
            'items': [
                {'id': item1.id, 'quantity': 1, 'price': item1.price},
                {'id': item2.id, 'quantity': 1, 'price': item2.price}
            ]
        }, headers={'X-CSRFToken': csrf})
        print(f"Edit API response status: {res.status_code}")
        
        # Total after edit
        total_after = sum(i.quantity * i.price_at_order for i in Order.query.get(order_id).items)
        print(f"Total after edit: Rs {total_after}")
        
        # 3. KDS Check
        print("--- Step 3: Fetching KDS page to check for 'NEW ITEMS ADDED'")
        kds_html = client.get('/kitchen').data.decode('utf-8')
        if "NEW ITEMS ADDED" in kds_html:
            print("MATCH FOUND: 'NEW ITEMS ADDED' badge is present in KDS HTML.")
        else:
            print("NOT FOUND: 'NEW ITEMS ADDED' badge is missing in KDS HTML.")
            
        # 4. Mark Completed -> Billed
        order = Order.query.get(order_id)
        order.status = 'completed'
        db.session.commit()
        print(f"--- Step 4: Order #{order_id} status changed to 'completed' (Billed)")
        
        # 5. Try editing completed order
        print("--- Step 5: Attempting to edit completed order...")
        res2 = client.post('/api/update_order', json={
            'order_id': order_id,
            'items': [{'id': item1.id, 'quantity': 2, 'price': item1.price}]
        }, headers={'X-CSRFToken': csrf})
        
        print(f"Update completed order API response status: {res2.status_code}")
        print(f"Response JSON: {res2.get_json()}")
        
        # Cleanup
        OrderItem.query.filter_by(order_id=order_id).delete()
        Order.query.filter_by(id=order_id).delete()
        db.session.commit()

if __name__ == '__main__':
    run_test()
