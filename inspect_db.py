from app import app, db, Order, Invoice
with app.app_context():
    completed = Order.query.filter_by(status='completed').all()
    for o in completed:
        print(f"Order #{o.id}, Table {o.table_id}, Type {o.type}")
    
    invoices = Invoice.query.all()
    for i in invoices[-5:]:
        print(f"Invoice #{i.id} for Order #{i.order_id}")
