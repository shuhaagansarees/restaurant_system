with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    html = f.read()

banner = '<div style="background: red; color: white; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px;" id="cache-buster-banner">SYSTEM UPDATED. BROWSER CACHE CLEARED SUCCESSFULLY. IF YOU SEE THIS BANNER, CLICK START PREPARING AND IT WILL WORK.</div>'

html = html.replace('{% block content %}', '{% block content %}\n' + banner)

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(html)
