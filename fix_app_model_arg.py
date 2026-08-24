with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

app_code = app_code.replace("is_auto_tracked=True", "")
app_code = app_code.replace("low_stock_threshold=5, )", "low_stock_threshold=5)")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
