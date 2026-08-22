with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

app_py = app_py.replace("response.headers['X-Content-Type-Options'] = 'nosniff'", "response.headers['X-Content-Type-Options'] = 'nosniff'\n    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'\n    response.headers['Pragma'] = 'no-cache'\n    response.headers['Expires'] = '0'")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)
