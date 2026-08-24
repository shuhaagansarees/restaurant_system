import re

# 1. Update models.py
with open('models.py', 'r', encoding='utf-8') as f:
    models = f.read()

ist_helper = '''from datetime import datetime, timedelta

def ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)
'''

models = models.replace('from datetime import datetime', ist_helper)
models = models.replace('default=datetime.utcnow().date', 'default=lambda: ist_now().date()')
models = models.replace('default=datetime.utcnow', 'default=ist_now')

with open('models.py', 'w', encoding='utf-8') as f:
    f.write(models)
print("Updated models.py")

# 2. Update app.py
with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

# Make sure we don't duplicate ist_now
if 'def ist_now():' not in app_code:
    app_code = app_code.replace('from datetime import datetime, timedelta', 'from datetime import datetime, timedelta\n\ndef ist_now():\n    return datetime.utcnow() + timedelta(hours=5, minutes=30)\n')

# There's a line: ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
# We should change the local variable name to avoid conflict, or just let it be if we remove it.
# Let's replace datetime.utcnow with ist_now globally. But wait, ist_now is a function now.
# So datetime.utcnow() becomes ist_now().
# And datetime.utcnow without parens (if any left) becomes ist_now.
app_code = app_code.replace('ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)', 'current_ist_time = ist_now()')
# Also replace ist_now. with current_ist_time. since it's an object
app_code = app_code.replace('ist_today_start = ist_now.replace(', 'ist_today_start = current_ist_time.replace(')

app_code = app_code.replace('datetime.utcnow()', 'ist_now()')

# Handle any remaining default=datetime.utcnow in app.py just in case
app_code = app_code.replace('datetime.utcnow', 'ist_now')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
print("Updated app.py")

