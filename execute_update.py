import requests
import re
try:
    s = requests.Session()
    # Let's hit the magic route to update the credentials
    r = s.get('https://restaurant-system-z5m7.onrender.com/admin/magic_update_admin')
    print('Magic route status:', r.status_code)
    print('Magic route output:', r.text)

    # Let's verify login with new credentials
    r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')
    match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
    csrf = match.group(1) if match else ''
    
    r_login = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})
    
    r_items = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
    if "Edit Menu Item" in r_items.text:
        print("Login with new credentials SUCCESSFUL! Items page loaded.")
    else:
        print("Login or Items page failed.")
except Exception as e:
    print('Error:', e)
