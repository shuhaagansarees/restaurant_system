import requests
import re

s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf = match.group(1) if match else ''

r = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})

r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf = match.group(1) if match else ''

# Find the first item ID
match = re.search(r'action="/admin/items/delete/(\d+)"', r.text)
if match:
    item_id = match.group(1)
    print("Found item:", item_id)
    
    # Let's hit the edit endpoint
    data = {
        'name': 'Cold Coffee (Classic)',
        'category_id': '1', # we need a valid category ID
        'price': '75.0',
        'csrf_token': csrf
    }
    # Wait, category_id is required. Let's find it.
    cat_match = re.search(r'<option value="(\d+)">Cold Beverages</option>', r.text)
    if not cat_match:
        cat_match = re.search(r'<option value="(\d+)">', r.text)
    if cat_match:
        data['category_id'] = cat_match.group(1)
        
    r = s.post(f'https://restaurant-system-z5m7.onrender.com/admin/items/edit/{item_id}', data=data)
    print("Edit status:", r.status_code)
    
    # Check if updated
    r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
    if '75.0' in r.text:
        print("Price updated successfully!")
        
    # Revert back
    data['price'] = '69.0'
    r = s.post(f'https://restaurant-system-z5m7.onrender.com/admin/items/edit/{item_id}', data=data)
else:
    print("No items found")
