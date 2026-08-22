import requests
import re
s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf = match.group(1) if match else ''
r_old = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '7999620244', 'password': 'soulsip@2000', 'csrf_token': csrf})
r_items = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
print("Status:", r_items.status_code)
if "Please log in" in r_items.text:
    print("Not logged in!")
elif "500 Internal Server Error" in r_items.text:
    print("500 Error on items page!")
else:
    print("Length of text:", len(r_items.text))
    match = re.search(r'<button[^>]*title="Edit Item"[^>]*>', r_items.text)
    if match:
        print("Button HTML:", match.group(0))
    else:
        print("No Edit button found")
