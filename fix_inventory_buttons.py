import re
with open('templates/admin/inventory.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add padding and border radius to btn-quick-add
html = html.replace('.btn-quick-add {\n    background: #f1f5f9;', '.btn-quick-add {\n    background: #f1f5f9;\n    padding: 6px 12px;\n    border-radius: 6px;\n    font-weight: 600;\n    font-size: 0.8rem;')

with open('templates/admin/inventory.html', 'w', encoding='utf-8') as f:
    f.write(html)
