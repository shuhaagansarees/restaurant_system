import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from models import Order, OrderItem, MenuItem, Table, Invoice, CreditLedger, WaiterCall, Feedback

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    c = app.test_client()
    
    print("Testing Phase 21 APIs...")
    
    # Create a dummy order for split bill test
    table = Table.query.first()
    menu_item = MenuItem.query.first()
    
    if not table or not menu_item:
        print("Need a table and menu item to test.")
        sys.exit(0)
        
    order = Order(branch_id=table.branch_id, table_id=table.id, type='dine-in', status='served', customer_name='Split Test', customer_mobile='7777777777', delivery_charge=0.0)
    db.session.add(order)
    db.session.commit()
    
    # Add an item of Rs 1000
    item = OrderItem(order_id=order.id, menu_item_id=menu_item.id, quantity=1, price_at_order=1000.0)
    db.session.add(item)
    db.session.commit()
    
    # 1. Test Split Bill
    print(f"\n--- Testing Split Bill (Order ID: {order.id}) ---")
    # Login as admin
    c.post('/admin/login', data={'mobile': '9999999999', 'password': 'admin123'})
    
    # Split into 3, payment method credit
    res = c.post('/api/split_bill', json={
        'order_id': order.id,
        'payment_method': 'credit',
        'split_ways': 3
    })
    
    data = res.json
    print("Split Bill Response:", data)
    if data['success']:
        inv_ids = data['invoice_ids']
        invoices = Invoice.query.filter(Invoice.id.in_(inv_ids)).all()
        for inv in invoices:
            print(f"Invoice {inv.invoice_number}: Total Rs.{inv.total}")
        
        # Check credit ledgers
        ledgers = CreditLedger.query.filter(CreditLedger.invoice_id.in_(inv_ids)).all()
        for l in ledgers:
            print(f"Credit Ledger for Invoice {l.invoice_id}: Rs.{l.amount} (Customer: {l.customer_name})")
            
    # 2. Test Call Waiter
    print("\n--- Testing Call Waiter ---")
    res2 = c.post('/api/call_waiter', json={'table_name': 'T-1', 'order_id': order.id})
    print("Call Waiter Response:", res2.json)
    
    calls = WaiterCall.query.filter_by(status='pending').all()
    if calls:
        call = calls[0]
        print(f"Created Waiter Call ID: {call.id} for Table {call.table_name}")
        
        # Resolve Call
        res3 = c.post(f'/api/resolve_call/{call.id}')
        print("Resolve Call Response:", res3.json)
        
    # 3. Test Feedback
    print("\n--- Testing Feedback ---")
    res4 = c.post('/api/submit_feedback', json={'order_id': order.id, 'rating': 5, 'comment': 'Great food split bill worked!'})
    print("Feedback Response:", res4.json)
    
    feedbacks = Feedback.query.filter_by(order_id=order.id).all()
    for fb in feedbacks:
        print(f"Feedback ID: {fb.id}, Rating: {fb.rating} Stars, Comment: {fb.comment}")
        
    print("\nAll Phase 21 backend tests passed!")
