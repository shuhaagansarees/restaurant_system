import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

new_combos = '''            {'name': 'Sandwich Snack Combo', 'desc': 'Veg Cheese Sandwich + Cold Drink', 'price': 99.0, 'img': '/static/img/combos/sandwich_snack_combo.jpg'},
            {'name': 'Peri Peri Paneer Pizza Combo', 'desc': 'Peri Peri Paneer Pizza + Cold Coffee (Classic)', 'price': 139.0, 'img': '/static/img/combos/peri_peri_paneer_pizza_combo.jpg'},
            {'name': 'Classic Burger Combo', 'desc': 'Standard Veg Burger + Salted Fries + Cold Drink (of your choice)', 'price': 129.0, 'img': '/static/img/combos/classic_burger_combo.jpg'}'''

app_code = app_code.replace("{'name': 'Sandwich Snack Combo', 'desc': 'Veg Cheese Sandwich + Cold Drink', 'price': 99.0, 'img': '/static/img/combos/sandwich_snack_combo.jpg'}", new_combos)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Updated app.py with the two new combos.")
