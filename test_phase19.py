import os
import requests
from app import app, db

os.environ['BACKUP_SECRET_KEY'] = 'test-key'
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SERVER_NAME'] = 'localhost.localdomain'

c = app.test_client()
with app.app_context():
    r1 = c.get('/api/trigger_backup')
    print('NO KEY:', r1.status_code)
    
    r2 = c.get('/api/trigger_backup?key=wrong')
    print('WRONG KEY:', r2.status_code)
    
    r3 = c.get('/api/trigger_backup?key=test-key')
    print('RIGHT KEY:', r3.status_code, r3.json)