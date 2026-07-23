import os
import time
from app import app, db
from models import Coupon, CustomerProfile, Order, Invoice, User

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    print("Running initial queries to ensure migrations ran...")
    
    # 1. Test Coupon creation
    c = Coupon.query.filter_by(code='TEST500').first()
    if not c:
        c = Coupon(code='TEST500', discount_type='flat', discount_value=50, min_order_amount=500)
        db.session.add(c)
        db.session.commit()
    print("Coupon TEST500 exists:", c.id)

    # 2. Test CustomerProfile creation
    p = CustomerProfile.query.filter_by(mobile='9999999999').first()
    if not p:
        p = CustomerProfile(mobile='9999999999', name='Test Customer', notes='VIP')
        db.session.add(p)
        db.session.commit()
    print("Customer profile exists:", p.name)
    
    # 3. Test Order fields
    o = Order.query.filter_by(customer_mobile='9999999999').first()
    if not o:
        o = Order(type='home-delivery', customer_mobile='9999999999', customer_name='Test', delivery_address='123 Main St', branch_id=1)
        db.session.add(o)
        db.session.commit()
    print("Delivery address on order:", o.delivery_address)
    
    # 4. API verify coupon
    c = app.test_client()
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    r1 = c.post('/api/verify_coupon', json={'code': 'TEST500', 'total': 400})
    print("Coupon 400 total:", r1.json) # Should fail min order
    
    r2 = c.post('/api/verify_coupon', json={'code': 'TEST500', 'total': 600})
    print("Coupon 600 total:", r2.json) # Should succeed
    
    print("All tests passed.")
