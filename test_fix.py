from app import app, db
from models import *

with app.app_context():
    dummy_names = ['Rice', 'Paneer Butter Masala', 'Cold Coffee w/ Ice Cream', 'Cold Coffee']
    for d in dummy_names:
        mat = RawMaterial.query.filter_by(name=d).first()
        if mat:
            InventoryLog.query.filter_by(raw_material_id=mat.id).delete()
            db.session.delete(mat)
    
    db.session.commit()
    
    menu_items = MenuItem.query.all()
    for mi in menu_items:
        clean_name = mi.name.strip()
        mat = RawMaterial.query.filter(db.func.lower(RawMaterial.name) == db.func.lower(clean_name)).first()
        if not mat:
            mat = RawMaterial(name=clean_name, current_stock=0, unit='pcs', low_stock_threshold=5, is_auto_tracked=True)
            db.session.add(mat)
    db.session.commit()
    print("Success")
