import os

files = [
    'templates/admin/new_dinein.html',
    'templates/admin/new_parcel.html',
    'templates/admin/new_delivery.html',
    'templates/admin/edit_order.html'
]

for file in files:
    if not os.path.exists(file): continue
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the card div
    old_card = '<div class="menu-item-card search-target card-item-{{ item.id }} food-{{ item.food_type }}" data-code="{{ item.short_code | lower }}">'
    new_card = '<div class="menu-item-card search-target card-item-{{ item.id }} food-{{ item.food_type }}" data-code="{{ item.short_code | lower }}" data-id="{{ item.id }}" data-name="{{ item.name|escape }}" data-price="{{ item.price }}" onclick="updateCartEvent(this, 1)" style="cursor: pointer;">'
    content = content.replace(old_card, new_card)
    
    # Update minus button
    old_minus = '<button onclick="updateCart({{ item.id }}, \'{{ item.name|replace(\'\\\'\', \'\\\\\\\'\') }}\', {{ item.price }}, -1)">-</button>'
    new_minus = '<button type="button" onclick="event.stopPropagation(); updateCartEvent(this, -1)" style="pointer-events: auto;">-</button>'
    
    # Also handle possible double quote versions if any
    old_minus_alt = '<button onclick="updateCart({{ item.id }}, \'{{ item.name|replace(\"\'\", \"\\\\\'\") }}\', {{ item.price }}, -1)">-</button>'
    content = content.replace(old_minus, new_minus).replace(old_minus_alt, new_minus)
    
    # Update plus button
    old_plus = '<button onclick="updateCart({{ item.id }}, \'{{ item.name|replace(\'\\\'\', \'\\\\\\\'\') }}\', {{ item.price }}, 1)">+</button>'
    new_plus = '<button type="button" onclick="event.stopPropagation(); updateCartEvent(this, 1)" style="pointer-events: auto;">+</button>'
    
    old_plus_alt = '<button onclick="updateCart({{ item.id }}, \'{{ item.name|replace(\"\'\", \"\\\\\'\") }}\', {{ item.price }}, 1)">+</button>'
    content = content.replace(old_plus, new_plus).replace(old_plus_alt, new_plus)
    
    # Add updateCartEvent function
    if 'function updateCartEvent' not in content:
        js_func = '''
    function updateCartEvent(element, delta) {
        const card = element.closest('.menu-item-card');
        if (!card) return;
        const itemId = card.dataset.id;
        const name = card.dataset.name;
        const price = parseFloat(card.dataset.price);
        updateCart(itemId, name, price, delta);
    }
'''
        content = content.replace('function updateCart(', js_func + '    function updateCart(')
        
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done!')
