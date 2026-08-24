with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

app_code = app_code.replace('def ist_now():\n    return ist_now() + timedelta(hours=5, minutes=30)', 'def ist_now():\n    return datetime.utcnow() + timedelta(hours=5, minutes=30)')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
