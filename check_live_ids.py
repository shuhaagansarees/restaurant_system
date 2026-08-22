import requests
import re
from bs4 import BeautifulSoup

s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
csrf = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text).group(1)
s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')

ids_to_check = [
    'editItemForm', 'editModalTitle', 'edit_name', 'edit_name_hi', 'edit_name_gu',
    'edit_category_id', 'edit_price', 'edit_variant_name', 'edit_description',
    'edit_food_type', 'edit_short_code', 'edit_is_favorite', 'edit_is_combo', 'editItemModal'
]

for i in ids_to_check:
    if f'id="{i}"' not in r.text and f"id='{i}'" not in r.text:
        print(f"MISSING ID: {i}")

print("Check complete.")
