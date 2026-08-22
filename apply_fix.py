with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Delete lines 747 to 788 (inclusive)
# Note: Python slice is [746:788] (0-indexed)
del lines[746:789]

html = ''.join(lines)

es5_script = '''<script>
// ES5 Fallback block for ancient POS browsers (e.g. Android 4.4 / Chrome 30)
function updateStatusAPI(orderId, status) {
    try {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/update_order_status", true);
        xhr.setRequestHeader("Content-Type", "application/json");
        var csrf = document.querySelector('meta[name="csrf-token"]');
        if (csrf) {
            xhr.setRequestHeader("X-CSRFToken", csrf.getAttribute('content'));
        }
        xhr.send(JSON.stringify({ order_id: orderId, status: status }));
    } catch(e) {
        alert("API Error: " + e);
    }
}

function updateCardButtons(card, status) {
    var orderId = card.getAttribute('data-id');
    var actionDiv = card.querySelector('.order-actions');
    if (!actionDiv) return;
    
    if (status === 'preparing') {
        actionDiv.innerHTML = '<button class="btn-status" style="flex:1; background:#059669; color:white; border-color:#059669;" onclick="try{event.preventDefault();}catch(e){} updateStatus(' + orderId + ', \\'served\\')">Mark Served</button>';
    } else if (status === 'served') {
        actionDiv.innerHTML = '<button class="btn-status" style="flex:1; background:#4f46e5; color:white; border-color:#4f46e5;" onclick="try{event.preventDefault();}catch(e){} updateStatus(' + orderId + ', \\'completed\\')">Complete</button>';
    } else if (status === 'completed') {
        actionDiv.innerHTML = '';
    }
}

function updateStatus(orderId, newStatus) {
    try {
        var card = document.querySelector('.order-card[data-id="' + orderId + '"]');
        var targetList = document.getElementById('list-' + newStatus);
        if (card && targetList) {
            targetList.appendChild(card);
            updateStatusAPI(orderId, newStatus);
            updateCardButtons(card, newStatus);
            
            // Force update counts if the function exists
            if (typeof updateCounts === 'function') {
                updateCounts();
            }
        }
    } catch(e) {
        alert('Update Status Error: ' + e);
    }
}
</script>
'''

html = html.replace('{% block content %}', '{% block content %}\n' + es5_script)

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(html)
