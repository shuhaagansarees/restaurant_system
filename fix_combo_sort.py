import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

# I will update the seed script part that creates or fetches the combo category
# Currently it is:
# combo_cat = Category.query.filter_by(name='Combos').first()
# if not combo_cat:
#     max_sort = db.session.query(db.func.max(Category.sort_order)).scalar() or 0
#     combo_cat = Category(name='Combos', sort_order=max_sort + 1)
#     db.session.add(combo_cat)
#     db.session.commit()

# I want to add:
# combo_cat.sort_order = -1
# db.session.commit()

new_cat_code = '''        combo_cat = Category.query.filter_by(name='Combos').first()
        if not combo_cat:
            combo_cat = Category(name='Combos', sort_order=-1)
            db.session.add(combo_cat)
        else:
            combo_cat.sort_order = -1
        db.session.commit()'''

app_code = re.sub(r"combo_cat = Category\.query\.filter_by\(name='Combos'\)\.first\(\).*?db\.session\.commit\(\)", new_cat_code, app_code, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Updated app.py to set Combos sort_order to -1")
