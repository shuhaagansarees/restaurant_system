with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

app_code = app_code.replace('total_gst = total_taxable * 0.05', 'total_gst = total_taxable * 0.0')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
