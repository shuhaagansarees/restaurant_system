import re

# 1. Update app.py order_status route
with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

old_route = """@app.route('/order/<int:order_id>')
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    total_amount = sum(item.price_at_order * item.quantity for item in order.items)
    return render_template('customer/status.html', order=order, total_amount=total_amount)"""

new_route = """@app.route('/order/<int:order_id>')
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    total_amount = sum(item.price_at_order * item.quantity for item in order.items)
    has_feedback = Feedback.query.filter_by(order_id=order_id).first() is not None
    return render_template('customer/status.html', order=order, total_amount=total_amount, has_feedback=has_feedback)"""

app_py = app_py.replace(old_route, new_route)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

# 2. Update status.html
with open('templates/customer/status.html', 'r', encoding='utf-8') as f:
    status_html = f.read()

old_feedback_if = "{% if order.status|lower == 'completed' %}"
new_feedback_if = "{% if order.status|lower == 'completed' and not has_feedback %}"
status_html = status_html.replace(old_feedback_if, new_feedback_if)

# Let's add an else block if they already submitted feedback
status_html = status_html.replace("""<button onclick="submitFeedback({{ order.id }})" class="btn-primary" style="width: 100%;">Submit Feedback</button>
    </div>
    {% endif %}""", """<button onclick="submitFeedback({{ order.id }})" class="btn-primary" style="width: 100%;">Submit Feedback</button>
    </div>
    {% elif order.status|lower == 'completed' and has_feedback %}
    <div style="margin-top: 20px; padding: 15px; background: #fff; border-radius: 12px; border: 1px solid var(--border-color); text-align: center;">
        <h4 style="color: green;">Thank you for your feedback! ✅</h4>
    </div>
    {% endif %}""")

# 3. Add window.location.reload() inside the socket handler
# Let's replace the whole socket handler logic
old_js = """            // Remove all existing status classes
            circle.className = `status-circle status-${status}`;
            text.innerText = status.toUpperCase();
            
            if (status === 'new') icon.innerText = '⏳';
            else if (status === 'preparing') icon.innerText = '🍳';
            else if (status === 'served' || status === 'completed') icon.innerText = '✅';
            
            // Optionally reload page for full sync
            // window.location.reload();"""
new_js = """            // We reload the page to ensure the feedback form and buttons are accurately shown/hidden
            window.location.reload();"""
            
status_html = status_html.replace(old_js, new_js)

with open('templates/customer/status.html', 'w', encoding='utf-8') as f:
    f.write(status_html)

print("Feedback patched successfully")
