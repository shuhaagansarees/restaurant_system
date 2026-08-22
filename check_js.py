import re

with open('live_orders_render.txt', 'r', encoding='utf-8') as f:
    html = f.read()

match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if match:
    with open('live_orders.js', 'w', encoding='utf-8') as f:
        # We need to mock document, window, socket, etc. to not throw runtime errors, 
        # but node --check only checks syntax.
        f.write(match.group(1))
