import requests
r = requests.get('https://restaurant-system-z5m7.onrender.com/admin/magic_update_admin')
print('Status:', r.status_code)
print('Response:', r.text)
