import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from models import Order, Feedback

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    c = app.test_client()
    
    # Let's find an order that is completed but HAS NO feedback
    # Since Order 3 has feedback, it should now show "Thank you for your feedback!"
    order3 = Order.query.get(3)
    if order3 and order3.status == 'completed':
        res3 = c.get(f'/order/{order3.id}')
        print(f"--- Output for Order {order3.id} (Has Feedback) ---")
        lines = res3.data.decode('utf-8').split('\n')
        for i, line in enumerate(lines):
            if 'Thank you for your feedback!' in line:
                print("\n".join(lines[i-2:i+3]))
                break
                
    # Now let's test one without feedback. (Order 1 or 2 are completed from Phase 19/20 tests maybe, or we can just create one)
    order_new = Order(branch_id=1, table_id=1, type='dine-in', status='completed')
    db.session.add(order_new)
    db.session.commit()
    
    res_new = c.get(f'/order/{order_new.id}')
    print(f"\n--- Output for Order {order_new.id} (No Feedback Yet) ---")
    lines_new = res_new.data.decode('utf-8').split('\n')
    for i, line in enumerate(lines_new):
        if 'id="feedback-section"' in line:
            print("\n".join(lines_new[i:i+12]))
            break
