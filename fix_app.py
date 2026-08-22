import re
with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

app_py = app_py.replace('db.session.delete(existing)\n            admin.mobile =', 'db.session.delete(existing)\n                db.session.flush()\n            admin.mobile =')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)
print('Fixed app.py flush')
