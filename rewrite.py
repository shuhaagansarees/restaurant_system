with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "'desc_gu': item.desc_gu or ''" in line:
        lines[i] = line.replace("'desc_gu': item.desc_gu or ''", "'desc_gu': item.desc_gu or '', 'price': item.price, 'category_id': item.category_id, 'is_combo': item.is_combo, 'is_favorite': item.is_favorite, 'food_type': item.food_type, 'short_code': item.short_code, 'variant_name': item.variant_name, 'name_gu': item.name_gu or ''")
        break

with open('templates/admin/items.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Done')
