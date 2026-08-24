import requests

url = 'https://restaurant-system-z5m7.onrender.com/admin/inventory/fix_dummy'
print(f"Hitting {url} ...")
try:
    response = requests.get(url, timeout=30)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
