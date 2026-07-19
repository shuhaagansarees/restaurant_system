import csv
import os
from app import app, db
from models import Branch, Category, MenuItem, Table, User

def seed_data():
    with app.app_context():
        # Drop all and recreate to ensure clean slate
        db.drop_all()
        db.create_all()
        
        print("Seeding data...")

        # Create Branch
        branch = Branch(
            name="Shiv Shakti Restaurant & Banquet",
            address="Shop no. 8 & 9, Green Residency, Commercial Shopping Center, Opp. Madhav Crest, Surat",
            phone="9876543210"
        )
        db.session.add(branch)
        db.session.commit() # Commit to get branch.id

        # Add admin user
        admin = User(name='Admin User', mobile='9999999999', role='admin', branch_id=branch.id)
        admin.set_password('admin123')
        db.session.add(admin)
        
        manager = User(name='Manager User', mobile='8888888888', role='manager', branch_id=branch.id)
        manager.set_password('manager123')
        db.session.add(manager)
        
        waiter = User(name='Waiter User', mobile='7777777777', role='waiter', branch_id=branch.id)
        waiter.set_password('waiter123')
        db.session.add(waiter)
        
        chef = User(name='Chef User', mobile='6666666666', role='chef', branch_id=branch.id)
        chef.set_password('chef123')
        db.session.add(chef)
        
        cashier = User(name='Cashier User', mobile='5555555555', role='cashier', branch_id=branch.id)
        cashier.set_password('cashier123')
        db.session.add(cashier)

        # Create Tables
        tables = []
        for i in range(1, 13):
            tables.append(Table(branch_id=branch.id, name=f"T-{i}", seats=4, status="vacant"))
        db.session.add_all(tables)
        db.session.commit()

        # Read CSV and create categories & menu items
        csv_path = os.path.join(os.path.dirname(__file__), 'menu_data.csv')
        
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                categories_map = {}
                sort_counter = 1
                
                for row in reader:
                    cat_name = row['csvcategory'].strip()
                    
                    if cat_name not in categories_map:
                        new_cat = Category(name=cat_name, sort_order=sort_counter)
                        db.session.add(new_cat)
                        db.session.commit()
                        categories_map[cat_name] = new_cat
                        sort_counter += 1
                        
                    cat_obj = categories_map[cat_name]
                    
                    item_name = row['item_name'].strip()
                    item_name_gu = row['item_name_gu'].strip()
                    price = float(row['price'].strip()) if row['price'].strip() else 0.0
                    
                    # Create item
                    item = MenuItem(
                        category_id=cat_obj.id,
                        name=item_name,
                        name_gu=item_name_gu,
                        price=price
                    )
                    db.session.add(item)
                    
            db.session.commit()
            print("Menu data loaded from CSV!")
        else:
            print("WARNING: menu_data.csv not found, skipping menu items.")

        print("Data seeded successfully!")
        print("-" * 30)
        print("Test Login Credentials:")
        print("Mobile: 9999999999")
        print("Password: admin123")
        print("-" * 30)

if __name__ == "__main__":
    seed_data()
