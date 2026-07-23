import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

print("Hitting /api/call_waiter...")
res = requests.post('http://localhost:10000/api/call_waiter', json={
    'table_name': 'T-DEBUG',
    'order_id': 1
})
print("Status Code:", res.status_code)
print("Response:", res.text)
