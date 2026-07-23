import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Add debug prints to call_waiter
old_call_waiter = """@app.route('/api/call_waiter', methods=['POST'])
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
    
    return jsonify({'success': True})"""

new_call_waiter = """@app.route('/api/call_waiter', methods=['POST'])
@csrf.exempt
@limiter.limit("5 per minute")
def call_waiter():
    data = request.json
    table_name = data.get('table_name')
    order_id = data.get('order_id')
    
    print(f"DEBUG API: /api/call_waiter hit. Table: {table_name}, Order: {order_id}", flush=True)
    
    call = WaiterCall(table_name=table_name, order_id=order_id, status='pending')
    db.session.add(call)
    db.session.commit()
    
    # Safe fetch of time
    time_str = call.created_at.strftime('%H:%M') if call.created_at else "Now"
    
    print(f"DEBUG API: EMITTING WAITER CALL {table_name}. Payload ID: {call.id}, Time: {time_str}", flush=True)
    
    try:
        socketio.emit('new_waiter_call', {
            'id': call.id,
            'table_name': table_name,
            'order_id': order_id,
            'time': time_str
        }, namespace='/')
        print(f"DEBUG API: EMIT SUCCESSFUL for {table_name}", flush=True)
    except Exception as e:
        print(f"DEBUG API: EMIT FAILED: {e}", flush=True)
    
    return jsonify({'success': True})"""

app_py = app_py.replace(old_call_waiter, new_call_waiter)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

# Add console logs to live_orders.html
with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    live_html = f.read()

live_html = live_html.replace("socket.on('new_waiter_call', (data) => {\n        console.log(\"New Waiter Call:\", data);", 
"""console.log("Waiter call listener registered");
    socket.on('new_waiter_call', (data) => {
        console.log("RECEIVED new_waiter_call event:", data);""")

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(live_html)

print("Patched debug logs")
