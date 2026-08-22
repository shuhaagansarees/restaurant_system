# -*- coding: utf-8 -*-
import requests
import re
import json

URL = 'https://restaurant-system-z5m7.onrender.com'
s = requests.Session()

# 1. Login
r = s.get(f'{URL}/admin/login')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf_token = match.group(1) if match else ''

r = s.post(f'{URL}/admin/login', data={
    'mobile': '7999620244',
    'password': 'soulsip@2000',
    'csrf_token': csrf_token
})
print("Logged in!")

# 2. Clear Menu
r = s.get(f'{URL}/admin/items')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf_token = match.group(1) if match else ''

r = s.post(f'{URL}/admin/menu/clear_all', data={'csrf_token': csrf_token})
print("Cleared old menu!", r.status_code)

# Data
menu = {
    "Hot Beverages / Coffee": [
        ("Black Coffee", 39, "Bold espresso, pure & unsweetened", False),
        ("Regular Coffee", 49, "Classic milk coffee, smooth & comforting", False),
        ("Filter Coffee", 59, "South-Indian brew, frothy & aromatic", False),
        ("Hot Chocolate", 99, "Velvety dark cocoa, served piping hot", False)
    ],
    "Cold Beverages": [
        ("Fresh Lime Soda", 49, "Sweet, salted or mixed - your choice", False),
        ("Cold Coffee (Classic)", 69, "Chilled, frothy coffee over ice", False),
        ("Cold Coffee w/ Ice Cream", 79, "Vanilla scoop & chocolate drizzle", False),
        ("Lemon Iced Tea", 79, "Black tea, fresh lemon, served chilled", False)
    ],
    "Mocktails": [
        ("Jaljeera Fizz", 89, "Spiced jaljeera, soda & crunchy boondi", False),
        ("Virgin Mojito", 99, "Muddled mint, lime & soda", False),
        ("Blue Lagoon", 109, "Blue curacao flavour, tangy lemonade", False),
        ("Watermelon Mint Cooler", 109, "Watermelon, lime & crushed ice", False),
        ("Green Apple Fizz", 109, "Crisp green apple, citrus splash", False),
        ("Strawberry Basil Smash", 119, "Strawberry & torn basil, topped with soda", False),
        ("Blueberry Basil Lemonade", 119, "Blueberry-basil twist on classic lemonade", False),
        ("Passion Fruit Mojito", 129, "Passion fruit, mint, lime & soda", True)
    ],
    "Regular Shakes": [
        ("Vanilla Shake", 89, "Classic vanilla bean & chilled milk", False),
        ("Strawberry Shake", 99, "Ripe strawberry, smooth & creamy", False),
        ("Mango Shake (Seasonal)", 99, "Silky mango blended with cool milk", False),
        ("Butterscotch Shake", 109, "Creamy butterscotch-caramel crunch", False),
        ("Kesar Pista Shake", 119, "Saffron & crushed pistachio, chilled milk", False)
    ],
    "Thick / Loaded Shakes": [
        ("Oreo Thick Shake", 139, "Crushed Oreo & creamy ice cream", False),
        ("KitKat Thick Shake", 149, "Loaded with crispy wafer chunks", False),
        ("Belgian Chocolate Thick Shake", 159, "Rich, dark Belgian chocolate fix", False),
        ("Ferrero Rocher Thick Shake", 169, "Golden Ferrero Rocher & roasted hazelnut", False),
        ("Nutella Brownie Thick Shake", 179, "Fudgy brownie meets creamy Nutella", False),
        ("Lotus Biscoff Thick Shake", 179, "Crushed Biscoff & spiced cookie butter", True)
    ],
    "Fries": [
        ("Salted Normal Fries", 79, "Golden fries, classic sea salt", False),
        ("Peri Peri Fries", 99, "Bold, spicy peri peri seasoning", False),
        ("Salted Cheese Fries", 119, "Smothered in warm melted cheese", False),
        ("Peri Peri Cheese Fries", 129, "Peri peri spice meets melted cheese", False),
        ("Nachos French Fries", 149, "Nacho chips, cheese & jalapenos", False),
        ("Special Loaded Long Fries", 279, "Extra-long fries, cheese, sauces & jalapenos", True)
    ],
    "Garlic Bread & Toast": [
        ("Salted Masala Toast", 99, "Garlic butter & Indian spice blend", False),
        ("Normal Cheese Garlic Bread", 109, "Garlic butter baked under melted cheese", False),
        ("Roasted Onion Pepper Toast", 109, "Caramelized onion & roasted bell pepper", False),
        ("Grilled Chilli Toast", 109, "Garlic toast, spicy green chillies & cheese", False),
        ("Cheese Corn Toast", 119, "Sweet corn & melted cheese", False),
        ("Schezwan Toast", 119, "Fiery schezwan sauce & melted cheese", False),
        ("5-Flavour Garlic Toast", 179, "Five seasoned toppings, one showstopper platter", True)
    ],
    "Momos": [
        ("Veg Steam Momos", 99, "Steamed, stuffed with fresh vegetables", False),
        ("Fry Veg Momos", 109, "Golden fried, spiced veg filling", False),
        ("Veg Paneer Steam Momos", 109, "Steamed, soft paneer & veggie mix", False),
        ("Cheese Steam Momos", 119, "Steamed, gooey melted cheese filling", False),
        ("Fry Paneer / Cheese Momos", 119, "Deep-fried, paneer or cheese filling", False),
        ("Tandoori Peri Peri Momos", 179, "Smoky tandoori marinade, peri peri kick", False)
    ],
    "Frankie / Wraps": [
        ("Aloo Tikki Frankie", 59, "Spiced potato patty, tangy chutneys", False),
        ("Veg Cheese Frankie", 69, "Melted cheese & fresh veggies in a soft warm roll", False),
        ("Tandoori Veg Frankie", 89, "Smoky tandoori veggies in a soft roll", False),
        ("Cheese Corn Frankie", 89, "Sweet corn & gooey melted cheese", False),
        ("Paneer Frankie", 99, "Spiced paneer, crunchy veggies & sauces", False),
        ("Mexican Veg Frankie", 119, "Mixed veg, salsa & Mexican spice", False),
        ("Paneer Tikka Frankie", 119, "Tandoori paneer tikka, onions & chutney", False),
        ("Schezwan Paneer Frankie", 119, "Paneer tossed in bold schezwan sauce", False),
        ("Double Cheese Paneer Frankie", 129, "Spiced paneer, double melted cheese blast", True)
    ],
    "Sandwich": [
        ("Bread Butter Sandwich", 49, "Soft bread, creamy butter", False),
        ("Cheese Jam Sandwich", 69, "Sweet jam meets rich cheese", False),
        ("Cheese Bread Butter", 69, "Buttered bread with a cheese slice", False),
        ("Veg Sandwich", 79, "Fresh veggies, creamy cheese layers", False),
        ("Mini Cheese Grill", 89, "Toasted pockets, melted cheese & herbs", False),
        ("Veg Cheese Sandwich", 99, "Sliced vegetables, smooth melted cheese", False),
        ("Cheese Aloo Sandwich", 99, "Spiced potato filling & melted cheese", False),
        ("Open Cheese Toast", 99, "Golden toast loaded with gooey cheese", False),
        ("Veg Cheese Grill Sandwich", 109, "Grilled, crunchy veg & melted cheese", False),
        ("Garlic Cheese Open Toast", 109, "Garlic butter, bubbly melted cheese", False),
        ("Corn Cheese Open Toast", 109, "Sweet corn & melted cheese, open-faced", False),
        ("Cheesy Spicy Open Toast", 119, "Melted cheese, spicy chillies & herbs", False),
        ("Bombay Grill Sandwich", 129, "Street-style, spiced potato & green chutney", False),
        ("Tandoori Paneer Sandwich", 139, "Smoky tandoori paneer, grilled", False),
        ("Special Protein Sandwich", 149, "Protein-rich grilled filling, fitness-focused & fresh", False),
        ("Matka Sandwich (Veg / Paneer)", 149, "Chef's special served in an earthen pot", True)
    ],
    "Burger": [
        ("Standard Veg Burger", 79, "Potato-veggie patty, lettuce & mayo", False),
        ("Crispy Crunch Burger", 95, "Extra-crunchy patty, tangy signature sauce", False),
        ("Red Hot Spicy Burger", 99, "Fiery patty, hot chilli mayo", False),
        ("Farm House Burger", 109, "Garden-fresh veggies, tomato & cheese", False),
        ("Tandoori Paneer Burger", 139, "Smoky paneer steak, mint mayo", False),
        ("Original Double Tikki Burger", 149, "Two crispy patties, melted cheese & sauces", True)
    ],
    "Pizza": [
        ("Peri Peri Paneer Pizza", 109, "Spiced peri peri paneer, onions & melted cheese", False),
        ("Margherita Pizza", 129, "Tomato sauce, mozzarella & fresh basil", False),
        ("Cheese Corn Pizza", 139, "Sweet corn, thick layer of cheese", False),
        ("Spicy Tangy Pizza", 169, "Zesty sauces, fiery jalapenos", False),
        ("Farm House Pizza", 209, "Onion, capsicum, tomato & mushroom", False),
        ("Tandoori Paneer Pizza", 279, "Tandoori paneer, capsicum, onion & cheese", True)
    ],
    "Mayo Pav": [
        ("Solid Masti Pav", 59, "Buttery pav, seasoned veggie patty", False),
        ("Cream Onion Pav", 69, "Caramelized onion, velvety sour cream", False),
        ("Veggie House Pav", 79, "Garden veggies, house-special spread", False),
        ("Hot Spicy Pav", 79, "Fiery red chilli spice & jalapenos", False),
        ("Tandoori Paneer Pav", 99, "Smoky tandoori paneer, crisp onions", False)
    ],
    "Pasta": [
        ("Red Sauce Pasta", 139, "Tangy tomato-basil, garlic & herbs", False),
        ("White Sauce Pasta", 159, "Silky garlic-cream sauce, melted cheese", False),
        ("Pink Sauce Pasta", 169, "Tomato marinara meets creamy white sauce", False)
    ],
    "Maggi": [
        ("Masala Maggi", 69, "Classic noodles, savoury Indian spice", False),
        ("Veggie Maggi", 89, "Sauteed garden vegetables", False),
        ("Cheesy Sauce Maggi", 99, "Rich, velvety cheese sauce", False),
        ("Schezwan Cheese Maggi", 109, "Fiery schezwan spice, melted cheese", False),
        ("Vegetable Cheese Maggi", 109, "Sauteed mixed vegetables in creamy cheese sauce", False),
        ("Extra Cheese Maggie", 129, "Extra velvety cheese sauce, ultra creamy", False)
    ],
    "Desserts": [
        ("Ice Cream (2 Scoops)", 79, "Classic flavour, cold & creamy", False),
        ("Chocolate Lava Cake", 79, "Molten cocoa centre, oozes with every bite", False),
        ("Brownie (Plain)", 99, "Rich, dense, fudgy chocolate brownie", False),
        ("Brownie with Ice Cream", 129, "Warm brownie, chilled vanilla scoop", False),
        ("Belgian Waffle (Choco / Nutella)", 149, "Golden-crisp, deep pockets & airy centre", False),
        ("Waffle with Ice Cream", 179, "Crispy waffle, chocolate/Nutella & ice cream", True)
    ]
}

# 3. Add categories and items
r = s.get(f'{URL}/admin/categories')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf_token = match.group(1) if match else ''

cat_map = {}
for cat_name in menu.keys():
    print("Adding category", cat_name)
    r = s.post(f'{URL}/admin/categories', data={
        'name': cat_name,
        'csrf_token': csrf_token
    })

# Fetch categories to get IDs
r = s.get(f'{URL}/api/categories')
cats = r.json()
for c in cats:
    cat_map[c['name']] = c['id']

r = s.get(f'{URL}/admin/items')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf_token = match.group(1) if match else ''

for cat_name, items in menu.items():
    cat_id = cat_map.get(cat_name)
    if not cat_id:
        print("Category not found", cat_name)
        continue
        
    for item_name, price, desc, is_fav in items:
        print("Adding item", item_name)
        data = {
            'name': item_name,
            'category_id': cat_id,
            'price': price,
            'description': desc,
            'food_type': 'veg',
            'csrf_token': csrf_token
        }
        if is_fav:
            data['is_favorite'] = 'on'
        s.post(f'{URL}/admin/items', data=data)

print("DONE!")
