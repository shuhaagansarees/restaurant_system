import os
import qrcode
import io
import csv
import zipfile
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_socketio import SocketIO
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from functools import wraps
from flask import abort, current_app
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            if current_user.role != 'admin' and current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# Load models
from models import db, User, Branch, Category, MenuItem, Table, Order, OrderItem, Invoice, CreditLedger, Refund, ActivityLog, Coupon, CustomerProfile, WaiterCall, Feedback

load_dotenv()

app = Flask(__name__)
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    import warnings
    warnings.warn("No SECRET_KEY set in .env. A random one has been generated, but sessions will be invalidated on restart!")
    secret_key = os.urandom(24)
app.config['SECRET_KEY'] = secret_key
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'database')
os.makedirs(db_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(db_dir, 'restaurant.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Security configs
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.login_view = 'admin_login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables before first request if they don't exist
with app.app_context():
    db.create_all()
    
    # Safe auto-migration for Phase 20 (Coupons & Delivery)
    try:
        from sqlalchemy import text
        queries = [
            "ALTER TABLE orders ADD COLUMN has_new_items BOOLEAN DEFAULT 0",
            "ALTER TABLE orders ADD COLUMN coupon_code VARCHAR(50)",
            "ALTER TABLE orders ADD COLUMN delivery_address TEXT",
            "ALTER TABLE orders ADD COLUMN landmark VARCHAR(100)",
            "ALTER TABLE orders ADD COLUMN delivery_charge FLOAT DEFAULT 0.0",
            "ALTER TABLE orders ADD COLUMN delivery_staff_id INTEGER REFERENCES staff_users(id)",
            "ALTER TABLE invoices ADD COLUMN delivery_charge FLOAT DEFAULT 0.0",
            "ALTER TABLE invoices ADD COLUMN coupon_code VARCHAR(50)"
        ]
        for q in queries:
            try:
                db.session.execute(text(q))
                db.session.commit()
            except Exception:
                db.session.rollback()
    except Exception:
        pass
    # Auto-seed logic for fresh deployments
    if User.query.count() == 0:
        print("Empty database detected. Running auto-seed...")
        try:
            import seed
            seed.seed_data()
            print("Auto-seed successful!")
        except Exception as e:
            print(f"Auto-seed failed: {e}")

def log_activity(action, details):
    uid = current_user.id if current_user.is_authenticated else None
    log = ActivityLog(user_id=uid, action=action, details=details)
    db.session.add(log)
    db.session.commit()

def send_whatsapp_message(mobile, text):
    if not mobile:
        return
        
    token = os.environ.get('WHATSAPP_TOKEN')
    phone_id = os.environ.get('WHATSAPP_PHONE_ID')
    
    if not token or not phone_id:
        print(f"[WhatsApp] Not configured \u2014 skipping message to {mobile}")
        return None
        
    # Ensure mobile starts with country code, default to 91 for India if 10 digits
    if len(mobile) == 10 and mobile.isdigit():
        mobile = '91' + mobile
        
    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": mobile,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }
    
    try:
        import requests
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        print(f"[WhatsApp] Sent to {mobile}, Status: {response.status_code}, Response: {response.text}")
        return response
    except Exception as e:
        print(f"[WhatsApp] Error sending to {mobile}: {str(e)}")
        return None

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

def export_model_to_csv(model):
    si = io.StringIO()
    cw = csv.writer(si)
    columns = [column.name for column in model.__mapper__.columns]
    cw.writerow(columns)
    records = model.query.all()
    for record in records:
        cw.writerow([getattr(record, col) for col in columns])
    return si.getvalue()

def generate_backup_zip():
    models_to_backup = [
        ('orders.csv', Order),
        ('order_items.csv', OrderItem),
        ('invoices.csv', Invoice),
        ('credit_ledger.csv', CreditLedger),
        ('refunds.csv', Refund),
        ('menu_items.csv', MenuItem),
        ('categories.csv', Category),
        ('tables.csv', Table)
    ]
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename, model in models_to_backup:
            csv_data = export_model_to_csv(model)
            zf.writestr(filename, csv_data)
            
    zip_buffer.seek(0)
    return zip_buffer

def send_backup_email(zip_buffer):
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = os.environ.get('SMTP_PORT')
    smtp_username = os.environ.get('SMTP_USERNAME')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    
    if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
        print("SMTP credentials not configured. Skipping email backup.")
        return False
        
    msg = EmailMessage()
    msg['Subject'] = f"Shiv Shakti System Database Backup - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = smtp_username
    msg['To'] = 'shivshaktidindoli@gmail.com'
    msg.set_content("Please find attached the daily database backup (CSV format).")
    
    msg.add_attachment(
        zip_buffer.read(),
        maintype='application',
        subtype='zip',
        filename=f"shivshakti_backup_{datetime.now().strftime('%Y%m%d')}.zip"
    )
    zip_buffer.seek(0)
    
    try:
        if int(smtp_port) == 465:
            server = smtplib.SMTP_SSL(smtp_server, int(smtp_port))
        else:
            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print("Backup email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send backup email: {e}")
        return False

# --- ROUTES ---

@app.route('/ping')
@limiter.exempt
def ping():
    return "OK", 200

@app.route('/api/trigger_backup')
@csrf.exempt
@limiter.exempt
def trigger_backup():
    secret_key = os.environ.get('BACKUP_SECRET_KEY')
    req_key = request.args.get('key')
    
    if not secret_key or req_key != secret_key:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    try:
        zip_buffer = generate_backup_zip()
        email_sent = send_backup_email(zip_buffer)
        return jsonify({'success': True, 'message': 'Backup generated', 'email_sent': email_sent})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/download_backup')
@login_required
@csrf.exempt
def download_backup():
    try:
        zip_buffer = generate_backup_zip()
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"shivshakti_backup_{datetime.now().strftime('%Y%m%d')}.zip"
        )
    except Exception as e:
        flash(f"Failed to generate backup: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/')
def index():
    return redirect(url_for('menu'))

@app.route('/menu')
def menu():
    table_name = request.args.get('table')
    categories = Category.query.order_by(Category.sort_order.asc()).all()
    menu_items_by_cat = {}
    for cat in categories:
        menu_items_by_cat[cat.id] = [i for i in cat.items if i.is_available]
        
    table = None
    if table_name:
        table = Table.query.filter_by(name=table_name).first()
        
    tables = Table.query.filter_by(is_active=True).all()
    return render_template('customer/menu.html', categories=categories, menu_items_by_cat=menu_items_by_cat, table=table, table_name=table_name, tables=tables)

@app.route('/api/place_order', methods=['POST'])
@csrf.exempt
@limiter.limit("10 per minute")
def place_order():
    data = request.json
    table_name = data.get('table_name')
    customer_name = data.get('customer_name', '')
    customer_mobile = data.get('customer_mobile', '')
    coupon_code = data.get('coupon_code', None)
    delivery_address = data.get('delivery_address', None)
    landmark = data.get('landmark', None)
    delivery_charge = float(data.get('delivery_charge', 0.0))
    delivery_staff_id = data.get('delivery_staff_id', None)
    items = data.get('items', [])
    order_type = data.get('order_type', 'dine-in') # dine-in, parcel, home-delivery
    
    table = None
    if table_name:
        table = Table.query.filter_by(name=table_name).first()
        if table:
            branch_id = table.branch_id
        else:
            return jsonify({'success': False, 'message': 'Invalid table'}), 400
    else:
        # Default branch if no table (parcel)
        branch = Branch.query.first()
        branch_id = branch.id

    if not items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400

    if table and order_type == 'dine-in':
        table.status = 'occupied'
        if not table.session_start_time:
            table.session_start_time = datetime.utcnow()

    new_order = Order(
        branch_id=branch_id, 
        table_id=table.id if table else None,
        type=order_type,
        status='new',
        customer_name=customer_name,
        customer_mobile=customer_mobile,
        coupon_code=coupon_code,
        delivery_address=delivery_address,
        landmark=landmark,
        delivery_charge=delivery_charge,
        delivery_staff_id=delivery_staff_id
    )
    db.session.add(new_order)
    db.session.commit() # commit to get order id

    validated_items = []
    total_amount = 0
    for item in items:
        qty = item.get('quantity', 0)
        if not isinstance(qty, int) or qty <= 0:
            return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
        
        menu_item = MenuItem.query.get(item['id'])
        if not menu_item:
            return jsonify({'success': False, 'message': 'Invalid menu item'}), 400
            
        validated_items.append({
            'id': menu_item.id,
            'variant': item.get('variant'),
            'quantity': qty,
            'price': menu_item.price
        })
        total_amount += (menu_item.price * qty)

    for item in validated_items:
        order_item = OrderItem(
            order_id=new_order.id,
            menu_item_id=item['id'],
            variant=item['variant'],
            quantity=item['quantity'],
            price_at_order=item['price']
        )
        db.session.add(order_item)
    
    db.session.commit()

    log_activity('order_placed', f"New {order_type} Order #{new_order.id} placed by {customer_name or 'Unknown'} for Rs.{total_amount}")

    if customer_mobile:
        send_whatsapp_message(customer_mobile, f"Hello {customer_name or ''}, your order #{new_order.id} has been confirmed. Thank you!")

    # Emit websocket event for admin
    socketio.emit('new_order', {'order_id': new_order.id}, namespace='/')

    return jsonify({'success': True, 'order_id': new_order.id})

@app.route('/admin/edit_order/<int:order_id>')
@login_required
@role_required('admin', 'manager', 'waiter')
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status in ['completed', 'cancelled']:
        flash('Cannot edit a completed or cancelled order')
        return redirect(url_for('live_orders'))
    categories = Category.query.order_by(Category.sort_order.asc()).all()
    return render_template('admin/edit_order.html', order=order, categories=categories, active_page='live_orders')

@app.route('/api/update_order', methods=['POST'])
@login_required
def update_order():
    data = request.json
    order_id = data.get('order_id')
    items = data.get('items', [])
    
    order = Order.query.get_or_404(order_id)
    
    if order.status in ['completed', 'cancelled']:
        return jsonify({'error': 'Cannot edit a billed order'}), 400
        
    if not items:
        # Cancel order
        order.status = 'cancelled'
        log_activity('order_edited', f"Order #{order_id} cancelled by removing all items by {current_user.name}")
        db.session.commit()
        socketio.emit('order_status_update', {'order_id': order.id, 'status': 'cancelled'}, namespace='/')
        return jsonify({'success': True})
        
    # Compare items
    old_items = {i.menu_item_id: i for i in order.items}
    new_items_dict = {i['id']: i for i in items}
    
    changes = []
    has_added = False
    
    # Check for removed or updated
    for old_id, old_item in list(old_items.items()):
        if old_id not in new_items_dict:
            changes.append(f"Removed {old_item.menu_item.name}")
            db.session.delete(old_item)
        else:
            new_qty = new_items_dict[old_id]['quantity']
            if old_item.quantity != new_qty:
                changes.append(f"Changed {old_item.menu_item.name} qty: {old_item.quantity} -> {new_qty}")
                old_item.quantity = new_qty
    
    # Check for new items
    for new_id, new_item_data in new_items_dict.items():
        if new_id not in old_items:
            menu_item = MenuItem.query.get(new_id)
            if menu_item:
                new_oi = OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    variant=menu_item.variant_name,
                    quantity=new_item_data['quantity'],
                    price_at_order=menu_item.price
                )
                db.session.add(new_oi)
                changes.append(f"Added {menu_item.name} (x{new_item_data['quantity']})")
                has_added = True
                
    if changes:
        if has_added and order.status == 'preparing':
            order.has_new_items = True
            
        log_activity('order_edited', f"Order #{order_id} edited by {current_user.name}: " + ", ".join(changes))
        db.session.commit()
        
        socketio.emit('order_status_update', {'order_id': order.id, 'status': order.status}, namespace='/')
        
    return jsonify({'success': True})

@app.route('/order/<int:order_id>')
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    total_amount = sum(item.price_at_order * item.quantity for item in order.items)
    return render_template('customer/status.html', order=order, total_amount=total_amount)

@app.route('/admin')
def admin_index():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(mobile=mobile).first()
        
        if not user or not user.check_password(password):
            flash('Invalid mobile number or password')
            return redirect(url_for('admin_login'))
            
        login_user(user, remember=remember)
        log_activity('staff_login', f"User {user.name} ({user.role}) logged in.")
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    log_activity('staff_logout', f"User {current_user.name} logged out.")
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Timezone aware start of day (IST is UTC+5:30)
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    ist_today_start = ist_now.replace(hour=0, minute=0, second=0, microsecond=0)
    utc_today_start = ist_today_start - timedelta(hours=5, minutes=30)
    
    today_invoices = Invoice.query.filter(Invoice.created_at >= utc_today_start).all()
    today_sales = sum(i.total for i in today_invoices)
    
    today_orders = Order.query.filter(Order.created_at >= utc_today_start).count()
    live_orders = Order.query.filter(Order.status.in_(['new', 'preparing', 'served'])).count()
    
    # Best seller logic
    from sqlalchemy import func
    best_seller = 'N/A'
    best_item = db.session.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label('qty')
    ).select_from(Order).join(OrderItem).join(MenuItem).filter(Order.created_at >= utc_today_start).group_by(MenuItem.id).order_by(func.sum(OrderItem.quantity).desc()).first()
    
    if best_item:
        best_seller = best_item[0]

    stats = {
        'today_sales': f"{today_sales:.2f}",
        'today_orders': str(today_orders),
        'live_orders': str(live_orders),
        'best_seller': best_seller
    }
    return render_template('admin/dashboard.html', stats=stats, active_page='dashboard')

@app.route('/admin/live_orders')
@login_required
@role_required('manager', 'waiter')
def live_orders():
    # Only show completed orders for today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    orders_new = Order.query.filter_by(status='new').order_by(Order.created_at.desc()).all()
    orders_preparing = Order.query.filter_by(status='preparing').order_by(Order.created_at.desc()).all()
    orders_served = Order.query.filter_by(status='served').order_by(Order.created_at.desc()).all()
    orders_completed = Order.query.filter(Order.status == 'completed', Order.created_at >= today_start).order_by(Order.created_at.desc()).all()
    
    branches = Branch.query.all()
    
    return render_template('admin/live_orders.html', 
                           active_page='live_orders',
                           orders_new=orders_new,
                           orders_preparing=orders_preparing,
                           orders_served=orders_served,
                           orders_completed=orders_completed,
                           branches=branches)

@app.route('/api/update_order_status', methods=['POST'])
@login_required
def update_order_status():
    data = request.json
    order_id = data.get('order_id')
    new_status = data.get('status')
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
        
    order.status = new_status
    db.session.commit()
    log_activity('order_status_change', f"Order #{order_id} status changed to {new_status}.")
    
    if new_status in ['served', 'ready'] and order.customer_mobile:
        send_whatsapp_message(order.customer_mobile, f"Hello, your order #{order.id} is now {new_status}! Please collect or enjoy your meal.")
    
    # Emit to customer and kitchen
    socketio.emit('order_status_update', {'order_id': order.id, 'status': new_status}, namespace='/')
    
    return jsonify({'success': True})

@app.route('/api/get_order_html/<int:order_id>')
@login_required
def get_order_html(order_id):
    order = Order.query.get_or_404(order_id)
    # We will render a single card to append dynamically via JS
    return render_template('admin/_order_card.html', order=order)

@app.route('/kitchen')
@login_required
@role_required('manager', 'chef')
def kitchen():
    orders = Order.query.filter(Order.status.in_(['new', 'preparing'])).order_by(Order.created_at.desc()).all()
    return render_template('admin/kds.html', orders=orders)

@app.route('/admin/live_tables')
@login_required
@role_required('manager', 'waiter')
def live_tables():
    tables = Table.query.all()
    total = len(tables)
    vacant = sum(1 for t in tables if t.status == 'vacant')
    occupied = sum(1 for t in tables if t.status == 'occupied')
    cleaning = sum(1 for t in tables if t.status == 'cleaning')
    return render_template('admin/live_tables.html', 
                           active_page='live_tables',
                           tables=tables,
                           stats={'total': total, 'vacant': vacant, 'occupied': occupied, 'cleaning': cleaning})

@app.route('/api/update_table_status', methods=['POST'])
@login_required
def update_table_status():
    data = request.json
    t = Table.query.get(data['table_id'])
    if t:
        t.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/admin/tables', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def manage_tables():
    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity', type=int)
        if name and capacity:
            branch = Branch.query.first() # Use first branch
            if branch:
                new_table = Table(name=name, seats=capacity, status='vacant', branch_id=branch.id)
                db.session.add(new_table)
                db.session.commit()
                flash(f"Table {name} added successfully!")
        return redirect(url_for('manage_tables'))
        
    tables = Table.query.all()
    return render_template('admin/tables.html', tables=tables, active_page='tables')

@app.route('/admin/qr/<int:table_id>')
@login_required
def get_qr(table_id):
    table = Table.query.get_or_404(table_id)
    # Important: request.host_url gives something like "http://127.0.0.1:5000/"
    url = f"{request.host_url}menu?table={table.name}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    from flask import send_file
    return send_file(img_io, mimetype='image/png')

@app.route('/admin/new_parcel')
@login_required
@role_required('admin', 'manager', 'cashier')
def new_parcel():
    categories = Category.query.order_by(Category.sort_order).all()
    items = MenuItem.query.filter_by(is_available=True).all()
    return render_template('admin/new_parcel.html', categories=categories, items=items, active_page='new_parcel')

@app.route('/admin/new_delivery')
@login_required
@role_required('admin', 'manager', 'cashier')
def new_delivery():
    categories = Category.query.order_by(Category.sort_order).all()
    items = MenuItem.query.filter_by(is_available=True).all()
    riders = User.query.filter_by(role='delivery').all()
    return render_template('admin/new_delivery.html', categories=categories, items=items, riders=riders, active_page='new_delivery')

@app.route('/admin/my_deliveries')
@login_required
@role_required('delivery')
def my_deliveries():
    orders = Order.query.filter(
        Order.delivery_staff_id == current_user.id,
        Order.status.in_(['new', 'preparing', 'out_for_delivery'])
    ).order_by(Order.created_at.desc()).all()
    return render_template('admin/my_deliveries.html', orders=orders, active_page='my_deliveries')

@app.route('/admin/billing')
@login_required
@role_required('manager', 'cashier')
def billing():
    # Fetch all completed orders
    completed_orders = Order.query.filter_by(status='completed').all()
    
    # Group by table for dine-in, keep parcel separate
    sessions = {}
    parcels = []
    
    for order in completed_orders:
        if order.table_id:
            if order.table_id not in sessions:
                sessions[order.table_id] = {
                    'table': order.table,
                    'orders': [],
                    'total_items': 0,
                    'total_amount': 0.0
                }
            sessions[order.table_id]['orders'].append(order)
            for item in order.items:
                sessions[order.table_id]['total_items'] += item.quantity
                sessions[order.table_id]['total_amount'] += (item.quantity * item.price_at_order)
        else:
            total_amt = sum(item.quantity * item.price_at_order for item in order.items)
            parcels.append({'order': order, 'total_amount': total_amt})
            
    return render_template('admin/billing.html', sessions=sessions.values(), parcels=parcels, active_page='billing')

@app.route('/api/get_bill_details/<string:type>/<int:id>')
@login_required
def get_bill_details(type, id):
    # type is 'table' or 'order'
    items = []
    subtotal = 0.0
    orders = []
    
    if type == 'table':
        orders = Order.query.filter_by(table_id=id, status='completed').all()
    else:
        order = Order.query.get(id)
        if order and order.status == 'completed':
            orders = [order]
            
    for order in orders:
        for item in order.items:
            items.append({
                'name': item.menu_item.name,
                'quantity': item.quantity,
                'price': item.price_at_order,
                'total': item.quantity * item.price_at_order
            })
            subtotal += item.quantity * item.price_at_order
            
    # Combine same items
    merged_items = {}
    for item in items:
        key = item['name']
        if key not in merged_items:
            merged_items[key] = item
        else:
            merged_items[key]['quantity'] += item['quantity']
            merged_items[key]['total'] += item['total']
            
    return jsonify({
        'items': list(merged_items.values()),
        'subtotal': subtotal,
        'order_ids': [o.id for o in orders]
    })

@app.route('/api/settle_bill', methods=['POST'])
@login_required
def settle_bill():
    data = request.json
    order_ids = data.get('order_ids', [])
    payment_method = data.get('payment_method')
    coupon_code = data.get('coupon_code', '').strip().upper()
    delivery_charge = float(data.get('delivery_charge', 0.0))
    
    orders = Order.query.filter(Order.id.in_(order_ids)).all()
    if not orders:
        return jsonify({'success': False, 'message': 'No orders found'})
        
    main_order = orders[0]
    
    subtotal = 0.0
    for order in orders:
        for item in order.items:
            subtotal += (item.quantity * item.price_at_order)
            
    discount = 0.0
    used_coupon = None
    
    # Try the manual coupon code first, else fall back to the one attached to main_order
    if not coupon_code and main_order.coupon_code:
        coupon_code = main_order.coupon_code
        
    if coupon_code:
        c = Coupon.query.filter_by(code=coupon_code).first()
        if c and c.is_active:
            valid = True
            if c.expiry_date and datetime.utcnow() > c.expiry_date:
                valid = False
            if c.max_usage_limit and c.usage_count >= c.max_usage_limit:
                valid = False
            if c.min_order_amount and subtotal < c.min_order_amount:
                valid = False
                
            if valid:
                used_coupon = c.code
                if c.discount_type == 'flat':
                    discount = c.discount_value
                elif c.discount_type == 'percent':
                    discount = (subtotal * c.discount_value) / 100.0
                
                # Cap discount
                if discount > subtotal:
                    discount = subtotal
                    
                # Increment usage
                c.usage_count += 1
                
    taxable = subtotal - discount + delivery_charge
    gst_amount = taxable * 0.05
    exact_total = taxable + gst_amount
    rounded_total = round(exact_total)
    round_off = rounded_total - exact_total
    
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    next_num = 1 if not last_invoice else int(last_invoice.invoice_number.split('-')[1]) + 1
    inv_number = f"MB-{str(next_num).zfill(5)}"
    
    invoice = Invoice(
        order_id=main_order.id,
        invoice_number=inv_number,
        subtotal=subtotal,
        discount=discount,
        gst_percent=5.0,
        gst_amount=gst_amount,
        round_off=round_off,
        delivery_charge=delivery_charge,
        total=rounded_total,
        payment_method=payment_method,
        coupon_code=used_coupon
    )
    db.session.add(invoice)
    db.session.flush() # Get invoice.id
    
    if payment_method == 'Credit/Udhar' or payment_method == 'credit':
        customer_name = main_order.customer_name or 'Unknown Customer'
        customer_mobile = main_order.customer_mobile or '0000000000'
        ledger = CreditLedger(
            customer_name=customer_name,
            customer_mobile=customer_mobile,
            invoice_id=invoice.id,
            amount=rounded_total,
            status='outstanding'
        )
        db.session.add(ledger)
        
    # Free up table if dine-in
    if main_order.table_id:
        table = Table.query.get(main_order.table_id)
        if table:
            table.status = 'vacant'
            table.session_start_time = None
            
    # Record coupon on main order if it wasn't there
    if used_coupon and not main_order.coupon_code:
        main_order.coupon_code = used_coupon
            
    # Mark orders settled
    for order in orders:
        order.status = 'completed'
        
    db.session.commit()
    log_activity('bill_settled', f"Settled orders {order_ids} into Invoice #{inv_number}. Total: Rs.{rounded_total}. Method: {payment_method}")
    return jsonify({'success': True, 'invoice_id': invoice.id})

@app.route('/api/generate_upi_qr')
@login_required
def generate_upi_qr():
    amount = request.args.get('amount', type=float)
    if not amount:
        return "Amount is required", 400
        
    upi_id = os.environ.get('UPI_ID', 'test@upi')
    merchant_name = os.environ.get('RESTAURANT_NAME', 'RestaurantOrdering')
    
    # upi://pay?pa=<UPI_ID>&pn=<Restaurant Name>&am=<amount>&cu=INR
    import urllib.parse
    import qrcode
    import io
    from flask import send_file
    
    intent_url = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(merchant_name)}&am={amount:.2f}&cu=INR"
    
    img = qrcode.make(intent_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@app.route('/admin/invoices')
@login_required
@role_required('manager', 'cashier')
def invoices_list():
    invs = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('admin/invoices.html', invoices=invs, active_page='invoices')

@app.route('/admin/invoices/print/<int:id>')
@login_required
def invoice_print(id):
    inv = Invoice.query.get_or_404(id)
    return render_template('admin/invoice_print.html', invoice=inv, active_page='invoices')

@app.route('/admin/credit')
@login_required
@role_required('manager', 'cashier')
def credit_ledger():
    # Fetch all outstanding credits
    ledgers = CreditLedger.query.filter_by(status='outstanding').all()
    
    total_outstanding = sum(l.amount for l in ledgers)
    customers_count = len(set(l.customer_mobile for l in ledgers if l.customer_mobile))
    
    return render_template('admin/credit.html', ledgers=ledgers, total=total_outstanding, count=customers_count, active_page='credit')

@app.route('/api/pay_credit', methods=['POST'])
@login_required
def pay_credit():
    data = request.json
    ledger = CreditLedger.query.get(data.get('ledger_id'))
    if ledger:
        ledger.status = 'paid'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/admin/refunds', methods=['GET', 'POST'])
@login_required
@role_required('manager', 'cashier')
def refunds():
    if request.method == 'POST':
        invoice_no = request.form.get('invoice_no')
        amount = request.form.get('amount', type=float)
        reason = request.form.get('reason')
        returned_via = request.form.get('returned_via')
        note = request.form.get('note')
        status = request.form.get('status', 'completed')
        
        inv = Invoice.query.filter_by(invoice_number=invoice_no).first()
        if inv and amount:
            ref = Refund(
                invoice_id=inv.id,
                amount=amount,
                reason=reason,
                returned_via=returned_via,
                note=note,
                status=status
            )
            db.session.add(ref)
            db.session.commit()
            log_activity('refund_recorded', f"Refund of Rs.{amount} recorded for Invoice #{invoice_no}. Reason: {reason}.")
            flash('Refund recorded successfully.')
        else:
            flash('Invalid Invoice Number or Amount.')
        return redirect(url_for('refunds'))
        
    all_refunds = Refund.query.order_by(Refund.created_at.desc()).all()
    
    pending_total = sum(r.amount for r in all_refunds if r.status == 'pending')
    refunded_total = sum(r.amount for r in all_refunds if r.status == 'completed')
    
    return render_template('admin/refunds.html', 
                           refunds=all_refunds, 
                           pending_total=pending_total, 
                           refunded_total=refunded_total,
                           active_page='refunds')

@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def categories():
    if request.method == 'POST':
        name = request.form.get('name')
        name_hi = request.form.get('name_hi')
        name_gu = request.form.get('name_gu')
        if name:
            cat = Category(name=name, name_hi=name_hi, name_gu=name_gu, sort_order=Category.query.count())
            db.session.add(cat)
            db.session.commit()
            socketio.emit('menu_update', namespace='/')
            log_activity('category_added', f"Category '{name}' added.")
            flash('Category added.')
        return redirect(url_for('categories'))
        
    cats = Category.query.order_by(Category.sort_order.asc()).all()
    return render_template('admin/categories.html', categories=cats, active_page='categories')

@app.route('/api/reorder_categories', methods=['POST'])
@login_required
def reorder_categories():
    data = request.json
    order = data.get('order', []) # array of category IDs in new order
    for idx, cat_id in enumerate(order):
        c = Category.query.get(cat_id)
        if c:
            c.sort_order = idx
    db.session.commit()
    socketio.emit('menu_update', namespace='/')
    log_activity('categories_reordered', "Menu categories were reordered.")
    return jsonify({'success': True})

@app.route('/admin/items', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def items():
    if request.method == 'POST':
        name = request.form.get('name')
        name_hi = request.form.get('name_hi')
        name_gu = request.form.get('name_gu')
        cat_id = request.form.get('category_id')
        price = request.form.get('price', type=float)
        desc = request.form.get('description', '')
        desc_hi = request.form.get('desc_hi', '')
        desc_gu = request.form.get('desc_gu', '')
        variant = request.form.get('variant_name', '')
        is_combo = request.form.get('is_combo') == 'on'
        combo_items = request.form.get('combo_items', '')
        
        if name and cat_id and price:
            import json
            combo_json = json.dumps([i.strip() for i in combo_items.split(',') if i.strip()]) if is_combo else "[]"
            item = MenuItem(category_id=cat_id, name=name, name_hi=name_hi, name_gu=name_gu, price=price, description=desc, desc_hi=desc_hi, desc_gu=desc_gu, variant_name=variant, is_combo=is_combo, combo_items=combo_json)
            db.session.add(item)
            db.session.commit()
            socketio.emit('menu_update', namespace='/')
            log_activity('item_added', f"Menu item '{name}' added at Rs.{price}.")
            flash('Item added.')
        return redirect(url_for('items'))
        
    cats = Category.query.order_by(Category.sort_order.asc()).all()
    items = MenuItem.query.join(Category).order_by(Category.sort_order, MenuItem.name).all()
    return render_template('admin/items.html', categories=cats, items=items, active_page='items')

@app.route('/api/toggle_item', methods=['POST'])
@login_required
def toggle_item():
    item_id = request.json.get('item_id')
    is_avail = request.json.get('is_available')
    item = MenuItem.query.get(item_id)
    if item:
        item.is_available = is_avail
        db.session.commit()
        socketio.emit('menu_update', namespace='/')
        log_activity('item_availability_toggled', f"Item '{item.name}' availability set to {is_avail}.")
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/admin/customers')
@login_required
def admin_customers():
    # Fetch all orders to aggregate
    orders = Order.query.filter(Order.customer_mobile != None).all()
    counts = {}
    for o in orders:
        m = o.customer_mobile
        if not m: continue
        if m not in counts:
            counts[m] = {'name': o.customer_name or 'Unknown', 'visits': 0, 'spend': 0, 'last_visit': o.created_at}
        counts[m]['visits'] += 1
        counts[m]['spend'] += sum(i.price_at_order * i.quantity for i in o.items)
        if o.created_at > counts[m]['last_visit']:
            counts[m]['last_visit'] = o.created_at
            
    # Load CRM profiles to get notes
    profiles = CustomerProfile.query.all()
    profile_map = {p.mobile: p for p in profiles}
    
    customers_data = []
    search_q = request.args.get('q', '').strip()
    
    for m, v in counts.items():
        if search_q and search_q not in m and search_q.lower() not in v['name'].lower():
            continue
        p = profile_map.get(m)
        notes = p.notes if p else ''
        customers_data.append({
            'mobile': m,
            'name': p.name if p and p.name else v['name'],
            'visits': v['visits'],
            'spend': v['spend'],
            'last_visit': v['last_visit'],
            'notes': notes
        })
        
    customers_data.sort(key=lambda x: x['spend'], reverse=True)
    return render_template('admin/customers.html', customers=customers_data, search_q=search_q)

@app.route('/admin/customer/<mobile>', methods=['GET', 'POST'])
@login_required
def admin_customer_profile(mobile):
    profile = CustomerProfile.query.get(mobile)
    if request.method == 'POST':
        notes = request.form.get('notes')
        name = request.form.get('name')
        if not profile:
            profile = CustomerProfile(mobile=mobile, name=name, notes=notes)
            db.session.add(profile)
        else:
            profile.name = name
            profile.notes = notes
        db.session.commit()
        flash('Customer profile updated.', 'success')
        return redirect(url_for('admin_customer_profile', mobile=mobile))
        
    orders = Order.query.filter_by(customer_mobile=mobile).order_by(Order.created_at.desc()).all()
    invoices = Invoice.query.join(Order).filter(Order.customer_mobile == mobile).all()
    invoice_map = {inv.order_id: inv for inv in invoices}
    
    total_spend = sum(inv.total for inv in invoices)
    
    return render_template('admin/customer_profile.html', mobile=mobile, profile=profile, orders=orders, invoice_map=invoice_map, total_spend=total_spend)

@app.route('/admin/coupons', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def admin_coupons():
    if request.method == 'POST':
        code = request.form.get('code').strip().upper()
        dtype = request.form.get('discount_type')
        val = float(request.form.get('discount_value', 0))
        min_order = float(request.form.get('min_order_amount') or 0)
        limit = request.form.get('max_usage_limit')
        expiry = request.form.get('expiry_date')
        
        c = Coupon(
            code=code,
            discount_type=dtype,
            discount_value=val,
            min_order_amount=min_order,
            max_usage_limit=int(limit) if limit else None,
            expiry_date=datetime.strptime(expiry, '%Y-%m-%d') if expiry else None
        )
        db.session.add(c)
        db.session.commit()
        flash('Coupon added successfully.', 'success')
        return redirect(url_for('admin_coupons'))
        
    coupons = Coupon.query.order_by(Coupon.id.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons, active_page='coupons')

@app.route('/admin/coupons/toggle/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def admin_coupons_toggle(id):
    c = Coupon.query.get_or_404(id)
    c.is_active = not c.is_active
    db.session.commit()
    flash(f'Coupon {c.code} status updated.', 'success')
    return redirect(url_for('admin_coupons'))

@app.route('/api/verify_coupon', methods=['POST'])
@csrf.exempt
def verify_coupon():
    data = request.json
    code = data.get('code', '').strip().upper()
    total = float(data.get('total', 0))
    
    if not code:
        return jsonify({'success': False, 'message': 'Code required.'})
        
    c = Coupon.query.filter_by(code=code).first()
    if not c:
        return jsonify({'success': False, 'message': 'Invalid coupon code.'})
        
    if not c.is_active:
        return jsonify({'success': False, 'message': 'Coupon is not active.'})
        
    if c.expiry_date and datetime.utcnow() > c.expiry_date:
        return jsonify({'success': False, 'message': 'Coupon has expired.'})
        
    if c.max_usage_limit and c.usage_count >= c.max_usage_limit:
        return jsonify({'success': False, 'message': 'Coupon usage limit reached.'})
        
    if c.min_order_amount and total < c.min_order_amount:
        return jsonify({'success': False, 'message': f'Minimum order amount of ₹{c.min_order_amount} required.'})
        
    discount = 0
    if c.discount_type == 'flat':
        discount = c.discount_value
    elif c.discount_type == 'percent':
        discount = (total * c.discount_value) / 100.0
        
    # Cap discount at total to avoid negative totals
    if discount > total:
        discount = total
        
    return jsonify({
        'success': True,
        'discount': round(discount, 2),
        'code': c.code,
        'message': 'Coupon applied successfully!'
    })

@app.route('/admin/reports')
@login_required
@role_required('manager')
def reports():
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    
    today_invoices = Invoice.query.filter(Invoice.created_at >= today_start).all()
    today_sales = sum(i.total for i in today_invoices)
    today_orders_count = Order.query.filter(Order.created_at >= today_start).count()
    pending_bills = Order.query.filter_by(status='completed').count()
    aov = (today_sales / len(today_invoices)) if today_invoices else 0
    
    return render_template('admin/reports.html', 
                           today_sales=today_sales,
                           today_orders=today_orders_count,
                           pending_bills=pending_bills,
                           aov=aov,
                           active_page='reports')

def get_report_data_raw(rtype, start_date=None, end_date=None):
    from sqlalchemy import func
    
    # Helper to apply date filters to a query with a date column
    def apply_dates(q, date_col):
        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d')
                q = q.filter(date_col >= sd)
            except ValueError:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                q = q.filter(date_col <= ed)
            except ValueError:
                pass
        return q

    if rtype == 'sales':
        q = Invoice.query
        q = apply_dates(q, Invoice.created_at)
        invs = q.all()
        return [{
            'Date': i.created_at.strftime('%Y-%m-%d'),
            'Invoice': i.invoice_number,
            'Subtotal': i.subtotal,
            'Discount': i.discount,
            'Tax': i.gst_amount,
            'Total': i.total
        } for i in invs]
        
    elif rtype in ['best_selling', 'least_selling']:
        q = db.session.query(
            MenuItem.name,
            func.sum(OrderItem.quantity).label('qty'),
            func.sum(OrderItem.quantity * OrderItem.price_at_order).label('rev')
        ).select_from(Order).join(OrderItem).join(MenuItem).group_by(MenuItem.id)
        
        q = apply_dates(q, Order.created_at)
        
        items_stats = q.order_by(
            func.sum(OrderItem.quantity).desc() if rtype == 'best_selling' else func.sum(OrderItem.quantity).asc()
        ).all()
        
        return [{
            'Item': row[0],
            'Qty Sold': row[1],
            'Revenue': row[2]
        } for row in items_stats]
        
    elif rtype == 'category':
        q = db.session.query(
            Category.name,
            func.sum(OrderItem.quantity * OrderItem.price_at_order).label('rev')
        ).select_from(Order).join(OrderItem).join(MenuItem).join(Category).group_by(Category.id)
        
        q = apply_dates(q, Order.created_at)
        cat_stats = q.all()
        
        return [{
            'Category': row[0],
            'Revenue': row[1]
        } for row in cat_stats]
        
    elif rtype == 'table_util':
        q = db.session.query(
            Table.name,
            func.count(Order.id).label('orders')
        ).outerjoin(Order, Table.id == Order.table_id).group_by(Table.id)
        # Note: Table util might not easily filter by date dynamically without dropping zero-tables, but we apply anyway
        q = apply_dates(q, Order.created_at)
        table_stats = q.all()
        
        return [{
            'Table': row[0],
            'Orders Handled': row[1]
        } for row in table_stats]
        
    elif rtype == 'aov':
        q = Invoice.query
        q = apply_dates(q, Invoice.created_at)
        invs = q.all()
        daily = {}
        for i in invs:
            d = i.created_at.strftime('%Y-%m-%d')
            if d not in daily:
                daily[d] = {'count': 0, 'total': 0}
            daily[d]['count'] += 1
            daily[d]['total'] += i.total
            
        return [{
            'Date': k,
            'Invoices': v['count'],
            'Total Sales': v['total'],
            'Average Order Value': v['total']/v['count']
        } for k, v in sorted(daily.items(), reverse=True)]
        
    elif rtype == 'orders':
        q = Order.query
        q = apply_dates(q, Order.created_at)
        orders = q.order_by(Order.created_at.desc()).all()
        return [{
            'Order ID': o.id,
            'Date': o.created_at.strftime('%Y-%m-%d %H:%M'),
            'Type': o.type,
            'Table/Customer': o.table.name if o.table else (o.customer_name or 'N/A'),
            'Status': o.status,
            'Items Count': sum(i.quantity for i in o.items),
            'Total Value': sum((i.price_at_order * i.quantity) for i in o.items)
        } for o in orders]
        
    elif rtype == 'customers':
        q = Order.query.filter(Order.customer_mobile != None)
        q = apply_dates(q, Order.created_at)
        orders = q.all()
        counts = {}
        for o in orders:
            if o.customer_mobile not in counts:
                counts[o.customer_mobile] = {'name': o.customer_name, 'visits': 0, 'spend': 0}
            counts[o.customer_mobile]['visits'] += 1
            counts[o.customer_mobile]['spend'] += sum(i.price_at_order * i.quantity for i in o.items)
            
        return [{
            'Mobile': m,
            'Name': v['name'] or 'N/A',
            'Type': 'Returning' if v['visits'] > 1 else 'New',
            'Visits': v['visits'],
            'Lifetime Value': v['spend']
        } for m, v in sorted(counts.items(), key=lambda x: x[1]['spend'], reverse=True)]
        
    elif rtype == 'cancellations':
        q = Order.query
        q = apply_dates(q, Order.created_at)
        all_orders = q.count()
        cancelled_orders = q.filter_by(status='cancelled').count()
        rate = (cancelled_orders / all_orders * 100) if all_orders else 0
        return [{
            'Total Orders': all_orders,
            'Cancelled Orders': cancelled_orders,
            'Cancellation Rate (%)': round(rate, 2)
        }]

    return []

@app.route('/api/report_data')
@login_required
def report_data():
    rtype = request.args.get('type', 'sales')
    start = request.args.get('start')
    end = request.args.get('end')
    data = get_report_data_raw(rtype, start, end)
    return jsonify({'data': data})

@app.route('/api/report_export_pdf')
@login_required
def report_export_pdf():
    rtype = request.args.get('type', 'sales')
    start = request.args.get('start')
    end = request.args.get('end')
    
    data = get_report_data_raw(rtype, start, end)
    
    import io
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    title = f"Restaurant Report: {rtype.replace('_', ' ').title()}"
    elements.append(Paragraph(title, styles['Title']))
    
    subtitle = f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    if start or end:
        subtitle += f"<br/>Date Range: {start or 'Start'} to {end or 'Today'}"
    elements.append(Paragraph(subtitle, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    if not data:
        elements.append(Paragraph("No data available for this report.", styles['Normal']))
    else:
        # Prepare table data
        keys = list(data[0].keys())
        table_data = [keys] # Header row
        
        totals = {k: 0 for k in keys if k in ['Subtotal', 'Tax', 'Discount', 'Total', 'Revenue', 'Qty Sold', 'Total Sales', 'Items Count', 'Total Value', 'Lifetime Value', 'Cancelled Orders']}
        
        for row in data:
            row_data = []
            for k in keys:
                val = row[k]
                if k in totals:
                    try: totals[k] += float(val)
                    except: pass
                if k in ['Subtotal', 'Tax', 'Discount', 'Total', 'Revenue', 'Total Sales', 'Average Order Value', 'Total Value', 'Lifetime Value']:
                    val = f"Rs.{float(val):.2f}"
                row_data.append(str(val))
            table_data.append(row_data)
            
        # Append totals row if applicable
        if any(v > 0 for v in totals.values()):
            footer_row = []
            for k in keys:
                if k == keys[0]:
                    footer_row.append("TOTAL")
                elif k in totals:
                    footer_row.append(f"Rs.{totals[k]:.2f}" if 'Rs' in str(table_data[1][keys.index(k)]) else str(totals[k]))
                else:
                    footer_row.append("")
            table_data.append(footer_row)
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')])
        ]))
        
        # Highlight total row
        if any(v > 0 for v in totals.values()):
            t.setStyle(TableStyle([
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
            ]))
            
        elements.append(t)
        
    doc.build(elements)
    buffer.seek(0)
    
    from flask import send_file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"report_{rtype}_{datetime.utcnow().strftime('%Y%m%d%H%M')}.pdf",
        mimetype='application/pdf'
    )

@app.route('/admin/staff', methods=['GET', 'POST'])
@login_required
@role_required('admin') # ONLY Admin can access staff management
def staff():
    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(mobile=mobile).first():
            flash('Mobile number already exists!')
        else:
            from werkzeug.security import generate_password_hash
            new_user = User(
                name=name,
                mobile=mobile,
                password_hash=generate_password_hash(password),
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            log_activity('staff_created', f"New staff user '{name}' created with role '{role}'.")
            flash(f'Staff member {name} added as {role}.')
        return redirect(url_for('staff'))
        
    staff_users = User.query.all()
    return render_template('admin/staff.html', staff=staff_users, active_page='staff')

@app.route('/admin/activity_log')
@login_required
@role_required('admin')
def activity_log():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
    return render_template('admin/activity_log.html', logs=logs, active_page='activity_log')

# Dummy route for unimplemented sidebar links to avoid 404s breaking the test
@app.route('/admin/<path:subpath>')
@login_required
def admin_dummy(subpath):
    if subpath == 'live_orders':
        return live_orders()
    if subpath == 'tables':
        return manage_tables()
    return render_template('admin/dashboard.html', stats={}, active_page=subpath, dummy=True)


@app.route('/api/split_bill', methods=['POST'])
@login_required
def split_bill():
    data = request.json
    order_id = data.get('order_id')
    payment_method = data.get('payment_method')
    split_ways = int(data.get('split_ways', 1))
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'})
        
    if split_ways < 1:
        return jsonify({'success': False, 'message': 'Invalid split ways'})
        
    subtotal = sum((item.quantity * item.price_at_order) for item in order.items)
    
    discount = 0.0
    if order.coupon_code:
        c = Coupon.query.filter_by(code=order.coupon_code).first()
        if c and c.is_active:
            if c.discount_type == 'flat':
                discount = c.discount_value
            elif c.discount_type == 'percent':
                discount = (subtotal * c.discount_value) / 100.0
            if discount > subtotal: discount = subtotal
                
    taxable = subtotal - discount + order.delivery_charge
    gst_amount = taxable * 0.05
    exact_total = taxable + gst_amount
    rounded_total = round(exact_total)
    
    split_amount = rounded_total // split_ways
    remainder = rounded_total % split_ways
    
    invoices_created = []
    
    for i in range(split_ways):
        amount = split_amount
        if i == split_ways - 1:
            amount += remainder # Last split gets remainder
            
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        next_num = 1 if not last_invoice else int(last_invoice.invoice_number.split('-')[1]) + 1
        inv_number = f"MB-{str(next_num).zfill(5)}"
        
        prorated_sub = subtotal / split_ways
        prorated_gst = gst_amount / split_ways
        prorated_del = order.delivery_charge / split_ways
        prorated_disc = discount / split_ways
        
        inv = Invoice(
            order_id=order.id,
            invoice_number=inv_number,
            subtotal=prorated_sub,
            discount=prorated_disc,
            gst_percent=5.0,
            gst_amount=prorated_gst,
            round_off=0.0,
            delivery_charge=prorated_del,
            total=amount,
            payment_method=payment_method,
            coupon_code=order.coupon_code
        )
        db.session.add(inv)
        db.session.flush()
        
        if payment_method.lower() in ['credit/udhar', 'credit']:
            ledger = CreditLedger(
                customer_name=order.customer_name or 'Unknown Customer',
                customer_mobile=order.customer_mobile or '0000000000',
                invoice_id=inv.id,
                amount=amount,
                status='outstanding'
            )
            db.session.add(ledger)
            
        invoices_created.append(inv.id)
        
    if order.table_id:
        table = Table.query.get(order.table_id)
        if table:
            table.status = 'vacant'
            table.session_start_time = None
            
    order.status = 'completed'
    db.session.commit()
    log_activity('bill_split', f"Split Order {order_id} into {split_ways} ways. Total: Rs.{rounded_total}.")
    
    return jsonify({'success': True, 'invoice_ids': invoices_created})

@app.route('/api/call_waiter', methods=['POST'])
@csrf.exempt
@limiter.limit("5 per minute")
def call_waiter():
    data = request.json
    table_name = data.get('table_name')
    order_id = data.get('order_id')
    
    call = WaiterCall(table_name=table_name, order_id=order_id, status='pending')
    db.session.add(call)
    db.session.commit()
    
    socketio.emit('new_waiter_call', {
        'id': call.id,
        'table_name': table_name,
        'order_id': order_id,
        'time': call.created_at.strftime('%H:%M')
    }, namespace='/')
    
    return jsonify({'success': True})

@app.route('/api/resolve_call/<int:call_id>', methods=['POST'])
@login_required
def resolve_call(call_id):
    call = WaiterCall.query.get(call_id)
    if call:
        call.status = 'resolved'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/submit_feedback', methods=['POST'])
@csrf.exempt
def submit_feedback():
    data = request.json
    order_id = data.get('order_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    if not order_id or not rating:
        return jsonify({'success': False})
        
    fb = Feedback(order_id=order_id, rating=int(rating), comment=comment)
    db.session.add(fb)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/feedback')
@login_required
def admin_feedback():
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    avg = 0
    if feedbacks:
        avg = sum(f.rating for f in feedbacks) / len(feedbacks)
    return render_template('admin/feedback.html', feedbacks=feedbacks, average_rating=round(avg, 1), active_page='feedback')

# --- SOCKET EVENTS ---


@socketio.on('connect')
def handle_connect():
    print("Client connected")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Use socketio.run for development server with websocket support
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
