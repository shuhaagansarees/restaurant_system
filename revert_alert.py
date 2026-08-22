with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_func = '''    function updateStatus(orderId, newStatus) {
        alert('updateStatus called! orderId=' + orderId + ' newStatus=' + newStatus);
        try {
            const card = document.querySelector(.order-card[data-id="\"]);
            const targetList = document.getElementById(list-\);
            alert('Card found: ' + !!card + ', TargetList found: ' + !!targetList);
            if (card && targetList) {'''

new_func = '''    function updateStatus(orderId, newStatus) {
        try {
            const card = document.querySelector(.order-card[data-id="\"]);
            const targetList = document.getElementById(list-\);
            if (card && targetList) {'''

html = html.replace(old_func, new_func)

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(html)
