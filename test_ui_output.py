from app import app, db
from models import User

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    # Make sure we have a test user
    u = User.query.filter_by(mobile='9999999999').first()
    if not u:
        u = User(mobile='9999999999', name='Admin', role='admin')
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()
        
    client = app.test_client()
    
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Login
    client.post('/admin/login', data={'mobile': '9999999999', 'password': 'admin123'})
    
    print("--- CUSTOMERS PAGE HTML ---")
    r_cust = client.get('/admin/customers')
    html_cust = r_cust.data.decode('utf-8')
    # Print just the table part to keep output short
    start_table = html_cust.find('<table')
    end_table = html_cust.find('</table>') + 8
    print(html_cust[start_table:end_table])
    
    print("\n--- COUPONS PAGE HTML ---")
    r_coup = client.get('/admin/coupons')
    html_coup = r_coup.data.decode('utf-8')
    start_table = html_coup.find('<table')
    end_table = html_coup.find('</table>') + 8
    print(html_coup[start_table:end_table])
