import csv
import os
from collections import defaultdict

csv_path = 'menu_data.csv'
csv_lines = 0
csv_categories = set()
csv_items = []
csv_cat_counts = defaultdict(int)

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_lines += 1
        cat = row['csvcategory'].strip()
        name = row['item_name'].strip()
        csv_categories.add(cat)
        csv_items.append((cat, name))
        csv_cat_counts[cat] += 1

print(f"CSV Total Data Lines (excluding header): {csv_lines}")
print(f"CSV Total Categories: {len(csv_categories)}")
print(f"CSV Categories List: {list(csv_categories)}")

from app import app, db
from models import Category, MenuItem

with app.app_context():
    db_cat_count = Category.query.count()
    db_item_count = MenuItem.query.count()
    
    print(f"\nDB Total Categories: {db_cat_count}")
    print(f"DB Total Items: {db_item_count}")
    
    print("\n--- DB Breakdown by Category ---")
    cats = Category.query.order_by(Category.sort_order).all()
    db_items_list = []
    for c in cats:
        count = MenuItem.query.filter_by(category_id=c.id).count()
        print(f"{c.name}: {count}")
        items = MenuItem.query.filter_by(category_id=c.id).all()
        for i in items:
            db_items_list.append((c.name, i.name))

    print("\n--- Missing Items Analysis ---")
    missing = set(csv_items) - set(db_items_list)
    if missing:
        print(f"Found {len(missing)} missing items:")
        for cat, name in missing:
            print(f" - {name} (in category {cat})")
    else:
        print("No missing items found. CSV exactly matches DB.")
