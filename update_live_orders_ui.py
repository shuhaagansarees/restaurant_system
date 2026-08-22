with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('const subtotal = currentSettleOrderTotal / 1.05;', 'const subtotal = currentSettleOrderTotal;')

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(html)
