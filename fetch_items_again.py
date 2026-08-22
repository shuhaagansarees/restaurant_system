import requests
import re
from bs4 import BeautifulSoup

s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
csrf = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text).group(1)
r = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')

soup = BeautifulSoup(r.text, 'html.parser')
buttons = soup.find_all('button', title='Edit Item')
for b in buttons[:1]:
    print("BUTTON ONCLICK:", b.get('onclick'))
    print("BUTTON DATA-ITEM:", b.get('data-item'))
