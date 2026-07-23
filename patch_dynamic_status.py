import re

with open('templates/customer/status.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Wrap action buttons in a container
old_buttons = """    {% if order.table and order.status not in ['completed', 'cancelled'] %}
    <div style="margin-top: 15px; text-align: center;">
        <button onclick="callWaiter('{{ order.table.name }}', {{ order.id }})" class="btn-primary" style="background-color: var(--danger); width: 100%; display: block; text-align: center; text-decoration: none; font-size: 1.1rem; padding: 14px;">
            🛎️ Call Waiter
        </button>
    </div>
    {% endif %}

    {% if order.table and order.status not in ['completed', 'cancelled'] %}
    <div style="margin-top: 20px;">
        <a href="{{ url_for('menu', table=order.table.name) }}" class="btn-primary" style="display: block; text-align: center; text-decoration: none;">+ Order More Items</a>
        <p style="text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-top: 8px;">Items will be added to your existing bill.</p>
    </div>
    {% endif %}"""

new_buttons = """    <div id="action-buttons-container" style="display: {% if order.status in ['completed', 'cancelled'] or not order.table %}none{% else %}block{% endif %};">
        <div style="margin-top: 15px; text-align: center;">
            <button onclick="callWaiter('{{ order.table.name if order.table else '' }}', {{ order.id }})" class="btn-primary" style="background-color: var(--danger); width: 100%; display: block; text-align: center; text-decoration: none; font-size: 1.1rem; padding: 14px;">
                🛎️ Call Waiter
            </button>
        </div>
        <div style="margin-top: 20px;">
            <a href="{{ url_for('menu', table=order.table.name if order.table else '') }}" class="btn-primary" style="display: block; text-align: center; text-decoration: none;">+ Order More Items</a>
            <p style="text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-top: 8px;">Items will be added to your existing bill.</p>
        </div>
    </div>"""
content = content.replace(old_buttons, new_buttons)

# 2. Make Feedback Section always present but hidden if not completed
old_feedback = """    {% if order.status|lower == 'completed' and not has_feedback %}
    <div id="feedback-section" style="margin-top: 20px; padding: 15px; background: #fff; border-radius: 12px; border: 1px solid var(--border-color); text-align: center;">
        <h4>How was your food?</h4>
        <div id="star-rating" style="font-size: 2rem; color: #ccc; cursor: pointer; margin: 10px 0;">
            <span data-value="1">★</span>
            <span data-value="2">★</span>
            <span data-value="3">★</span>
            <span data-value="4">★</span>
            <span data-value="5">★</span>
        </div>
        <textarea id="feedback-comment" placeholder="Any comments? (Optional)" style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 10px;"></textarea>
        <button onclick="submitFeedback({{ order.id }})" class="btn-primary" style="width: 100%;">Submit Feedback</button>
    </div>
    {% elif order.status|lower == 'completed' and has_feedback %}
    <div style="margin-top: 20px; padding: 15px; background: #fff; border-radius: 12px; border: 1px solid var(--border-color); text-align: center;">
        <h4 style="color: green;">Thank you for your feedback! ✅</h4>
    </div>
    {% endif %}"""

new_feedback = """    <div id="feedback-container" style="display: {% if order.status|lower == 'completed' %}block{% else %}none{% endif %};">
        {% if not has_feedback %}
        <div id="feedback-section" style="margin-top: 20px; padding: 15px; background: #fff; border-radius: 12px; border: 1px solid var(--border-color); text-align: center;">
            <h4>How was your food?</h4>
            <div id="star-rating" style="font-size: 2rem; color: #ccc; cursor: pointer; margin: 10px 0;">
                <span data-value="1">★</span>
                <span data-value="2">★</span>
                <span data-value="3">★</span>
                <span data-value="4">★</span>
                <span data-value="5">★</span>
            </div>
            <textarea id="feedback-comment" placeholder="Any comments? (Optional)" style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 10px;"></textarea>
            <button onclick="submitFeedback({{ order.id }})" class="btn-primary" style="width: 100%;">Submit Feedback</button>
        </div>
        {% else %}
        <div style="margin-top: 20px; padding: 15px; background: #fff; border-radius: 12px; border: 1px solid var(--border-color); text-align: center;">
            <h4 style="color: green;">Thank you for your feedback! ✅</h4>
        </div>
        {% endif %}
    </div>"""
content = content.replace(old_feedback, new_feedback)

# 3. Modify WebSocket JS
old_js = """            // We reload the page to ensure the feedback form and buttons are accurately shown/hidden
            window.location.reload();"""
new_js = """            // Remove all existing status classes
            circle.className = `status-circle status-${status}`;
            text.innerText = status.toUpperCase();
            
            if (status === 'new') icon.innerText = '⏳';
            else if (status === 'preparing') icon.innerText = '🍳';
            else if (status === 'served' || status === 'completed') icon.innerText = '✅';
            
            if (status === 'completed') {
                const feedbackContainer = document.getElementById('feedback-container');
                if (feedbackContainer) feedbackContainer.style.display = 'block';
                
                const actionBtns = document.getElementById('action-buttons-container');
                if (actionBtns) actionBtns.style.display = 'none';
                
                // Hide tracker
                if (circle) circle.style.display = 'none';
            }"""
content = content.replace(old_js, new_js)

with open('templates/customer/status.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Dynamic JS patched in status.html")
