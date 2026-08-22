import requests
import re
s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf = match.group(1) if match else ''
r = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '7999620244', 'password': 'soulsip@2000', 'csrf_token': csrf})
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
print("Items page snippet:")
print(r.text[:500])
