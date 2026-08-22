import re
with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    html = f.read()

ids_to_check = [
    'editItemForm', 'editModalTitle', 'edit_name', 'edit_name_hi', 'edit_name_gu',
    'edit_category_id', 'edit_price', 'edit_variant_name', 'edit_description',
    'edit_food_type', 'edit_short_code', 'edit_is_favorite', 'edit_is_combo', 'editItemModal'
]

for i in ids_to_check:
    if f'id="{i}"' not in html and f"id='{i}'" not in html:
        print(f"MISSING ID: {i}")
print("Check done.")
