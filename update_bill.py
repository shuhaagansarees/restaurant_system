import re

# 1. Update invoice_print.html
with open('templates/admin/invoice_print.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace address
html = html.replace('123 Main Street, City', 'Shop no 07, Shiva Park, nearby Ayodhya market, Godadara, Surat, Gujarat 395010')
# Replace phone
html = html.replace('Phone: +91 9999999999', 'Phone: +91 8141005168')
# Remove GSTIN
html = html.replace('<br>\n            GSTIN: 27AAAAA0000A1Z5', '')
html = html.replace('<br>GSTIN: 27AAAAA0000A1Z5', '')
html = re.sub(r'<br>\s*GSTIN: 27AAAAA0000A1Z5', '', html)

# Remove CGST/SGST lines in HTML table
cgst_regex = r'<tr>\s*<!-- Formula: gst = \(subtotal - discount\) \* 0\.05 -->\s*<td>CGST \(2\.5%\)</td>\s*<td class="money">{{ "%\.2f"\|format\(invoice\.gst_amount / 2\) }}</td>\s*</tr>'
html = re.sub(cgst_regex, '', html)

sgst_regex = r'<tr>\s*<td>SGST \(2\.5%\)</td>\s*<td class="money">{{ "%\.2f"\|format\(invoice\.gst_amount / 2\) }}</td>\s*</tr>'
html = re.sub(sgst_regex, '', html)

# Remove Taxes from WhatsApp share text
html = re.sub(r'billText \+= "Taxes: Rs\.{{ \'%\.2f\'\|format\(invoice\.gst_amount\) }}\\n";', '', html)

# Add Radha Pos system footer
html = html.replace('&copy; 2026 Soul Sip Cafe.<br>All rights reserved. Unauthorized copying prohibited.', '&copy; 2026 Soul Sip Cafe.<br>Radha Pos system')

with open('templates/admin/invoice_print.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated invoice_print.html")

# 2. Update app.py to set GST to 0%
with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

app_code = app_code.replace('gst_amount = taxable * 0.05', 'gst_amount = taxable * 0.0')
app_code = app_code.replace('gst_percent=5.0', 'gst_percent=0.0')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
print("Updated app.py")

# 3. Update base.html footer
with open('templates/admin/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

base_html = base_html.replace('Powered by SOUL SIP POS', 'Radha Pos system')

with open('templates/admin/base.html', 'w', encoding='utf-8') as f:
    f.write(base_html)
print("Updated base.html")
