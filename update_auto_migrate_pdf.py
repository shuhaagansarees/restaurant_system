with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

# First, remove the magic route I just added
# I'll just use string replacement if possible, or leave it there and just add to auto_migrate.
# It's fine to leave it there. I will add the logic to auto_migrate!

seed_code = '''
        # Replace Menu with PDF Menu
        from menu_data import MENU_DATA
        if not Category.query.filter_by(name='HOT BEVERAGES / COFFEE').first():
            combos_cat = Category.query.filter_by(name='Combos').first()
            if combos_cat:
                old_items = MenuItem.query.filter(MenuItem.category_id != combos_cat.id).all()
            else:
                old_items = MenuItem.query.all()
                
            for item in old_items:
                try:
                    OrderItem.query.filter_by(menu_item_id=item.id).delete()
                    db.session.delete(item)
                except:
                    pass
            db.session.commit()
            
            if combos_cat:
                old_cats = Category.query.filter(Category.id != combos_cat.id).all()
            else:
                old_cats = Category.query.all()
                
            for cat in old_cats:
                try:
                    db.session.delete(cat)
                except:
                    pass
            db.session.commit()
            
            sort_idx = 1
            for cat_name, items in MENU_DATA.items():
                cat = Category(name=cat_name, sort_order=sort_idx)
                db.session.add(cat)
                db.session.commit()
                
                for item_data in items:
                    name, price, desc, is_fav = item_data
                    mi = MenuItem(
                        name=name,
                        price=price,
                        description=desc,
                        category_id=cat.id,
                        is_favorite=is_fav,
                        food_type='veg'
                    )
                    db.session.add(mi)
                sort_idx += 1
                db.session.commit()
'''

app_code = app_code.replace("db.session.commit()\n\n# Run migration on startup safely", "db.session.commit()\n" + seed_code + "\n# Run migration on startup safely")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Added automatic PDF menu seed to auto_migrate.")
