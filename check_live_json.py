import requests
import re
from bs4 import BeautifulSoup
import json

r = requests.get('https://restaurant-system-z5m7.onrender.com/admin/login')
csrf_match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
if csrf_match:
    csrf = csrf_match.group(1)
    s = requests.Session()
    s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})
    r2 = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
    soup = BeautifulSoup(r2.text, 'html.parser')
    btns = soup.find_all('button', title='Edit Item')
    for b in btns[:2]:
        dataset_item = b.get('data-item')
        print("Raw dataset item:", dataset_item)
        try:
            parsed = json.loads(dataset_item)
            print("Parsed OK:", parsed)
        except Exception as e:
            print("Parse Error:", e)
