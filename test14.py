import requests
url = 'https://restaurant-system-z5m7.onrender.com/admin/magic_update_admin'
try:
    r = requests.get(url)
    print("Status:", r.status_code)
    print("Response:", r.text)
except Exception as e:
    print("Error:", e)
