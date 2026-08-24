from menu_data import MENU_DATA

route_code = """
@app.route('/admin/magic_replace_menu')
def magic_replace_menu():
    try:
        from models import db, Category, MenuItem, OrderItem
        from menu_data import MENU_DATA
        
        # 1. Get Combos category
        combos_cat = Category.query.filter_by(name='Combos').first()
        
        # 2. Get all menu items NOT in Combos
        if combos_cat:
            old_items = MenuItem.query.filter(MenuItem.category_id != combos_cat.id).all()
        else:
            old_items = MenuItem.query.all()
            
        for item in old_items:
            # Delete related OrderItems to avoid FK constraint
            OrderItem.query.filter_by(menu_item_id=item.id).delete()
            db.session.delete(item)
            
        db.session.commit()
        
        # 3. Delete old categories except Combos
        if combos_cat:
            old_cats = Category.query.filter(Category.id != combos_cat.id).all()
        else:
            old_cats = Category.query.all()
            
        for cat in old_cats:
            db.session.delete(cat)
            
        db.session.commit()
        
        # 4. Insert new categories and items
        sort_idx = 1
        for cat_name, items in MENU_DATA.items():
            cat = Category(name=cat_name, sort_order=sort_idx)
            db.session.add(cat)
            db.session.commit() # Commit to get ID
            
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
            
        return "SUCCESS! Menu replaced."
    except Exception as e:
        db.session.rollback()
        return f"ERROR: {str(e)}"
"""

with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

app_code = app_code.replace("@app.route('/admin/magic_add_menu')", route_code + "\n\n@app.route('/admin/magic_add_menu')")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Added magic_replace_menu route to app.py")
