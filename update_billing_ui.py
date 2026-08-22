import re

with open('templates/admin/billing.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove GST row from UI
html = re.sub(r'<div class="summary-row">\s*<span>GST \(5%\)</span>\s*<span id="txt-gst">.*?</span>\s*</div>', '', html)

# Change calculation
html = html.replace('let gst = taxable * 0.05;', 'let gst = taxable * 0.0;')

with open('templates/admin/billing.html', 'w', encoding='utf-8') as f:
    f.write(html)
