# -*- coding: utf-8 -*-
import requests
import re

URL = 'https://restaurant-system-z5m7.onrender.com'
s = requests.Session()

# 1. Login
r = s.get(f'{URL}/admin/login')
match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
csrf_token = match.group(1) if match else ''

r = s.post(f'{URL}/admin/login', data={
    'mobile': '7999620244',
    'password': 'soulsip@2000',
    'csrf_token': csrf_token
})
print("Logged in!")

# 2. Add tables T-2 through T-6
for i in range(2, 7):
    table_name = f'T-{i}'
    print(f"Adding table {table_name}...")
    
    r = s.get(f'{URL}/admin/tables')
    match = re.search(r'name="csrf_token"[\s\S]*?value="([^"]+)"', r.text)
    csrf_token = match.group(1) if match else ''
    
    res = s.post(f'{URL}/admin/tables', data={
        'name': table_name,
        'capacity': '4',
        'section': 'Main',
        'csrf_token': csrf_token
    })
    
    if res.status_code == 200:
        print(f"Success for {table_name}")
    else:
        print(f"Failed for {table_name}: HTTP {res.status_code}")

print("DONE!")
