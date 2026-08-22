import re

with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''    function updateStatus(orderId, newStatus) {
        try {
            const card = document.querySelector(.order-card[data-id="\\"]);
            const targetList = document.getElementById(list-\\);
            if (card && targetList) {
                targetList.appendChild(card);
                updateStatusAPI(orderId, newStatus);
                updateCardButtons(card, newStatus);
            } else {
                alert('DOM Error: Cannot find card or target list');
            }
        } catch(e) {
            alert('JS Error: ' + e);
        }
    }'''

content = re.sub(r'    function updateStatus\(orderId, newStatus\) \{[\s\S]*?    \}', new_func, content)

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
