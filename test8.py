import requests
r = requests.get('https://restaurant-system-z5m7.onrender.com/admin/login')
if 'magic_update_admin' in r.text or 'forceescape' in r.text:
    print('Fixes are deployed')
else:
    print('Checking items page...')
    s = requests.Session()
    match = __import__('re').search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
    csrf = match.group(1) if match else ''
    r = s.post('https://restaurant-system-z5m7.onrender.com/admin/login', data={'mobile': '8141005168', 'password': 'soulsip@2000', 'csrf_token': csrf})
    r = s.get('https://restaurant-system-z5m7.onrender.com/admin/items')
    if 'data-item=' in r.text:
        print('Fixes are deployed (data-item found)')
    else:
        print('Fixes NOT deployed. Old code found.')
