import re

with open('templates/customer/status.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Call Waiter button
call_waiter_html = """
    {% if order.table and order.status not in ['completed', 'cancelled'] %}
    <div style="margin-top: 15px; text-align: center;">
        <button onclick="callWaiter('{{ order.table.name }}', {{ order.id }})" class="btn-primary" style="background: var(--brand-orange); border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%;">
            🛎️ Call Waiter
        </button>
    </div>
    {% endif %}
"""
content = content.replace("{% if order.table and order.status not in ['completed', 'cancelled'] %}", call_waiter_html + "\n    {% if order.table and order.status not in ['completed', 'cancelled'] %}")

# Add Feedback form
feedback_html = """
    {% if order.status|lower == 'completed' %}
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
    {% endif %}
"""
content = content.replace("</div>\n{% endblock %}", feedback_html + "\n</div>\n{% endblock %}")

# Add JS functions
js_code = """
    let selectedRating = 0;
    
    document.addEventListener('DOMContentLoaded', () => {
        const stars = document.querySelectorAll('#star-rating span');
        if (stars) {
            stars.forEach(star => {
                star.addEventListener('click', (e) => {
                    selectedRating = parseInt(e.target.dataset.value);
                    stars.forEach((s, idx) => {
                        s.style.color = idx < selectedRating ? '#f59e0b' : '#ccc';
                    });
                });
            });
        }
    });

    function callWaiter(tableName, orderId) {
        fetch('/api/call_waiter', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ table_name: tableName, order_id: orderId })
        }).then(r => r.json()).then(data => {
            if (data.success) {
                alert('Waiter has been called!');
            }
        });
    }
    
    function submitFeedback(orderId) {
        if (!selectedRating) {
            alert('Please select a star rating.');
            return;
        }
        const comment = document.getElementById('feedback-comment').value;
        fetch('/api/submit_feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ order_id: orderId, rating: selectedRating, comment: comment })
        }).then(r => r.json()).then(data => {
            if (data.success) {
                document.getElementById('feedback-section').innerHTML = '<h4 style="color: green;">Thank you for your feedback! ✅</h4>';
            }
        });
    }
</script>
"""
content = content.replace("</script>", js_code)

with open('templates/customer/status.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("status.html patched")
