import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

# Update Add Item route
# It looks like: is_combo = 'is_combo' in request.form
app_code = app_code.replace("is_combo = 'is_combo' in request.form", "is_combo = 'is_combo' in request.form\n        image_url = request.form.get('image_url')")
app_code = app_code.replace("is_combo=is_combo", "is_combo=is_combo,\n            image_url=image_url")

# Update Edit Item route
app_code = app_code.replace("item.is_combo = 'is_combo' in request.form", "item.is_combo = 'is_combo' in request.form\n        item.image_url = request.form.get('image_url')")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
