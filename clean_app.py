import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

# Remove the leftover code at the bottom of sync_menu_inventory
bad_code = '''        
    menu_items = MenuItem.query.all()
    count_added = 0
    for mi in menu_items:
        clean_name = mi.name.strip()
        mat = RawMaterial.query.filter(db.func.lower(RawMaterial.name) == db.func.lower(clean_name)).first()
        if not mat:
            mat = RawMaterial(
                name=clean_name,
                unit='pcs',
                current_stock=25.0,
                low_stock_threshold=5.0
            )
            db.session.add(mat)
            count_added += 1
            
    db.session.commit()
    flash(f"Successfully synced menu items! {count_added} new items linked to inventory tracking.", "success")
    return redirect(url_for('admin_inventory'))'''

app_code = app_code.replace(bad_code, '')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
