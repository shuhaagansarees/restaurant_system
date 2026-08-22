import re
with open('live_items.html', 'r', encoding='utf-8') as f:
    html = f.read()

matches = re.findall(r'<button type="button"[^>]*onclick="openEditItemModal[^>]*>', html)
for m in matches[:2]:
    print(m)
    print("---")
