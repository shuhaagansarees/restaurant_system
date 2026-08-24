import re

files = [
    'templates/admin/edit_order.html',
    'templates/admin/new_delivery.html',
    'templates/admin/new_dinein.html',
    'templates/admin/new_parcel.html'
]

img_tag = '\n                        {% if item.image_url %}<img src="{{ item.image_url }}" style="width: 100%; height: 120px; object-fit: cover; border-radius: 6px; margin-bottom: 10px;">{% endif %}'

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # The structure is usually <div class="menu-item-card ...">\n                    <div>\n                        <h4 class="item-name">
    # We want to insert the img tag right before <h4
    html = html.replace('<h4 class="item-name">', img_tag + '\n                        <h4 class="item-name">')
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(html)

print("Updated HTML templates with image tags.")
