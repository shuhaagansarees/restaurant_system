import requests
import re
r = requests.get('https://restaurant-system-z5m7.onrender.com/admin/login')
csrf = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text).group(1)
s = requests.Session()
s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})
html = s.get('https://restaurant-system-z5m7.onrender.com/admin/items').text
with open('live_items.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved live items")
