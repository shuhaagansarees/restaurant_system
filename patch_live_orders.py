import re

with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    content = f.read()
    
# 1. Add Split Ways to Modal
split_html = """
        <div class="form-group">
            <label>Split Bill (Ways)</label>
            <input type="number" id="settle-split-ways" value="1" min="1">
            <small style="color:var(--text-secondary);">Set > 1 to divide bill equally</small>
        </div>
"""
content = content.replace('<div class="form-group">\n            <label>Payment Method</label>', split_html + '\n        <div class="form-group">\n            <label>Payment Method</label>')

# 2. Add Waiter Call Panel (floating)
waiter_html = """
<!-- Waiter Calls Panel -->
<div id="waiter-calls-panel" style="position: fixed; bottom: 20px; right: 20px; width: 300px; z-index: 9999; display: flex; flex-direction: column; gap: 10px;">
</div>
"""
content = content.replace('<!-- Audio for notification -->', waiter_html + '\n<!-- Audio for notification -->')

# 3. Update submitSettle JS
submit_js = """
    function submitSettle() {
        const method = document.getElementById('payment-method').value;
        const coupon = document.getElementById('settle-coupon').value;
        const delivery = document.getElementById('settle-delivery').value;
        const splitWays = parseInt(document.getElementById('settle-split-ways').value) || 1;
        
        let endpoint = '/api/settle_bill';
        let payload = {
            order_id: currentSettleOrderId, // Using order_ids: [currentSettleOrderId] for settle_bill compatibility
            order_ids: [currentSettleOrderId],
            payment_method: method,
            coupon_code: coupon,
            delivery_charge: delivery
        };
        
        if (splitWays > 1) {
            endpoint = '/api/split_bill';
            payload.split_ways = splitWays;
        }
        
        fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token() }}'},
            body: JSON.stringify(payload)
        }).then(r => r.json()).then(data => {
            if(data.success) {
                location.reload();
            } else {
                alert(data.message || 'Error settling bill');
            }
        });
    }
"""
content = re.sub(r'function submitSettle\(\) \{.*?\n    \}', submit_js.strip(), content, flags=re.DOTALL)

# 4. Add Waiter Call JS
waiter_js = """
    // WebSockets logic
    
    socket.on('new_waiter_call', (data) => {
        console.log("New Waiter Call:", data);
        const panel = document.getElementById('waiter-calls-panel');
        const callCard = document.createElement('div');
        callCard.id = `waiter-call-${data.id}`;
        callCard.style = "background: #ef4444; color: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center;";
        callCard.innerHTML = `
            <div>
                <strong>🛎️ Table ${data.table_name}</strong><br>
                <small>${data.time}</small>
            </div>
            <button onclick="resolveCall(${data.id})" style="background: white; color: #ef4444; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;">Resolve</button>
        `;
        panel.appendChild(callCard);
        
        const audio = document.getElementById('notif-sound');
        if (audio) {
            audio.play().catch(e => console.log('Audio play failed:', e));
        }
    });
    
    function resolveCall(callId) {
        fetch(`/api/resolve_call/${callId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token() }}'}
        }).then(r => r.json()).then(data => {
            if(data.success) {
                const el = document.getElementById(`waiter-call-${callId}`);
                if (el) el.remove();
            }
        });
    }
"""
content = content.replace("// WebSockets logic", waiter_js)

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("live_orders.html patched successfully")
