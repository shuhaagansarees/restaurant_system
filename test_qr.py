import sys
from app import app, db
from models import User, Table

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    # Make sure we have a table and admin user
    if not Table.query.first():
        db.session.add(Table(name='T-1', branch_id=1, capacity=4))
        db.session.commit()
    
    table = Table.query.first()
    admin = User.query.filter_by(role='admin').first()

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
            
        res = c.get(f'/admin/qr/{table.id}')
        print(f"Status Code: {res.status_code}")
        print(f"Content Type: {res.content_type}")
        if res.status_code == 200:
            print(f"Response length: {len(res.data)}")
        else:
            print(f"Error: {res.data}")
