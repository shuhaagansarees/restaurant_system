import re

with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace inset: 0; with top: 0; left: 0; right: 0; bottom: 0; width: 100%; height: 100%;
html = html.replace('inset: 0;', 'top: 0; left: 0; right: 0; bottom: 0; width: 100%; height: 100%;')

with open('templates/admin/items.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Fixed modal CSS')
