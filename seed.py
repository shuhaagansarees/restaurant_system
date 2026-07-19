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
            name="Downtown Diner",
            address="123 Main St, City Center",
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

        # Create Categories
        cat_starters = Category(name="Starters", sort_order=1)
        cat_mains = Category(name="Main Course", sort_order=2)
        cat_drinks = Category(name="Beverages", sort_order=3)
        db.session.add_all([cat_starters, cat_mains, cat_drinks])
        db.session.commit() # Commit to get category ids

        # Create Menu Items
        item1 = MenuItem(
            category_id=cat_starters.id,
            name="Paneer Tikka",
            description="Grilled cottage cheese cubes marinated in spices.",
            price=250.0
        )
        item2 = MenuItem(
            category_id=cat_mains.id,
            name="Butter Chicken",
            description="Classic rich tomato and butter gravy.",
            price=350.0
        )
        item3 = MenuItem(
            category_id=cat_mains.id,
            name="Garlic Naan",
            description="Freshly baked flatbread with garlic.",
            price=50.0
        )
        item4 = MenuItem(
            category_id=cat_drinks.id,
            name="Cold Coffee",
            description="Refreshing blended iced coffee.",
            price=120.0,
            variant_name="Regular"
        )
        db.session.add_all([item1, item2, item3, item4])

        # Create Tables
        table1 = Table(branch_id=branch.id, name="T-1", seats=4, status="vacant")
        table2 = Table(branch_id=branch.id, name="T-2", seats=2, status="vacant")
        table3 = Table(branch_id=branch.id, name="T-3", seats=6, status="vacant")
        db.session.add_all([table1, table2, table3])

        db.session.commit()
        print("Data seeded successfully!")
        print("-" * 30)
        print("Test Login Credentials:")
        print("Mobile: 9999999999")
        print("Password: admin123")
        print("-" * 30)

if __name__ == "__main__":
    seed_data()
