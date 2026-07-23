import sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app, db
from models import WaiterCall

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    c = app.test_client()
    res = c.post('/api/call_waiter', json={
        'table_name': 'T-DEBUG',
        'order_id': 1
    })
    print("Status Code:", res.status_code)
    print("Response:", res.data.decode('utf-8'))
