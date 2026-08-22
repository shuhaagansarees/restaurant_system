import re

with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace async function updateStatusAPI
html = re.sub(
    r"async function updateStatusAPI\(orderId, status\) \{.*?\try \{.*?await fetch\('/api/update_order_status', \{(.*?)\}\);.*?\} catch \(err\) \{(.*?)\}.*?\}",
    r"function updateStatusAPI(orderId, status) {\n        fetch('/api/update_order_status', {\1}).catch(function(err) {\2});\n    }",
    html, flags=re.DOTALL
)

# Replace setInterval async
html = re.sub(
    r"setInterval\(async \(\) => \{",
    r"setInterval(function() {",
    html
)
html = html.replace('const resp = await fetch', '/*await*/ const resp = await fetch')

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(html)
