with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

fix_route = '''
@app.route('/admin/inventory/fix_dummy')
def fix_dummy_inventory():
    dummy_names = ['Rice', 'Paneer Butter Masala', 'Cold Coffee w/ Ice Cream', 'Cold Coffee']
    # Find and delete dummy items and their logs
    for d in dummy_names:
        mat = RawMaterial.query.filter_by(name=d).first()
        if mat:
            InventoryLog.query.filter_by(raw_material_id=mat.id).delete()
            db.session.delete(mat)
    
    db.session.commit()
    
    # Sync actual menu
    menu_items = MenuItem.query.all()
    for mi in menu_items:
        clean_name = mi.name.strip()
        mat = RawMaterial.query.filter(db.func.lower(RawMaterial.name) == db.func.lower(clean_name)).first()
        if not mat:
            mat = RawMaterial(name=clean_name, current_stock=0, unit='pcs', low_stock_threshold=5, is_auto_tracked=True)
            db.session.add(mat)
    db.session.commit()
    return "Fix applied! Please go back to the inventory page."
'''

# Insert the new route right before sync_menu_inventory
app_code = app_code.replace("@app.route('/admin/inventory/sync_menu', methods=['POST', 'GET'])", fix_route + "\n@app.route('/admin/inventory/sync_menu', methods=['POST', 'GET'])")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
