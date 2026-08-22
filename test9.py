import requests
import re

s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/admin/login')

if 'magic_update_admin' in r.text or 'forceescape' in r.text:
    print('Fixes are deployed')
else:
    print('Login page checked. Checking items page...')
    match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
    csrf = match.group(1) if match else ''
    
    # Try old login
    r_old = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '7999620244', 'password': 'soulsip@2000', 'csrf_token': csrf})
    
    r_items = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
    if 'data-item=' in r_items.text:
        print('Fixes are deployed on items page (data-item found)')
    else:
        print('Fixes NOT deployed. Old code found on items page.')
        
    r_magic = s.get('https://restaurant-system-z5m7.onrender.com/admin/magic_update_admin')
    print('Magic route status:', r_magic.status_code)
    print('Magic route response:', r_magic.text)
