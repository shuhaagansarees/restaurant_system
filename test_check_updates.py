import requests

s = requests.Session()
r = s.get('https://restaurant-system-z5m7.onrender.com/api/check_updates?since=undefined')
print(r.status_code)
print(r.text)
