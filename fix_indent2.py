with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "combo_cat = Category.query.filter_by(name='Combos').first()" in line:
        lines[i] = "        combo_cat = Category.query.filter_by(name='Combos').first()\n"
        break

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
