import re

with open('live_orders_render.txt', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script.*?>\s*(.*?)\s*</script>', html, re.DOTALL)
with open('live_orders.js', 'w', encoding='utf-8') as f:
    for s in scripts:
        if s.strip():
            f.write(s + '\n')
