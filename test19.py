import re
with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    html = f.read()
match = re.search(r'action="/admin/items/delete.*?onsubmit="(.*?)"', html)
if match:
    print(match.group(1))
