import re

with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_data = r'''data-item="\{\{\s*\{\s*'id': item.id,\s*'name': item.name,\s*'name_hi': item.name_hi or '',\s*'description': item.description or '',\s*'desc_hi': item.desc_hi or '',\s*'desc_gu': item.desc_gu or ''\s*\}\|tojson\|forceescape \}\}"'''

new_data = '''data-item="{{ {
                                  'id': item.id,
                                  'name': item.name,
                                  'name_hi': item.name_hi or '',
                                  'name_gu': item.name_gu or '',
                                  'category_id': item.category_id,
                                  'price': item.price,
                                  'description': item.description or '',
                                  'desc_hi': item.desc_hi or '',
                                  'desc_gu': item.desc_gu or '',
                                  'variant_name': item.variant_name or '',
                                  'is_combo': item.is_combo,
                                  'is_favorite': item.is_favorite,
                                  'food_type': item.food_type or 'veg',
                                  'short_code': item.short_code or ''
                              }|tojson|forceescape }}"'''

html = re.sub(old_data, new_data, html)

with open('templates/admin/items.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated data-item in items.html")
