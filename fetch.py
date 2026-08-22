import requests, re
s = requests.Session()
r1 = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
match = re.search(r'name="csrf_token" value="([^"]+)"', r1.text)
if not match:
    match = re.search(r'id="csrf_token".*?value="([^"]+)"', r1.text)
csrf_token = match.group(1) if match else 'IjBkMjRlNDM4YmExNjUxMmE1NDY1ZDdkNWQwMTZmMmUwOTliNjQ5ZjEi.Z3ROXg.oYx4fM_vP9j4fU1h8z7d5y7Z4'
print('Token:', csrf_token)
r2 = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'username': '7999620244', 'password': 'soulsip@2000', 'csrf_token': csrf_token})
print('Login Status:', r2.status_code)
html = s.get('https://restaurant-system-z5m7.onrender.com/admin/edit_order/19').text
with open('render_html.txt', 'w', encoding='utf-8') as f:
    f.write(html)
print('Length:', len(html))
