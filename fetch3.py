import requests, re
s = requests.Session()
r1 = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r1.text)
csrf_token = match.group(1) if match else ''
r2 = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '7999620244', 'password': 'soulsip@2000', 'csrf_token': csrf_token})
html = s.get('https://restaurant-system-z5m7.onrender.com/admin/edit_order/19').text
with open('render_html.txt', 'w', encoding='utf-8') as f:
    f.write(html)
print('Length:', len(html))
