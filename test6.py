import requests
import re
s = requests.Session()
r = s.get('http://127.0.0.1:5000/admin/login')
print("Login status:", r.status_code)
