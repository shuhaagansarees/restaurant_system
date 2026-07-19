import unittest
from app import app, db
from models import User, Order, Branch, Table

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for easier testing
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            
            # Create a test branch
            branch = Branch.query.first()
            if not branch:
                branch = Branch(name="Test Branch")
                db.session.add(branch)
                db.session.commit()
                
            # Ensure the test admin exists
            admin = User.query.filter_by(mobile='7999620244').first()
            if not admin:
                admin = User(name='Admin', mobile='7999620244', role='admin', branch_id=branch.id)
                admin.set_password('shivshakti@2000')
                db.session.add(admin)
                db.session.commit()

    def test_1_rate_limiting_login(self):
        # We test that hitting /admin/login 6 times triggers a 429
        # Flask-Limiter tracks by IP. Test client uses 127.0.0.1
        responses = []
        for _ in range(6):
            res = self.client.post('/admin/login', data={'mobile': '7999620244', 'password': 'wrong'})
            responses.append(res.status_code)
            
        self.assertIn(429, responses, "Rate limit (429) was not triggered after 5 attempts.")

    def test_2_static_folder_isolation(self):
        # By default, Flask only serves static files from /static/
        # Root files like .env or database/restaurant.db should return 404.
        res_env = self.client.get('/.env')
        res_db = self.client.get('/database/restaurant.db')
        
        self.assertEqual(res_env.status_code, 404, ".env should not be accessible")
        self.assertEqual(res_db.status_code, 404, "Database file should not be accessible")

    def test_3_security_headers(self):
        res = self.client.get('/admin/login')
        headers = res.headers
        self.assertIn('X-Content-Type-Options', headers)
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn('X-Frame-Options', headers)
        self.assertEqual(headers['X-Frame-Options'], 'DENY')

    def test_4_live_orders_state_persistence(self):
        with app.app_context():
            # 1. Place a test order
            branch = Branch.query.first()
            order = Order(branch_id=branch.id, type='dine-in', status='new', customer_name='TestPersistence')
            db.session.add(order)
            db.session.commit()
            order_id = order.id
            
        # 2. Login to simulate real flow (using different IP to avoid rate limit from Test 1)
        login_res = self.client.post('/admin/login', data={
            'mobile': '7999620244',
            'password': 'shivshakti@2000'
        }, follow_redirects=True, environ_base={'REMOTE_ADDR': '127.0.0.2'})
        self.assertEqual(login_res.status_code, 200)
        
        # 3. Fetch Live Orders page
        live_res = self.client.get('/admin/live_orders')
        self.assertEqual(live_res.status_code, 200)
        
        # 4. Check if the newly placed order is rendered in the HTML
        html_content = live_res.data.decode('utf-8')
        self.assertIn('TestPersistence', html_content, "Pre-existing order did not render on page load!")
        self.assertIn(f"#{order_id}", html_content, "Order ID did not render on page load!")
        
        # Cleanup
        with app.app_context():
            Order.query.filter_by(id=order_id).delete()
            db.session.commit()

if __name__ == '__main__':
    unittest.main(verbosity=2)
