import re
with open('templates/admin/base.html', 'r', encoding='utf-8') as f:
    html = f.read()

match = re.search(r'<div[^>]*class="[^"]*main-content[^"]*"[^>]*>', html)
if match:
    print(match.group(0))
    idx = html.find(match.group(0))
    print(html[idx:idx+500])
