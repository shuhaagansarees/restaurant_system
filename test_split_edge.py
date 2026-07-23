import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from models import Order, OrderItem, MenuItem, Table, Invoice

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    c = app.test_client()
    
    print("Testing Split Bill Remainder Handling...")
    
    table = Table.query.first()
    menu_item = MenuItem.query.first()
    
    # We will manipulate the price_at_order to force an exact taxable amount
    # Taxable amount = base price. We want Exact Total (incl GST) to be exactly 1000 for test 1
    # GST is 5%, so exact_total = taxable * 1.05
    # taxable = 1000 / 1.05 = 952.38095
    
    # ---------------- TEST 1: 3-Way Split of EXACTLY Rs. 1000 (after 5% GST rounding) ----------------
    base_price_1 = 1000 / 1.05
    
    order1 = Order(branch_id=table.branch_id, table_id=table.id, type='dine-in', status='served', customer_name='Test 1', customer_mobile='1111', delivery_charge=0.0)
    db.session.add(order1)
    db.session.commit()
    
    item1 = OrderItem(order_id=order1.id, menu_item_id=menu_item.id, quantity=1, price_at_order=base_price_1)
    db.session.add(item1)
    db.session.commit()
    
    c.post('/admin/login', data={'mobile': '9999999999', 'password': 'admin123'})
    
    print(f"\n--- Test 1: Split Rs. 1000 into 3 Ways ---")
    res1 = c.post('/api/split_bill', json={'order_id': order1.id, 'payment_method': 'cash', 'split_ways': 3})
    data1 = res1.json
    
    if data1['success']:
        inv_ids1 = data1['invoice_ids']
        invoices1 = Invoice.query.filter(Invoice.id.in_(inv_ids1)).order_by(Invoice.id.asc()).all()
        total_sum1 = sum(inv.total for inv in invoices1)
        for i, inv in enumerate(invoices1, 1):
            print(f"Invoice {i}: Total Rs.{inv.total}")
        print(f"Sum of 3 invoices: Rs.{total_sum1} (Original Expected: Rs.1000)")
        
    # ---------------- TEST 2: 5-Way Split of Rs. 1004 (after 5% GST rounding) ----------------
    base_price_2 = 1004 / 1.05
    
    order2 = Order(branch_id=table.branch_id, table_id=table.id, type='dine-in', status='served', customer_name='Test 2', customer_mobile='2222', delivery_charge=0.0)
    db.session.add(order2)
    db.session.commit()
    
    item2 = OrderItem(order_id=order2.id, menu_item_id=menu_item.id, quantity=1, price_at_order=base_price_2)
    db.session.add(item2)
    db.session.commit()
    
    print(f"\n--- Test 2: Split Rs. 1004 into 5 Ways ---")
    res2 = c.post('/api/split_bill', json={'order_id': order2.id, 'payment_method': 'cash', 'split_ways': 5})
    data2 = res2.json
    
    if data2['success']:
        inv_ids2 = data2['invoice_ids']
        invoices2 = Invoice.query.filter(Invoice.id.in_(inv_ids2)).order_by(Invoice.id.asc()).all()
        total_sum2 = sum(inv.total for inv in invoices2)
        for i, inv in enumerate(invoices2, 1):
            print(f"Invoice {i}: Total Rs.{inv.total}")
        print(f"Sum of 5 invoices: Rs.{total_sum2} (Original Expected: Rs.1004)")
