import requests
import re
s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf = match.group(1) if match else ''
r = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
print('Status:', r.status_code)
if r.status_code == 200:
    import json
    import html
    matches = re.finditer(r'data-item="([^"]+)"', r.text)
    for i, match in enumerate(matches):
        data_item = match.group(1)
        decoded = html.unescape(data_item)
        try:
            parsed = json.loads(decoded)
        except Exception as e:
            print(f'PARSE ERROR on item {i}:', e)
            print('Decoded:', decoded)
            break
    else:
        print("All items parsed successfully!")
