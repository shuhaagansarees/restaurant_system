import re
with open('templates/admin/billing.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(r"document\.getElementById\('txt-gst'\)\.innerText = .*?;\n", '', html)

with open('templates/admin/billing.html', 'w', encoding='utf-8') as f:
    f.write(html)
