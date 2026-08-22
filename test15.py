import requests
import re
s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf = match.group(1) if match else ''
r = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '7999620244', 'password': 'soulsip@2000', 'csrf_token': csrf})
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
print("Status:", r.status_code)
if "data-item" in r.text:
    print("Edit button fix is deployed and items page loaded successfully!")
else:
    print("Items page failed or fix not found.")
