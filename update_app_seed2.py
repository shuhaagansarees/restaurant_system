import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

seed_code = '''            db.session.rollback()

        # Image URL column for MenuItem
        try:
            db.session.execute(text('ALTER TABLE menu_items ADD COLUMN image_url VARCHAR(255)'))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Seed Combos
        combo_cat = Category.query.filter_by(name='Combos').first()
        if not combo_cat:
            max_sort = db.session.query(db.func.max(Category.sort_order)).scalar() or 0
            combo_cat = Category(name='Combos', sort_order=max_sort + 1)
            db.session.add(combo_cat)
            db.session.commit()
        
        combos_data = [
            {'name': 'Margherita Pizza Combo', 'desc': 'Margherita Pizza + Cold Drink (of your choice)', 'price': 129.0, 'img': '/static/img/combos/margherita_pizza_combo.jpg'},
            {'name': 'Momo Munch Combo', 'desc': 'Veg Steam Momos + Cold Drink', 'price': 99.0, 'img': '/static/img/combos/momo_munch_combo.jpg'},
            {'name': 'Aloo Tikki Frankie Combo', 'desc': 'Salted Fries + Aloo Tikki Frankie + Cold Drink', 'price': 129.0, 'img': '/static/img/combos/aloo_tikki_frankie_combo.jpg'},
            {'name': 'Frankie Fiesta Combo', 'desc': 'Paneer Frankie + Cold Coffee (Classic)', 'price': 119.0, 'img': '/static/img/combos/frankie_fiesta_combo.jpg'},
            {'name': 'Sandwich Snack Combo', 'desc': 'Veg Cheese Sandwich + Cold Drink', 'price': 99.0, 'img': '/static/img/combos/sandwich_snack_combo.jpg'},
            {'name': 'Peri Peri Paneer Pizza Combo', 'desc': 'Peri Peri Paneer Pizza + Cold Coffee (Classic)', 'price': 139.0, 'img': '/static/img/combos/peri_peri_paneer_pizza_combo.jpg'},
            {'name': 'Classic Burger Combo', 'desc': 'Standard Veg Burger + Salted Fries + Cold Drink (of your choice)', 'price': 129.0, 'img': '/static/img/combos/classic_burger_combo.jpg'}
        ]
        
        for cd in combos_data:
            mi = MenuItem.query.filter_by(name=cd['name']).first()
            if not mi:
                mi = MenuItem(
                    name=cd['name'],
                    description=cd['desc'],
                    price=cd['price'],
                    category_id=combo_cat.id,
                    is_combo=True,
                    image_url=cd['img']
                )
                db.session.add(mi)
            else:
                mi.image_url = cd['img']
        db.session.commit()
'''

app_code = app_code.replace('''        # Phase 23
        try:
            db.session.execute(text('ALTER TABLE customers ADD COLUMN loyalty_points INTEGER DEFAULT 0'))
            db.session.commit()
        except Exception:
            db.session.rollback()''', '''        # Phase 23
        try:
            db.session.execute(text('ALTER TABLE customers ADD COLUMN loyalty_points INTEGER DEFAULT 0'))
            db.session.commit()
        except Exception:
''' + seed_code)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Updated auto_migrate with DB migrations and seed data for ALL 7 Combos.")
