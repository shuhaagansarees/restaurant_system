with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

new_sync = '''
@app.route('/admin/inventory/sync_menu', methods=['POST', 'GET'])
@login_required
def sync_menu_inventory():
    if current_user.role not in ['admin', 'manager']:
        flash('Unauthorized', 'danger')
        return redirect(url_for('admin_inventory'))
        
    menu_items = MenuItem.query.all()
    valid_names = [mi.name.strip().lower() for mi in menu_items]
    
    # 1. Delete inventory items that are no longer in the menu
    all_materials = RawMaterial.query.all()
    for mat in all_materials:
        if mat.name.strip().lower() not in valid_names:
            InventoryLog.query.filter_by(raw_material_id=mat.id).delete()
            db.session.delete(mat)
    db.session.commit()
    
    # 2. Add missing menu items to inventory
    count_added = 0
    for mi in menu_items:
        clean_name = mi.name.strip()
        mat = RawMaterial.query.filter(db.func.lower(RawMaterial.name) == db.func.lower(clean_name)).first()
        if not mat:
            mat = RawMaterial(name=clean_name, current_stock=0, unit='pcs', low_stock_threshold=5)
            db.session.add(mat)
            count_added += 1
            
    db.session.commit()
    flash(f'Menu perfectly synced! Removed old items and added {count_added} new items to inventory.', 'success')
    return redirect(url_for('admin_inventory'))
'''

import re
app_code = re.sub(r"@app\.route\('/admin/inventory/sync_menu'.*?return redirect\(url_for\('admin_inventory'\)\)", new_sync.strip(), app_code, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
