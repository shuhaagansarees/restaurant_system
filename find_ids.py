import re
with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    html = f.read()
ids = re.findall(r'id="(edit_[^"]+)"', html)
print(ids)
