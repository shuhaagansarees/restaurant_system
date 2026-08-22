import requests
import re
from bs4 import BeautifulSoup

s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
csrf = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text).group(1)
s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')

if 'function openEditItemModal' in r.text:
    print("Function exists in HTML!")
else:
    print("FUNCTION MISSING!")
    
if 'id="editItemModal"' in r.text:
    print("Modal exists in HTML!")
else:
    print("MODAL MISSING!")
