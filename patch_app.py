import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
new_code = """
@app.route('/api/split_bill', methods=['POST'])
@login_required
def split_bill():
    data = request.json
    order_id = data.get('order_id')
    payment_method = data.get('payment_method')
    split_ways = int(data.get('split_ways', 1))
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'})
        
    if split_ways < 1:
        return jsonify({'success': False, 'message': 'Invalid split ways'})
        
    subtotal = sum((item.quantity * item.price_at_order) for item in order.items)
    
    discount = 0.0
    if order.coupon_code:
        c = Coupon.query.filter_by(code=order.coupon_code).first()
        if c and c.is_active:
            if c.discount_type == 'flat':
                discount = c.discount_value
            elif c.discount_type == 'percent':
                discount = (subtotal * c.discount_value) / 100.0
            if discount > subtotal: discount = subtotal
                
    taxable = subtotal - discount + order.delivery_charge
    gst_amount = taxable * 0.05
    exact_total = taxable + gst_amount
    rounded_total = round(exact_total)
    
    split_amount = rounded_total // split_ways
    remainder = rounded_total % split_ways
    
    invoices_created = []
    
    for i in range(split_ways):
        amount = split_amount
        if i == split_ways - 1:
            amount += remainder # Last split gets remainder
            
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        next_num = 1 if not last_invoice else int(last_invoice.invoice_number.split('-')[1]) + 1
        inv_number = f"MB-{str(next_num).zfill(5)}"
        
        prorated_sub = subtotal / split_ways
        prorated_gst = gst_amount / split_ways
        prorated_del = order.delivery_charge / split_ways
        prorated_disc = discount / split_ways
        
        inv = Invoice(
            order_id=order.id,
            invoice_number=inv_number,
            subtotal=prorated_sub,
            discount=prorated_disc,
            gst_percent=5.0,
            gst_amount=prorated_gst,
            round_off=0.0,
            delivery_charge=prorated_del,
            total=amount,
            payment_method=payment_method,
            coupon_code=order.coupon_code
        )
        db.session.add(inv)
        db.session.flush()
        
        if payment_method.lower() in ['credit/udhar', 'credit']:
            ledger = CreditLedger(
                customer_name=order.customer_name or 'Unknown Customer',
                customer_mobile=order.customer_mobile or '0000000000',
                invoice_id=inv.id,
                amount=amount,
                status='outstanding'
            )
            db.session.add(ledger)
            
        invoices_created.append(inv.id)
        
    if order.table_id:
        table = Table.query.get(order.table_id)
        if table:
            table.status = 'vacant'
            table.session_start_time = None
            
    order.status = 'completed'
    db.session.commit()
    log_activity('bill_split', f"Split Order {order_id} into {split_ways} ways. Total: Rs.{rounded_total}.")
    
    return jsonify({'success': True, 'invoice_ids': invoices_created})

@app.route('/api/call_waiter', methods=['POST'])
@csrf.exempt
@limiter.limit("5 per minute")
def call_waiter():
    data = request.json
    table_name = data.get('table_name')
    order_id = data.get('order_id')
    
    call = WaiterCall(table_name=table_name, order_id=order_id, status='pending')
    db.session.add(call)
    db.session.commit()
    
    socketio.emit('new_waiter_call', {
        'id': call.id,
        'table_name': table_name,
        'order_id': order_id,
        'time': call.created_at.strftime('%H:%M')
    }, namespace='/')
    
    return jsonify({'success': True})

@app.route('/api/resolve_call/<int:call_id>', methods=['POST'])
@login_required
def resolve_call(call_id):
    call = WaiterCall.query.get(call_id)
    if call:
        call.status = 'resolved'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/submit_feedback', methods=['POST'])
@csrf.exempt
def submit_feedback():
    data = request.json
    order_id = data.get('order_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    if not order_id or not rating:
        return jsonify({'success': False})
        
    fb = Feedback(order_id=order_id, rating=int(rating), comment=comment)
    db.session.add(fb)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/feedback')
@login_required
def admin_feedback():
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    avg = 0
    if feedbacks:
        avg = sum(f.rating for f in feedbacks) / len(feedbacks)
    return render_template('admin/feedback.html', feedbacks=feedbacks, average_rating=round(avg, 1), active_page='feedback')

# --- SOCKET EVENTS ---
"""

content = content.replace("# --- SOCKET EVENTS ---", new_code)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("app.py patched successfully")
