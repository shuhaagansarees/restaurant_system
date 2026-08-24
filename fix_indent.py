with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

app_code = app_code.replace("              combo_cat = Category.query.filter_by(name='Combos').first()", "        combo_cat = Category.query.filter_by(name='Combos').first()")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
