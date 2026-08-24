with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

# Add ALTER TABLE
alter_table_code = '''
        try:
            db.session.execute(text('ALTER TABLE menu_items ADD COLUMN image_url VARCHAR(255)'))
            db.session.commit()
        except Exception:
            db.session.rollback()
'''

if 'ALTER TABLE menu_items ADD COLUMN image_url' not in app_code:
    app_code = app_code.replace("except Exception:\n            db.session.rollback()\n\n        # Insert defaults", "except Exception:\n            db.session.rollback()\n" + alter_table_code + "\n        # Insert defaults")

seed_code = '''
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
            {'name': 'Sandwich Snack Combo', 'desc': 'Veg Cheese Sandwich + Cold Drink', 'price': 99.0, 'img': '/static/img/combos/sandwich_snack_combo.jpg'}
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

if '# Seed Combos' not in app_code:
    # Find the right place to insert this in app.py's app_context block
    # Searching for: admin = User.query.filter_by(mobile='8141005168').first()
    app_code = app_code.replace("admin = User.query.filter_by(mobile='8141005168').first()", seed_code + "\n        admin = User.query.filter_by(mobile='8141005168').first()")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
print("Updated app.py with DB migrations and seed data for Combos.")
