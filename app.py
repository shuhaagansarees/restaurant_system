import gevent.monkey
gevent.monkey.patch_all()
import threading
import gevent
class GeventTimer:
    def __init__(self, interval, function, args=None, kwargs=None):
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self._g = None
        self.name = 'GeventTimer'
        self.daemon = True
        self.ident = None
    def start(self):
        self._g = gevent.spawn_later(self.interval, self.function, *self.args, **self.kwargs)
    def cancel(self):
        if self._g: self._g.kill()
    def join(self, timeout=None):
        if self._g: self._g.join(timeout=timeout)
    def is_alive(self):
        return bool(self._g and not self._g.ready())
threading.Timer = GeventTimer
import os
import json
import qrcode
import io
import csv
import zipfile
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from background_tasks import bg_queue, _send_whatsapp_task, _send_email_task
from flask_socketio import SocketIO
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from functools import wraps
from flask import abort, current_app
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.orm import joinedload

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

from models import db, User, Branch, Category, MenuItem, Table, Order, OrderItem, Invoice, CreditLedger, Refund, ActivityLog, Coupon, CustomerProfile, WaiterCall, Feedback, DayEndRecord, RawMaterial, InventoryLog, Expense, CashFlow, OutletSetting

load_dotenv()

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    import secrets
    import warnings
    new_key = secrets.token_hex(24)
    env_path = os.path.join(basedir, '.env')
    try:
        with open(env_path, 'a') as f:
            f.write(f"\nSECRET_KEY={new_key}\n")
        print("WARNING: New SECRET_KEY auto-generated, please verify .env is persistent")
        secret_key = new_key
    except Exception as e:
        warnings.warn(f"Failed to write SECRET_KEY to .env: {e}. Sessions will invalidate on restart!")
        secret_key = os.urandom(24)
app.config['SECRET_KEY'] = secret_key
app.permanent_session_lifetime = timedelta(minutes=30)

db_dir = os.path.join(basedir, 'database')
os.makedirs(db_dir, exist_ok=True)

# Use DATABASE_URL for Neon Postgres if available, otherwise fallback to local SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render and some providers use postgres:// which is deprecated in SQLAlchemy 1.4+
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in database_url and "neon.tech" in database_url:
        sep = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{sep}sslmode=require"
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 40,
        'pool_timeout': 30,
    }
else:
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

import time
GLOBAL_LAST_UPDATE_TIMESTAMP = time.time()
def update_global_timestamp(*args, **kwargs):
    global GLOBAL_LAST_UPDATE_TIMESTAMP
    GLOBAL_LAST_UPDATE_TIMESTAMP = time.time()

class DummySocket:
    def emit(self, *args, **kwargs):
        update_global_timestamp()
    def run(self, app, **kwargs):
        kwargs.pop('allow_unsafe_werkzeug', None)
        app.run(**kwargs)
    def on(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

socketio = DummySocket()
login_manager = LoginManager()
login_manager.login_view = 'admin_login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_inventory_alerts():
    try:
        if current_user.is_authenticated and current_user.role in ['admin', 'manager']:
            low_stock_items = RawMaterial.query.filter(RawMaterial.current_stock <= RawMaterial.low_stock_threshold).all()
            return dict(low_stock_items=low_stock_items)
    except Exception as e:
        print(f"Error in inject_inventory_alerts: {e}")
    return dict(low_stock_items=[])


# Create tables and auto-seed on startup safely
def init_database_and_seed():
    with app.app_context():
        try:
            db.create_all()
            
            # Execute CREATE INDEX for performance optimization explicitly for existing tables
            from sqlalchemy import text
            index_queries = [
                "CREATE INDEX IF NOT EXISTS ix_menu_items_category_id ON menu_items (category_id);",
                "CREATE INDEX IF NOT EXISTS ix_orders_branch_id ON orders (branch_id);",
                "CREATE INDEX IF NOT EXISTS ix_orders_table_id ON orders (table_id);",
                "CREATE INDEX IF NOT EXISTS ix_orders_status ON orders (status);",
                "CREATE INDEX IF NOT EXISTS ix_orders_created_at ON orders (created_at);",
                "CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items (order_id);",
                "CREATE INDEX IF NOT EXISTS ix_invoices_order_id ON invoices (order_id);",
                "CREATE INDEX IF NOT EXISTS ix_invoices_created_at ON invoices (created_at);"
            ]
            for q in index_queries:
                try:
                    db.session.execute(text(q))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    
        except Exception as e:
            print(f"Error in db.create_all: {e}")

        # License Key Sync
        client_license = os.environ.get('CLIENT_LICENSE_KEY')
        if client_license:
            try:
                first_branch = Branch.query.first()
                if first_branch and first_branch.license_key != client_license:
                    first_branch.license_key = client_license
                    db.session.commit()
            except Exception:
                db.session.rollback()

        # Auto-seed logic for fresh deployments & menu loading
        try:
            if User.query.count() == 0:
                print("Empty database detected. Running auto-seed...")
                import seed
                seed.seed_data()
                print("Auto-seed successful!")
            elif Category.query.count() == 0:
                import seed
                seed.load_menu_from_csv()
                print("Menu auto-loaded from CSV!")
        except Exception as e:
            print(f"Auto-seed warning: {e}")
            db.session.rollback()

        # Auto-sync menu items to inventory if RawMaterial is empty
        try:
            if RawMaterial.query.count() == 0 and MenuItem.query.count() > 0:
                for mi in MenuItem.query.all():
                    mat = RawMaterial(
                        name=mi.name.strip(),
                        unit='pcs',
                        current_stock=20.0,
                        low_stock_threshold=5.0
                    )
                    db.session.add(mat)
                db.session.commit()
                print("All menu items auto-synced to inventory with 20.0 initial stock!")
        except Exception as e:
            print(f"Inventory auto-sync error: {e}")
            db.session.rollback()

try:
    init_database_and_seed()
except Exception as e:
    print(f"Database initialization warning: {e}")

def log_activity(action, details):
    uid = current_user.id if current_user.is_authenticated else None
    log = ActivityLog(user_id=uid, action=action, details=details)
    db.session.add(log)
    db.session.commit()

def deduct_item_inventory(menu_item, quantity, order_id=None, order_type='dine-in', user_id=None):
    """
    Automatically deducts inventory stock when a menu item is ordered.
    Auto-creates RawMaterial entry if not present.
    Emits real-time low-stock alert when remaining stock <= low_stock_threshold (default 5.0).
    """
    if not menu_item or quantity <= 0:
        return None
        
    try:
        clean_name = menu_item.name.strip()
        mat = RawMaterial.query.filter(db.func.lower(RawMaterial.name) == db.func.lower(clean_name)).first()
        
        if not mat:
            mat = RawMaterial(
                name=clean_name,
                unit='pcs',
                current_stock=20.0,
                low_stock_threshold=5.0
            )
            db.session.add(mat)
            db.session.commit()
            init_log = InventoryLog(
                raw_material_id=mat.id,
                type='add',
                quantity=20.0,
                reason='Auto-tracked Item Initialized',
                user_id=user_id
            )
            db.session.add(init_log)
            db.session.commit()
            
        # Deduct ordered quantity
        mat.current_stock = max(0.0, float(mat.current_stock) - float(quantity))
        
        reason_str = f"Order #{order_id} ({order_type})" if order_id else "Order Placed"
        log = InventoryLog(
            raw_material_id=mat.id,
            type='deduct',
            quantity=float(quantity),
            reason=reason_str,
            user_id=user_id
        )
        db.session.add(log)
        db.session.commit()
        
        # Broadcast real-time stock update to all connected admin / inventory views
        stock_status = 'out' if mat.current_stock <= 0 else ('low' if mat.current_stock <= mat.low_stock_threshold else 'optimal')
        socketio.emit('inventory_stock_updated', {
            'material_id': mat.id,
            'name': mat.name,
            'current_stock': int(mat.current_stock) if mat.current_stock.is_integer() else mat.current_stock,
            'threshold': mat.low_stock_threshold,
            'unit': mat.unit,
            'status': stock_status
        }, namespace='/')

        # Check Low Stock Warning (e.g. <= 5 items remaining)
        if mat.current_stock <= mat.low_stock_threshold:
            display_qty = int(mat.current_stock) if mat.current_stock.is_integer() else mat.current_stock
            alert_msg = f"⚠️ Low Stock Warning: Only {display_qty} {mat.unit} left for '{mat.name}'!"
            
            socketio.emit('inventory_alert', {
                'id': mat.id,
                'name': mat.name,
                'current_stock': mat.current_stock,
                'threshold': mat.low_stock_threshold,
                'unit': mat.unit,
                'message': alert_msg
            }, namespace='/')
            
            log_activity('low_stock_warning', alert_msg)
            try:
                print(f"[INVENTORY ALERT] {alert_msg}")
            except Exception:
                pass
            
        return mat
    except Exception as e:
        try:
            print(f"Error deducting inventory for {menu_item.name}: {e}")
        except Exception:
            pass
        db.session.rollback()
        return None

def restore_item_inventory(menu_item, quantity, order_id=None, user_id=None):
    """
    Restores inventory stock when an item is removed or cancelled from an order.
    """
    if not menu_item or quantity <= 0:
        return None
    try:
        clean_name = menu_item.name.strip()
        mat = RawMaterial.query.filter(db.func.lower(RawMaterial.name) == db.func.lower(clean_name)).first()
        if mat:
            mat.current_stock = float(mat.current_stock) + float(quantity)
            reason_str = f"Item restored from Order #{order_id}" if order_id else "Item returned"
            log = InventoryLog(
                raw_material_id=mat.id,
                type='add',
                quantity=float(quantity),
                reason=reason_str,
                user_id=user_id
            )
            db.session.add(log)
            db.session.commit()
            
            stock_status = 'out' if mat.current_stock <= 0 else ('low' if mat.current_stock <= mat.low_stock_threshold else 'optimal')
            socketio.emit('inventory_stock_updated', {
                'material_id': mat.id,
                'name': mat.name,
                'current_stock': int(mat.current_stock) if mat.current_stock.is_integer() else mat.current_stock,
                'threshold': mat.low_stock_threshold,
                'unit': mat.unit,
                'status': stock_status
            }, namespace='/')
            return mat
    except Exception as e:
        print(f"Error restoring inventory for {menu_item.name}: {e}")
        db.session.rollback()
        return None

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
        
    # Fire and forget immediately using fully detached subprocess
    import subprocess
    import sys
    subprocess.Popen(
        [sys.executable, "send_whatsapp.py", mobile, text, token, phone_id],
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )

import time
from flask import g

@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def add_security_headers(response):
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        print(f"[LIFECYCLE] {request.path} took {elapsed:.4f}s", flush=True)

    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Server'] = 'Protected'
    response.headers.pop('X-Powered-By', None)
    response.headers['X-Frame-Options'] = 'DENY'
    return response

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

def export_model_to_csv(model, records=None):
    si = io.StringIO()
    cw = csv.writer(si)
    columns = [column.name for column in model.__mapper__.columns]
    cw.writerow(columns)
    if records is None:
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
        
    subject = f"Soul Sip Cafe Database Backup - {datetime.now().strftime('%Y-%m-%d')}"
    to_email = os.environ.get('BACKUP_TO_EMAIL', 'soulsipcafe@gmail.com')
    body = "Please find attached the daily database backup (CSV format)."
    filename = f"soulsip_backup_{datetime.now().strftime('%Y%m%d')}.zip"
    
    # Read bytes for passing to background task
    zip_bytes = zip_buffer.read()
    zip_buffer.seek(0)
    
    # Fire and forget
    bg_queue.submit(_send_email_task, smtp_server, smtp_port, smtp_username, smtp_password, to_email, subject, body, zip_bytes, filename)
    return True

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

@app.route('/admin/download_today_data')
@login_required
@role_required('admin', 'manager')
def download_today_data():
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    
    today_orders = Order.query.filter(Order.created_at >= today_start).all()
    today_invoices = Invoice.query.filter(Invoice.created_at >= today_start).all()
    
    order_ids = [o.id for o in today_orders]
    today_order_items = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).all() if order_ids else []

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('today_orders.csv', export_model_to_csv(Order, today_orders))
        zf.writestr('today_invoices.csv', export_model_to_csv(Invoice, today_invoices))
        zf.writestr('today_order_items.csv', export_model_to_csv(OrderItem, today_order_items))
        
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"today_data_{today.strftime('%Y%m%d')}.zip"
    )

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
            download_name=f"soulsip_backup_{datetime.now().strftime('%Y%m%d')}.zip"
        )
    except Exception as e:
        flash(f"Failed to generate backup: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/')
def index():
    return redirect(url_for('menu'))

@app.route('/menu')
@limiter.limit("100 per minute")
def menu():
    table_name = request.args.get('table')
    
    # Optimize N+1 queries by fetching everything at once and grouping in memory
    categories = Category.query.order_by(Category.sort_order.asc()).all()
    all_items = MenuItem.query.filter_by(is_available=True).all()
    
    menu_items_by_cat = {cat.id: [] for cat in categories}
    for item in all_items:
        if item.category_id in menu_items_by_cat:
            menu_items_by_cat[item.category_id].append(item)
        
    table = None
    if table_name:
        table = Table.query.filter_by(name=table_name).first()
        
    tables = Table.query.filter_by(is_active=True).all()
    return render_template('customer/menu.html', categories=categories, menu_items_by_cat=menu_items_by_cat, table=table, table_name=table_name, tables=tables)

@app.route('/api/place_order', methods=['POST'])
@csrf.exempt
@limiter.limit("10 per minute")
def place_order():
    import time
    t_start = time.time()
    data = request.json
    table_name = data.get('table_name')
    customer_name = data.get('customer_name', '')
    customer_mobile = data.get('customer_mobile', '')
    covers = int(data.get('covers', 1))
    coupon_code = data.get('coupon_code', None)
    delivery_address = data.get('delivery_address', None)
    landmark = data.get('landmark', None)
    delivery_charge = float(data.get('delivery_charge', 0.0))
    delivery_staff_id = data.get('delivery_staff_id', None)
    items = data.get('items', [])
    order_type = data.get('order_type', 'dine-in') # dine-in, parcel, home-delivery
    
    table = None
    default_branch = Branch.query.first()
    default_branch_id = default_branch.id if default_branch else 1

    if table_name and str(table_name).strip():
        clean_tbl = str(table_name).strip()
        table = Table.query.filter(db.func.lower(Table.name) == db.func.lower(clean_tbl)).first()
        if not table:
            tbl_stripped = clean_tbl.lower().replace('table', '').strip()
            table = Table.query.filter(db.func.lower(Table.name) == tbl_stripped).first()
        
        if table:
            branch_id = table.branch_id or default_branch_id
        else:
            # Fallback to parcel if table name is invalid instead of crashing
            branch_id = default_branch_id
            order_type = 'parcel'
    else:
        branch_id = default_branch_id

    if not items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400

    # Prevent double-submission duplicate orders (10 second debounce per branch/table)
    from datetime import datetime
    
    if order_type == 'dine-in' and table:
        recent_order = Order.query.filter_by(table_id=table.id, type='dine-in').order_by(Order.created_at.desc()).first()
    else:
        recent_order = Order.query.filter_by(branch_id=branch_id, type='parcel').order_by(Order.created_at.desc()).first()
        
    if recent_order and recent_order.created_at and (datetime.utcnow() - recent_order.created_at).total_seconds() < 10:
        return jsonify({'success': True, 'order_id': recent_order.id, 'duplicate': True})
        
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
        covers=covers,
        coupon_code=coupon_code,
        delivery_address=delivery_address,
        landmark=landmark,
        delivery_charge=delivery_charge,
        delivery_staff_id=delivery_staff_id,
        created_by=current_user.id if current_user.is_authenticated else None
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
        
        # Deduct from inventory
        menu_item_obj = MenuItem.query.get(item['id'])
        if menu_item_obj:
            deduct_item_inventory(
                menu_item=menu_item_obj,
                quantity=item['quantity'],
                order_id=new_order.id,
                order_type=order_type,
                user_id=current_user.id if current_user.is_authenticated else None
            )
    
    db.session.commit()

    log_activity('order_placed', f"New {order_type} Order #{new_order.id} placed by {customer_name or 'Unknown'} for Rs.{total_amount}")
    
    import time
    t0 = time.time()

    if customer_mobile:
        print(f"[{time.time() - t_start:.4f}s] WhatsApp queue-submit se pehle", flush=True)
        send_whatsapp_message(customer_mobile, f"Hello {customer_name or ''}, your order #{new_order.id} has been confirmed. Thank you!")
        print(f"[{time.time() - t_start:.4f}s] WhatsApp queue-submit ke baad", flush=True)
    
    t_sock_start = time.time()
    socketio.emit('new_order', {'order_id': new_order.id}, namespace='/')
    t_sock_end = time.time()

    t1 = time.time()
    timing_data = {
        'total_time': t1 - t_start,
        'socket_time': t_sock_end - t_sock_start,
        'whatsapp_launch_time': t_sock_start - t0 # approx
    }
    print(f"[{time.time() - t_start:.4f}s] response return karne se pehle", flush=True)

    return jsonify({'success': True, 'order_id': new_order.id, 'timings': timing_data})

@app.route('/api/speed_test', methods=['GET', 'POST'])
@csrf.exempt
def speed_test():
    import time
    return jsonify({"success": True, "time": time.time()})

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
    covers = data.get('covers')
    customer_name = data.get('customer_name')
    customer_mobile = data.get('customer_mobile')
    
    order = Order.query.get_or_404(order_id)
    
    if order.status in ['completed', 'cancelled']:
        return jsonify({'error': 'Cannot edit a billed order'}), 400
        
    if covers is not None:
        try:
            order.covers = int(covers)
        except ValueError:
            pass
            
    if customer_name is not None:
        order.customer_name = customer_name
    if customer_mobile is not None:
        order.customer_mobile = customer_mobile
        if customer_mobile:
            profile = CustomerProfile.query.get(customer_mobile)
            if not profile:
                profile = CustomerProfile(mobile=customer_mobile, name=customer_name or '')
                db.session.add(profile)
            elif customer_name and (not profile.name or profile.name == ''):
                profile.name = customer_name
                
    if not items:
        # Cancel order
        order.status = 'cancelled'
        log_activity('order_edited', f"Order #{order_id} cancelled by removing all items by {current_user.name}")
        db.session.commit()
        socketio.emit('order_status_update', {'order_id': order.id, 'status': 'cancelled'}, namespace='/')
        return jsonify({'success': True})
        
    # KOT Logic: Calculate next KOT number if there are new additions
    current_kots = [i.kot_number for i in order.items if i.kot_number is not None]
    next_kot = max(current_kots) + 1 if current_kots else 1
    
    # Calculate total existing quantities per menu_item_id
    existing_items_by_menu_id = {}
    for item in order.items:
        if item.menu_item_id not in existing_items_by_menu_id:
            existing_items_by_menu_id[item.menu_item_id] = []
        existing_items_by_menu_id[item.menu_item_id].append(item)
        
    new_items_dict = {i['id']: i for i in items}
    
    changes = []
    has_added = False
    
    # Check for removed or quantity-decreased items
    for menu_id, existing_records in existing_items_by_menu_id.items():
        existing_total = sum(r.quantity for r in existing_records)
        new_qty = new_items_dict[menu_id]['quantity'] if menu_id in new_items_dict else 0
        
        if new_qty < existing_total:
            # Need to remove items. Remove from highest KOT first.
            diff = existing_total - new_qty
            changes.append(f"Reduced qty of {existing_records[0].menu_item.name} by {diff}")
            
            # Restore inventory for reduced quantity
            if existing_records and existing_records[0].menu_item:
                restore_item_inventory(existing_records[0].menu_item, diff, order_id=order.id, user_id=current_user.id if current_user.is_authenticated else None)
            
            # Sort descending by kot_number so we delete newest first
            existing_records.sort(key=lambda x: x.kot_number or 0, reverse=True)
            for r in existing_records:
                if diff <= 0:
                    break
                if r.quantity <= diff:
                    diff -= r.quantity
                    db.session.delete(r)
                else:
                    r.quantity -= diff
                    diff = 0
                    
    # Check for increased or brand new items
    for new_id, new_item_data in new_items_dict.items():
        new_qty = new_item_data['quantity']
        existing_records = existing_items_by_menu_id.get(new_id, [])
        existing_total = sum(r.quantity for r in existing_records)
        
        if new_qty > existing_total:
            diff = new_qty - existing_total
            menu_item = MenuItem.query.get(new_id)
            if menu_item:
                new_oi = OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    variant=menu_item.variant_name,
                    quantity=diff,
                    price_at_order=menu_item.price,
                    kot_number=next_kot,
                    added_at=datetime.utcnow()
                )
                db.session.add(new_oi)
                
                # Deduct newly added item quantity from inventory
                deduct_item_inventory(
                    menu_item=menu_item,
                    quantity=diff,
                    order_id=order.id,
                    order_type=order.type,
                    user_id=current_user.id if current_user.is_authenticated else None
                )
                
                changes.append(f"Added {menu_item.name} (x{diff}) [KOT-{next_kot}]")
                has_added = True
                
    if changes:
        if has_added and order.status == 'preparing':
            order.has_new_items = True
            
        log_activity('order_edited', f"Order #{order_id} edited by {current_user.name}: " + ", ".join(changes))
        db.session.commit()
        
        socketio.emit('order_status_update', {'order_id': order.id, 'status': order.status}, namespace='/')
        
    return jsonify({'success': True})

@app.route('/order/<int:order_id>')
@limiter.limit("20 per minute")
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    total_amount = sum(item.price_at_order * item.quantity for item in order.items)
    has_feedback = Feedback.query.filter_by(order_id=order_id).first() is not None
    return render_template('customer/status.html', order=order, total_amount=total_amount, has_feedback=has_feedback)

@app.route('/api/customer_order_status/<int:order_id>')
@limiter.limit("30 per minute")
def api_customer_order_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Not found'}), 404
    return jsonify({'success': True, 'status': order.status})

@app.route('/api/check_updates', methods=['GET'])
def check_updates():
    client_time = request.args.get('since', type=float, default=0.0)
    return jsonify({
        'has_updates': GLOBAL_LAST_UPDATE_TIMESTAMP > client_time,
        'server_time': GLOBAL_LAST_UPDATE_TIMESTAMP
    })

@app.route('/admin/inventory')
@login_required
def admin_inventory():
    if current_user.role not in ['admin', 'manager']:
        flash('Access Denied', 'danger')
        return redirect(url_for('admin_index'))
    materials = RawMaterial.query.all()
    logs = InventoryLog.query.order_by(InventoryLog.created_at.desc()).limit(100).all()
    return render_template('admin/inventory.html', materials=materials, logs=logs)

@app.route('/admin/inventory/material', methods=['POST'])
@login_required
def add_raw_material():
    if current_user.role not in ['admin', 'manager']:
        return "Unauthorized", 403
    name = request.form.get('name')
    unit = request.form.get('unit')
    initial_stock = float(request.form.get('initial_stock', 0.0))
    threshold = float(request.form.get('low_stock_threshold', 10.0))
    
    mat = RawMaterial(name=name, unit=unit, current_stock=initial_stock, low_stock_threshold=threshold)
    db.session.add(mat)
    db.session.commit()
    
    if initial_stock > 0:
        log = InventoryLog(raw_material_id=mat.id, type='add', quantity=initial_stock, reason='Initial Stock', user_id=current_user.id)
        db.session.add(log)
        db.session.commit()
        
    flash(f"Material {name} added successfully.", "success")
    return redirect(url_for('admin_inventory'))

@app.route('/admin/inventory/entry', methods=['POST'])
@login_required
def add_inventory_entry():
    if current_user.role not in ['admin', 'manager']:
        return "Unauthorized", 403
    
    raw_mat_id = request.form.get('material_id')
    if not raw_mat_id:
        flash("Please select a valid inventory item.", "danger")
        return redirect(url_for('admin_inventory'))
    try:
        material_id = int(raw_mat_id)
    except (ValueError, TypeError):
        flash("Invalid material ID.", "danger")
        return redirect(url_for('admin_inventory'))
    
    entry_type = request.form.get('type') # add, deduct
    try:
        quantity = float(request.form.get('quantity', 0.0))
    except (ValueError, TypeError):
        quantity = 0.0
    reason = request.form.get('reason')
    
    mat = RawMaterial.query.get(material_id)
    if not mat:
        flash("Invalid material.", "danger")
        return redirect(url_for('admin_inventory'))
        
    if entry_type == 'deduct':
        if quantity > mat.current_stock:
            quantity = mat.current_stock
            flash(f"Deduction capped at current stock ({mat.current_stock} {mat.unit}). Cannot deduct more than available.", "warning")
        else:
            flash(f"Deducted {quantity} {mat.unit} of {mat.name}.", "success")
        mat.current_stock -= quantity
    else:
        mat.current_stock += quantity
        flash(f"Added {quantity} {mat.unit} of {mat.name}.", "success")
        
    log = InventoryLog(raw_material_id=mat.id, type=entry_type, quantity=quantity, reason=reason, user_id=current_user.id)
    db.session.add(log)
    db.session.commit()
    
    # Broadcast alert if below threshold after manual deduction
    if mat.current_stock <= mat.low_stock_threshold:
        display_qty = int(mat.current_stock) if mat.current_stock.is_integer() else mat.current_stock
        socketio.emit('inventory_alert', {
            'id': mat.id,
            'name': mat.name,
            'current_stock': mat.current_stock,
            'threshold': mat.low_stock_threshold,
            'unit': mat.unit,
            'message': f"⚠️ Low Stock Warning: Only {display_qty} {mat.unit} left for '{mat.name}'!"
        }, namespace='/')
        
    return redirect(url_for('admin_inventory'))

@app.route('/admin/inventory/sync_menu', methods=['POST', 'GET'])
@login_required
def sync_menu_inventory():
    if current_user.role not in ['admin', 'manager']:
        flash('Unauthorized', 'danger')
        return redirect(url_for('admin_inventory'))
        
    menu_items = MenuItem.query.all()
    count_added = 0
    for mi in menu_items:
        clean_name = mi.name.strip()
        mat = RawMaterial.query.filter(db.func.lower(RawMaterial.name) == db.func.lower(clean_name)).first()
        if not mat:
            mat = RawMaterial(
                name=clean_name,
                unit='pcs',
                current_stock=25.0,
                low_stock_threshold=5.0
            )
            db.session.add(mat)
            count_added += 1
            
    db.session.commit()
    flash(f"Successfully synced menu items! {count_added} new items linked to inventory tracking.", "success")
    return redirect(url_for('admin_inventory'))

@app.route('/api/inventory/quick_update', methods=['POST'])
@login_required
def api_quick_inventory_update():
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    data = request.json or {}
    material_id = data.get('material_id')
    new_stock = data.get('current_stock')
    threshold = data.get('low_stock_threshold')
    
    mat = RawMaterial.query.get(material_id)
    if not mat:
        return jsonify({'success': False, 'message': 'Item not found'}), 404
        
    if new_stock is not None:
        try:
            val = float(new_stock)
            diff = val - mat.current_stock
            mat.current_stock = max(0.0, val)
            log = InventoryLog(
                raw_material_id=mat.id,
                type='adjustment',
                quantity=abs(diff),
                reason=f"Quick Stock Adjustment to {val}",
                user_id=current_user.id
            )
            db.session.add(log)
        except ValueError:
            pass
            
    if threshold is not None:
        try:
            mat.low_stock_threshold = max(0.0, float(threshold))
        except ValueError:
            pass
            
    db.session.commit()
    
    # Broadcast alert if stock <= threshold
    if mat.current_stock <= mat.low_stock_threshold:
        display_qty = int(mat.current_stock) if mat.current_stock.is_integer() else mat.current_stock
        socketio.emit('inventory_alert', {
            'id': mat.id,
            'name': mat.name,
            'current_stock': mat.current_stock,
            'threshold': mat.low_stock_threshold,
            'unit': mat.unit,
            'message': f"⚠️ Low Stock Warning: Only {display_qty} {mat.unit} left for '{mat.name}'!"
        }, namespace='/')
        
    return jsonify({
        'success': True,
        'current_stock': mat.current_stock,
        'low_stock_threshold': mat.low_stock_threshold,
        'is_low_stock': mat.current_stock <= mat.low_stock_threshold
    })

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
            
        session.permanent = True
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
    
    from sqlalchemy import func
    today_sales = db.session.query(func.sum(Invoice.total)).filter(Invoice.created_at >= utc_today_start).scalar() or 0.0
    
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
        'today_orders': today_orders,
        'live_orders': live_orders,
        'best_seller': best_seller
    }
    return render_template('admin/dashboard.html', stats=stats, active_page='dashboard')

@app.route('/admin/live_orders')
@login_required
@role_required('manager', 'waiter')
def live_orders():
    # Only show completed orders for today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    orders_new = [o for o in Order.query.options(joinedload(Order.items), joinedload(Order.table)).filter_by(status='new').order_by(Order.created_at.desc()).limit(50).all() if len(o.items) > 0]
    orders_preparing = [o for o in Order.query.options(joinedload(Order.items), joinedload(Order.table)).filter_by(status='preparing').order_by(Order.created_at.desc()).limit(50).all() if len(o.items) > 0]
    orders_served = [o for o in Order.query.options(joinedload(Order.items), joinedload(Order.table)).filter_by(status='served').order_by(Order.created_at.desc()).limit(50).all() if len(o.items) > 0]
    orders_completed = [o for o in Order.query.options(joinedload(Order.items), joinedload(Order.table)).filter(Order.status == 'completed', Order.created_at >= today_start).order_by(Order.created_at.desc()).limit(50).all() if len(o.items) > 0]
    waiter_calls = WaiterCall.query.filter_by(status='pending').order_by(WaiterCall.created_at.desc()).all()
    branches = Branch.query.all()
    
    return render_template('admin/live_orders.html', 
                           active_page='live_orders',
                           orders_new=orders_new,
                           orders_preparing=orders_preparing,
                           orders_served=orders_served,
                           orders_completed=orders_completed,
                           waiter_calls=waiter_calls,
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
        
    old_status = order.status
    order.status = new_status
    db.session.commit()
    log_activity('order_status_change', f"Order #{order_id} status changed to {new_status}.")
    
    if new_status == 'cancelled' and old_status != 'cancelled':
        for oi in order.items:
            if oi.menu_item:
                restore_item_inventory(oi.menu_item, oi.quantity, order_id=order.id, user_id=current_user.id if current_user.is_authenticated else None)
    
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
    tables = Table.query.order_by(Table.section, Table.name).all()
    
    # Calculate live totals and time
    from datetime import datetime
    now = datetime.utcnow()
    
    grouped_tables = {}
    for t in tables:
        t.active_total = 0
        t.elapsed_mins = 0
        
        if t.status == 'occupied':
            # Sum all non-completed/cancelled orders for this table
            active_orders = Order.query.options(joinedload(Order.items)).filter(Order.table_id == t.id, Order.status.notin_(['completed', 'cancelled', 'settled'])).all()
            for o in active_orders:
                for item in o.items:
                    t.active_total += item.price_at_order * item.quantity
                    
            if t.session_start_time:
                delta = now - t.session_start_time
                t.elapsed_mins = int(delta.total_seconds() // 60)
                
        if t.section not in grouped_tables:
            grouped_tables[t.section] = []
        grouped_tables[t.section].append(t)
        
    total = len(tables)
    vacant = sum(1 for t in tables if t.status == 'vacant')
    occupied = sum(1 for t in tables if t.status == 'occupied')
    cleaning = sum(1 for t in tables if t.status == 'cleaning')
    return render_template('admin/live_tables.html', 
                           active_page='live_tables',
                           grouped_tables=grouped_tables,
                           stats={'total': total, 'vacant': vacant, 'occupied': occupied, 'cleaning': cleaning})

@app.route('/api/update_table_status', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'cashier')
def update_table_status():
    data = request.json
    t = Table.query.get(data['table_id'])
    if t:
        t.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/api/take_table_order', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'cashier')
def take_table_order():
    data = request.json
    table_id = data.get('table_id')
    covers = int(data.get('covers', 1))
    t = Table.query.get(table_id)
    if not t:
        return jsonify({'success': False, 'message': 'Table not found'}), 404
        
    # Check for active order
    active_order = Order.query.filter_by(table_id=table_id, type='dine-in').filter(Order.status.in_(['new', 'preparing', 'served'])).first()
    
    if active_order:
        return jsonify({'success': True, 'redirect_url': url_for('edit_order', order_id=active_order.id)})
    
    # Create new shell order
    branch = Branch.query.first()
    new_order = Order(
        branch_id=branch.id,
        table_id=table_id,
        type='dine-in',
        status='new',
        covers=covers,
        created_by=current_user.id if current_user.is_authenticated else None
    )
    db.session.add(new_order)
    
    t.status = 'occupied'
    if not t.session_start_time:
        t.session_start_time = datetime.utcnow()
        
    db.session.commit()
    
    # Emit websockets so it reflects instantly
    socketio.emit('new_order', {'order_id': new_order.id}, namespace='/')
    socketio.emit('table_update', {}, namespace='/')
    
    return jsonify({'success': True, 'redirect_url': url_for('edit_order', order_id=new_order.id)})

@app.route('/admin/kot/print/<int:order_id>')
@login_required
@role_required('admin', 'manager', 'cashier')
def kot_print(order_id):
    order = Order.query.get_or_404(order_id)
    kot_number = request.args.get('kot', type=int)
    
    # Filter items to only show the ones belonging to the specific KOT
    if kot_number:
        items = [item for item in order.items if item.kot_number == kot_number]
    else:
        # Default to highest KOT number if none specified (i.e. the one just added)
        kot_number = max([item.kot_number for item in order.items]) if order.items else 1
        items = [item for item in order.items if item.kot_number == kot_number]
        
    return render_template('admin/kot_print.html', order=order, items=items, kot_number=kot_number)

@app.route('/admin/tables', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def manage_tables():
    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity', type=int)
        section = request.form.get('section', 'Main')
        if name and capacity:
            branch = Branch.query.first() # Use first branch
            if branch:
                new_table = Table(name=name, section=section, seats=capacity, status='vacant', branch_id=branch.id)
                db.session.add(new_table)
                db.session.commit()
                flash(f"Table {name} in {section} added successfully!")
        return redirect(url_for('manage_tables'))
        
    tables = Table.query.all()
    return render_template('admin/tables.html', tables=tables, active_page='tables')

@app.route('/admin/edit_table/<int:table_id>', methods=['POST'])
@login_required
def edit_table(table_id):
    table = Table.query.get_or_404(table_id)
    name = request.form.get('name')
    capacity = request.form.get('capacity', type=int)
    section = request.form.get('section')
    
    if name and capacity:
        table.name = name
        table.seats = capacity
        if section:
            table.section = section
        db.session.commit()
        flash(f"Table {name} updated successfully!")
    return redirect(url_for('manage_tables'))

@app.route('/admin/qr/<int:table_id>')
@app.route('/table/qr/<int:table_id>')
def get_qr(table_id):
    table = Table.query.get_or_404(table_id)
    url = f"{request.host_url}menu?table={table.name}"
    
    qr = qrcode.QRCode(version=1, box_size=12, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    from flask import send_file, make_response
    response = make_response(send_file(img_io, mimetype='image/png'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/table/qr_by_name/<string:table_name>')
def get_qr_by_name(table_name):
    table = Table.query.filter(db.func.lower(Table.name) == db.func.lower(table_name.strip())).first()
    if not table:
        url = f"{request.host_url}menu?table={table_name}"
    else:
        url = f"{request.host_url}menu?table={table.name}"
        
    qr = qrcode.QRCode(version=1, box_size=12, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    from flask import send_file, make_response
    response = make_response(send_file(img_io, mimetype='image/png'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/admin/new_parcel')
@login_required
@role_required('admin', 'manager', 'cashier')
def new_parcel():
    categories = Category.query.order_by(Category.sort_order).all()
    items = MenuItem.query.filter_by(is_available=True).all()
    return render_template('admin/new_parcel.html', categories=categories, items=items, active_page='new_parcel')

@app.route('/admin/new_dinein/<int:table_id>')
@login_required
@role_required('admin', 'manager', 'cashier', 'waiter')
def new_dinein(table_id):
    table = Table.query.get_or_404(table_id)
    # Check if table is occupied and redirect to edit order if so
    active_order = Order.query.filter_by(table_id=table_id, type='dine-in').filter(Order.status.in_(['new', 'preparing', 'served'])).first()
    if active_order:
        return redirect(url_for('edit_order', order_id=active_order.id))
        
    categories = Category.query.order_by(Category.sort_order).all()
    items = MenuItem.query.filter_by(is_available=True).all()
    return render_template('admin/new_dinein.html', table=table, categories=categories, items=items, active_page='live_tables')

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
    # Fetch all completed orders with eager loading to prevent massive N+1 slow queries
    completed_orders = Order.query.options(joinedload(Order.items), joinedload(Order.table)).filter_by(status='completed').order_by(Order.created_at.desc()).limit(200).all()
    
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
    custom_payment_method = data.get('custom_payment_method')
    payment_note = data.get('payment_note')
    customer_paid = float(data.get('customer_paid', 0.0))
    change_returned = float(data.get('change_returned', 0.0))
    tip_amount = float(data.get('tip_amount', 0.0))
    coupon_code = data.get('coupon_code', '').strip().upper()
    delivery_charge = float(data.get('delivery_charge', 0.0))
    redeemed_points = int(data.get('redeemed_points', 0))
    
    discount_type = data.get('discount_type')
    discount_value = float(data.get('discount_value', 0.0))
    discount_reason = data.get('discount_reason')
    
    orders = Order.query.filter(Order.id.in_(order_ids)).all()
    if not orders:
        return jsonify({'success': False, 'message': 'No orders found'})
        
    main_order = orders[0]
    
    if discount_type and discount_value > 0:
        main_order.discount_type = discount_type
        main_order.discount_value = discount_value
        main_order.discount_reason = discount_reason
    
    subtotal = 0.0
    for order in orders:
        for item in order.items:
            subtotal += (item.quantity * item.price_at_order)
            
    discount = 0.0
    used_coupon = None
    
    # Check for order level discount (Phase 22D)
    if main_order.discount_type == 'fixed':
        discount = main_order.discount_value
    elif main_order.discount_type == 'percent':
        discount = (subtotal * main_order.discount_value) / 100.0
    
    # Try the manual coupon code first, else fall back to the one attached to main_order
    if not coupon_code and main_order.coupon_code:
        coupon_code = main_order.coupon_code
        
    if coupon_code and not discount:
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
                used_coupon = c
                if c.discount_type == 'flat':
                    discount = c.discount_value
                elif c.discount_type == 'percent':
                    discount = (subtotal * c.discount_value) / 100.0
                
                # Increment usage
                c.usage_count += 1
                
    # Phase 23: Loyalty Points Redemption
    customer_profile = None
    if main_order.customer_mobile:
        customer_profile = CustomerProfile.query.get(main_order.customer_mobile)
        
    if redeemed_points > 0 and customer_profile:
        if redeemed_points > (customer_profile.loyalty_points or 0):
            return jsonify({'success': False, 'message': 'Not enough loyalty points'})
        customer_profile.loyalty_points -= redeemed_points
        discount += redeemed_points
                    
    if discount > subtotal: discount = subtotal
    
    taxable = subtotal - discount + delivery_charge
    gst_amount = taxable * 0.05
    exact_total = taxable + gst_amount
    rounded_total = round(exact_total)
    round_off = rounded_total - exact_total
    
    invoice = Invoice(
        order_id=main_order.id,
        invoice_number=f"INV-{main_order.id}-{datetime.utcnow().strftime('%H%M%S')}",
        subtotal=subtotal,
        discount=discount,
        gst_percent=5.0,
        gst_amount=gst_amount,
        round_off=round_off,
        delivery_charge=delivery_charge,
        total=rounded_total,
        payment_method=payment_method,
        custom_payment_method=custom_payment_method,
        payment_note=payment_note,
        customer_paid=customer_paid,
        change_returned=change_returned,
        tip_amount=tip_amount,
        coupon_code=used_coupon.code if used_coupon else None
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
            
    # Phase 23: Earn points on settled invoice total (post-discount, pre-tax)
    if customer_profile and taxable > 0:
        earned_points = int(taxable // 100)  # 1 point per Rs.100 (excluding GST)
        customer_profile.loyalty_points = (customer_profile.loyalty_points or 0) + earned_points
            
    # Record coupon on main order if it wasn't there
    if used_coupon and not main_order.coupon_code:
        main_order.coupon_code = used_coupon
            
    # Mark orders settled
    for order in orders:
        order.status = 'settled'
        
    db.session.commit()
    log_activity('bill_settled', f"Settled orders {order_ids} into Invoice #{invoice.invoice_number}. Total: Rs.{rounded_total}. Method: {payment_method}")
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
    invs = Invoice.query.order_by(Invoice.created_at.desc()).limit(500).all()
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
        
    all_refunds = Refund.query.order_by(Refund.created_at.desc()).limit(200).all()
    
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
        
        is_favorite = request.form.get('is_favorite') == 'on'
        food_type = request.form.get('food_type', 'veg')
        short_code = request.form.get('short_code', '')
        
        if name and cat_id and price:
            import json
            combo_json = json.dumps([i.strip() for i in combo_items.split(',') if i.strip()]) if is_combo else "[]"
            item = MenuItem(category_id=cat_id, name=name, name_hi=name_hi, name_gu=name_gu, price=price, description=desc, desc_hi=desc_hi, desc_gu=desc_gu, variant_name=variant, is_combo=is_combo, combo_items=combo_json, is_favorite=is_favorite, food_type=food_type, short_code=short_code)
            db.session.add(item)
            db.session.commit()
            socketio.emit('menu_update', namespace='/')
            log_activity('item_added', f"Menu item '{name}' added at Rs.{price}.")
            flash('Item added.')
        return redirect(url_for('items'))
        
    cats = Category.query.order_by(Category.sort_order.asc()).all()
    items = MenuItem.query.join(Category).options(joinedload(MenuItem.category)).order_by(Category.sort_order, MenuItem.name).all()
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

@app.route('/admin/items/edit/<int:item_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def edit_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    old_name = item.name
    
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
    is_favorite = request.form.get('is_favorite') == 'on'
    food_type = request.form.get('food_type', 'veg')
    short_code = request.form.get('short_code', '')
    
    if name and cat_id and price is not None:
        import json
        combo_json = json.dumps([i.strip() for i in combo_items.split(',') if i.strip()]) if is_combo else "[]"
        
        item.name = name.strip()
        item.name_hi = name_hi.strip() if name_hi else None
        item.name_gu = name_gu.strip() if name_gu else None
        item.category_id = cat_id
        item.price = price
        item.description = desc
        item.desc_hi = desc_hi
        item.desc_gu = desc_gu
        item.variant_name = variant
        item.is_combo = is_combo
        item.combo_items = combo_json
        item.is_favorite = is_favorite
        item.food_type = food_type
        item.short_code = short_code
        
        # If name changed, also update corresponding RawMaterial name
        if old_name != item.name:
            mat = RawMaterial.query.filter(db.func.lower(RawMaterial.name) == db.func.lower(old_name)).first()
            if mat:
                mat.name = item.name
                
        db.session.commit()
        socketio.emit('menu_update', namespace='/')
        log_activity('item_edited', f"Menu item '{item.name}' updated.")
        flash(f"Item '{item.name}' updated successfully.", 'success')
    else:
        flash("Invalid item data.", 'danger')
        
    return redirect(url_for('items'))

@app.route('/admin/items/delete/<int:item_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item_name = item.name
    try:
        OrderItem.query.filter_by(menu_item_id=item_id).delete()
        db.session.delete(item)
        db.session.commit()
        socketio.emit('menu_update', namespace='/')
        log_activity('item_deleted', f"Menu item '{item_name}' was deleted.")
        flash(f"Item '{item_name}' deleted successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting item: {str(e)}", 'error')
    return redirect(url_for('items'))

@app.route('/admin/categories/edit/<int:cat_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def edit_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    name = request.form.get('name')
    name_hi = request.form.get('name_hi')
    name_gu = request.form.get('name_gu')
    
    if name:
        cat.name = name.strip()
        cat.name_hi = name_hi.strip() if name_hi else None
        cat.name_gu = name_gu.strip() if name_gu else None
        db.session.commit()
        socketio.emit('menu_update', namespace='/')
        log_activity('category_edited', f"Category updated to '{cat.name}'.")
        flash(f"Category '{cat.name}' updated successfully.", 'success')
    else:
        flash("Category name is required.", 'danger')
        
    return redirect(url_for('categories'))

@app.route('/admin/categories/delete/<int:cat_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    cat_name = cat.name
    try:
        items = MenuItem.query.filter_by(category_id=cat_id).all()
        for itm in items:
            OrderItem.query.filter_by(menu_item_id=itm.id).delete()
            db.session.delete(itm)
        db.session.delete(cat)
        db.session.commit()
        socketio.emit('menu_update', namespace='/')
        log_activity('category_deleted', f"Category '{cat_name}' and all its items were deleted.")
        flash(f"Category '{cat_name}' deleted successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting category: {str(e)}", 'error')
    return redirect(url_for('categories'))

@app.route('/admin/menu/clear_all', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def clear_all_menu():
    try:
        OrderItem.query.delete()
        MenuItem.query.delete()
        Category.query.delete()
        db.session.commit()
        socketio.emit('menu_update', namespace='/')
        log_activity('menu_cleared', "All menu categories and items were deleted.")
        flash("All menu items and categories have been deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error clearing menu: {str(e)}", "error")
    return redirect(url_for('items'))

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

@app.route('/api/customer/autocomplete')
@login_required
def customer_autocomplete():
    q = request.args.get('q', '').strip()
    if len(q) < 4:
        return jsonify([])
    customers = CustomerProfile.query.filter(CustomerProfile.mobile.like(f"{q}%")).limit(10).all()
    return jsonify([{'mobile': c.mobile, 'name': c.name or ''} for c in customers])

@app.route('/api/customer/history')
@login_required
def customer_history():
    mobile = request.args.get('mobile', '').strip()
    if not mobile:
        return jsonify({'success': False, 'message': 'Mobile is required'}), 400
        
    customer = CustomerProfile.query.get(mobile)
    if not customer:
        return jsonify({'success': False, 'message': 'Customer not found in CRM'}), 404
        
    # Max ordered item
    max_item = db.session.query(MenuItem.name, func.sum(OrderItem.quantity).label('total_qty')) \
        .join(OrderItem, MenuItem.id == OrderItem.menu_item_id) \
        .join(Order, OrderItem.order_id == Order.id) \
        .filter(Order.customer_mobile == mobile, Order.status == 'completed') \
        .group_by(MenuItem.name) \
        .order_by(func.sum(OrderItem.quantity).desc()) \
        .first()
        
    max_ordered = f"{max_item[0]} ({max_item[1]} times)" if max_item else "N/A"
    
    # Average Bill & Coming Since
    orders = Order.query.filter(Order.customer_mobile == mobile, Order.status == 'completed').order_by(Order.created_at.asc()).all()
    
    visits_count = len(orders)
    coming_since = orders[0].created_at.strftime('%Y-%m-%d') if visits_count > 0 else "N/A"
    
    total_spend = sum(sum(i.price_at_order * i.quantity for i in o.items) for o in orders)
    avg_bill = total_spend / visits_count if visits_count > 0 else 0
    
    # Recent 25 orders
    recent_orders = []
    for o in sorted(orders, key=lambda x: x.created_at, reverse=True)[:25]:
        items_str = ", ".join([f"{i.quantity}x {i.menu_item.name}" for i in o.items])
        total = sum(i.price_at_order * i.quantity for i in o.items)
        recent_orders.append({
            'date': o.created_at.strftime('%Y-%m-%d %H:%M'),
            'items': items_str,
            'total': total
        })
        
    return jsonify({
        'success': True,
        'name': customer.name or 'Unknown',
        'mobile': customer.mobile,
        'max_ordered': max_ordered,
        'avg_bill': round(avg_bill, 2),
        'coming_since': coming_since,
        'visits': visits_count,
        'loyalty_points': customer.loyalty_points or 0,
        'recent_orders': recent_orders
    })

@app.route('/admin/day_end')
@login_required
@role_required('admin', 'manager')
def day_end():
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    
    today_invoices = Invoice.query.filter(Invoice.created_at >= today_start).all()
    total_sales = sum(i.total for i in today_invoices)
    total_tips = sum(i.tip_amount for i in today_invoices)
    cash_expected = sum(i.customer_paid - i.change_returned for i in today_invoices if i.payment_method == 'cash')
    
    today_orders = Order.query.filter(Order.created_at >= today_start).count()
    
    # Check if already closed today
    existing_close = DayEndRecord.query.filter_by(date=today).first()
    
    return render_template('admin/day_end.html', 
                           total_sales=total_sales, 
                           total_orders=today_orders,
                           total_tips=total_tips,
                           cash_expected=cash_expected,
                           existing_close=existing_close,
                           active_page='day_end')

@app.route('/api/day_end_close', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def day_end_close():
    today = datetime.utcnow().date()
    existing_close = DayEndRecord.query.filter_by(date=today).first()
    if existing_close:
        return jsonify({'success': False, 'message': 'Day is already closed for today.'})
        
    today_start = datetime(today.year, today.month, today.day)
    
    today_invoices = Invoice.query.filter(Invoice.created_at >= today_start).all()
    total_sales = sum(i.total for i in today_invoices)
    total_tips = sum(i.tip_amount for i in today_invoices)
    cash_expected = sum(i.customer_paid - i.change_returned for i in today_invoices if i.payment_method == 'cash')
    
    today_orders = Order.query.filter(Order.created_at >= today_start).count()
    
    record = DayEndRecord(
        date=today,
        closed_by=current_user.id,
        total_sales=total_sales,
        total_orders=today_orders,
        expected_cash=cash_expected,
        total_tips=total_tips
    )
    db.session.add(record)
    log_activity('day_end', f"{current_user.name} closed the day with sales ₹{total_sales}")
    db.session.commit()
    
    return jsonify({'success': True})

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

    elif rtype == 'employee_sales':
        q = db.session.query(
            Order.created_by,
            func.count(db.distinct(Order.id)).label('orders'),
            func.sum(Invoice.total).label('sales')
        ).join(Invoice, Invoice.order_id == Order.id).group_by(Order.created_by)
        
        q = apply_dates(q, Order.created_at)
        stats = q.all()
        
        users = {u.id: u.name for u in User.query.all()}
        
        return [{
            'Employee': users.get(row[0], 'Unknown/System') if row[0] else 'Unknown/System',
            'Orders Handled': row[1],
            'Total Sales': row[2] or 0
        } for row in stats]
        
    elif rtype == 'covers':
        q = Order.query
        q = apply_dates(q, Order.created_at)
        orders = q.all()
        
        daily = {}
        for o in orders:
            d = o.created_at.strftime('%Y-%m-%d')
            if d not in daily:
                daily[d] = {'orders': 0, 'covers': 0}
            daily[d]['orders'] += 1
            daily[d]['covers'] += (o.covers or 1)
            
        return [{
            'Date': k,
            'Total Orders': v['orders'],
            'Total Guests (Covers)': v['covers'],
            'Avg Guests/Order': round(v['covers'] / v['orders'], 2) if v['orders'] else 0
        } for k, v in sorted(daily.items(), reverse=True)]
        
    elif rtype == 'tips':
        q = Invoice.query.filter(Invoice.tip_amount > 0)
        q = apply_dates(q, Invoice.created_at)
        invs = q.all()
        
        daily = {}
        for i in invs:
            d = i.created_at.strftime('%Y-%m-%d')
            if d not in daily:
                daily[d] = {'count': 0, 'tips': 0}
            daily[d]['count'] += 1
            daily[d]['tips'] += i.tip_amount
            
        return [{
            'Date': k,
            'Invoices with Tips': v['count'],
            'Total Tips Collected': v['tips']
        } for k, v in sorted(daily.items(), reverse=True)]

    elif rtype == 'day_end_summary':
        q = DayEndRecord.query
        q = apply_dates(q, DayEndRecord.date)
        records = q.order_by(DayEndRecord.date.desc()).all()
        return [{
            'Date': r.date.strftime('%Y-%m-%d'),
            'Total Orders': r.total_orders,
            'Total Sales': r.total_sales,
            'Cash In Hand': r.expected_cash,
            'Tips': r.total_tips,
            'Closed At': r.closed_at.strftime('%I:%M %p') if r.closed_at else 'N/A'
        } for r in records]

    elif rtype == 'expense_summary':
        q = Expense.query
        q = apply_dates(q, Expense.created_at)
        exps = q.order_by(Expense.created_at.desc()).all()
        return [{
            'Date': e.created_at.strftime('%Y-%m-%d %H:%M'),
            'Category': e.category,
            'Description': e.description or 'N/A',
            'Payment Mode': e.payment_mode.upper(),
            'Recorded By': e.recorded_by,
            'Amount': e.amount
        } for e in exps]

    elif rtype == 'cashflow_summary':
        q = CashFlow.query
        q = apply_dates(q, CashFlow.created_at)
        cfs = q.order_by(CashFlow.created_at.desc()).all()
        return [{
            'Timestamp': c.created_at.strftime('%Y-%m-%d %H:%M'),
            'Type': c.flow_type.upper(),
            'Reason': c.reason,
            'Staff': c.recorded_by,
            'Amount': c.amount
        } for c in cfs]

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

@app.route('/admin/backup/export_all_csv')
@login_required
@role_required('admin')
def export_all_backup_csv():
    import io
    import csv
    import zipfile
    from flask import send_file
    
    # Create an in-memory zip file containing all CSV tables
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        # 1. Orders & Items CSV
        orders_output = io.StringIO()
        writer = csv.writer(orders_output)
        writer.writerow(['Order ID', 'Date', 'Type', 'Table/Customer', 'Status', 'Total Amount', 'Items Summary'])
        for o in Order.query.order_by(Order.created_at.desc()).limit(500).all():
            items_str = "; ".join([f"{i.quantity}x {i.menu_item.name if i.menu_item else 'Item'} (₹{i.price_at_order})" for i in o.items])
            total_val = sum(i.quantity * i.price_at_order for i in o.items)
            tbl = o.table.name if o.table else (o.customer_name or 'N/A')
            writer.writerow([o.id, o.created_at.strftime('%Y-%m-%d %H:%M:%S'), o.type, tbl, o.status, total_val, items_str])
        zip_file.writestr("1_orders_history.csv", orders_output.getvalue())
        
        # 2. Invoices CSV
        invoices_output = io.StringIO()
        writer = csv.writer(invoices_output)
        writer.writerow(['Invoice ID', 'Invoice No', 'Date', 'Order ID', 'Subtotal', 'Discount', 'GST Amount', 'Total', 'Payment Method', 'Customer Mobile', 'Tip'])
        for inv in Invoice.query.order_by(Invoice.created_at.desc()).limit(500).all():
            writer.writerow([inv.id, inv.invoice_number, inv.created_at.strftime('%Y-%m-%d %H:%M:%S'), inv.order_id, inv.subtotal, inv.discount, inv.gst_amount, inv.total, inv.payment_method, inv.order.customer_mobile if inv.order else '', inv.tip_amount])
        zip_file.writestr("2_invoices_sales.csv", invoices_output.getvalue())
        
        # 3. Day-End Close Reports CSV
        dayend_output = io.StringIO()
        writer = csv.writer(dayend_output)
        writer.writerow(['Date', 'Total Sales', 'Total Orders', 'Expected Cash', 'Total Tips', 'Closed At'])
        for d in DayEndRecord.query.order_by(DayEndRecord.date.desc()).all():
            writer.writerow([d.date.strftime('%Y-%m-%d'), d.total_sales, d.total_orders, d.expected_cash, d.total_tips, d.closed_at.strftime('%Y-%m-%d %H:%M:%S') if d.closed_at else ''])
        zip_file.writestr("3_day_end_reports.csv", dayend_output.getvalue())
        
        # 4. Expenses & Cashflow CSV
        expenses_output = io.StringIO()
        writer = csv.writer(expenses_output)
        writer.writerow(['ID', 'Date', 'Category', 'Description', 'Amount', 'Payment Mode', 'Recorded By'])
        for e in Expense.query.order_by(Expense.created_at.desc()).all():
            writer.writerow([e.id, e.created_at.strftime('%Y-%m-%d %H:%M:%S'), e.category, e.description, e.amount, e.payment_mode, e.recorded_by])
        zip_file.writestr("4_expenses.csv", expenses_output.getvalue())
        
        # 5. Inventory Stock & Logs CSV
        inventory_output = io.StringIO()
        writer = csv.writer(inventory_output)
        writer.writerow(['Item ID', 'Name', 'Current Stock', 'Unit', 'Low Stock Threshold'])
        for mat in RawMaterial.query.all():
            writer.writerow([mat.id, mat.name, mat.current_stock, mat.unit, mat.low_stock_threshold])
        zip_file.writestr("5_inventory_current_stock.csv", inventory_output.getvalue())
        
    zip_buffer.seek(0)
    filename = f"SoulSipCafe_FullBackup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/zip'
    )

@app.route('/admin/backup/reset_transactions', methods=['POST'])
@login_required
@role_required('admin')
def reset_transaction_data():
    from werkzeug.security import check_password_hash
    password = request.form.get('admin_password', '').strip()
    confirm_text = request.form.get('confirm_text', '').strip().upper()
    
    # Security validation
    if not check_password_hash(current_user.password_hash, password):
        flash("Incorrect Admin Password! Data reset aborted for security.", "danger")
        return redirect(url_for('reports'))
        
    if confirm_text != "RESET":
        flash("You must type 'RESET' in the confirmation box to proceed.", "warning")
        return redirect(url_for('reports'))
        
    try:
        # Clear transactional tables
        CreditLedger.query.delete()
        Refund.query.delete()
        Invoice.query.delete()
        OrderItem.query.delete()
        WaiterCall.query.delete()
        Feedback.query.delete()
        Order.query.delete()
        DayEndRecord.query.delete()
        Expense.query.delete()
        CashFlow.query.delete()
        InventoryLog.query.delete()
        ActivityLog.query.delete()
        
        # Reset all live table states to vacant
        for t in Table.query.all():
            t.status = 'vacant'
            t.session_start_time = None
            
        db.session.commit()
        
        # Log fresh start
        log_activity('system_reset', f"Admin {current_user.name} safely reset transaction data after CSV backup.")
        flash("✅ All orders, invoices, and transaction logs have been successfully reset! Menu, categories, tables, and staff accounts remain 100% intact.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error resetting database: {str(e)}", "danger")
        
    return redirect(url_for('reports'))

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
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(300).all()
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


@app.route('/api/order_details/<int:order_id>', methods=['GET'])
@login_required
def api_order_details(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'})
    items = []
    for item in order.items:
        items.append({
            'id': item.id,
            'menu_item_id': item.menu_item_id,
            'name': item.menu_item.name,
            'price': item.price_at_order,
            'quantity': item.quantity,
            'kot_number': item.kot_number
        })
    return jsonify({'success': True, 'items': items, 'total': sum(i['price'] * i['quantity'] for i in items)})

@app.route('/api/split_bill', methods=['POST'])
@login_required
def split_bill():
    data = request.json
    order_id = data.get('order_id')
    split_type = data.get('split_type', 'portion')
    split_ways = int(data.get('split_ways', 1))
    percentages = data.get('percentages', [])
    item_parts = data.get('item_parts', [])
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'})
        
    total_subtotal = sum((item.quantity * item.price_at_order) for item in order.items)
    
    discount = 0.0
    if order.coupon_code:
        c = Coupon.query.filter_by(code=order.coupon_code).first()
        if c and c.is_active:
            if c.discount_type == 'flat': discount = c.discount_value
            elif c.discount_type == 'percent': discount = (total_subtotal * c.discount_value) / 100.0
            if discount > total_subtotal: discount = total_subtotal
                
    total_taxable = total_subtotal - discount + order.delivery_charge
    total_gst = total_taxable * 0.05
    exact_grand_total = total_taxable + total_gst
    
    invoices = []
    
    if split_type == 'portion':
        if split_ways < 1: return jsonify({'success': False, 'message': 'Invalid split ways'})
        split_amount = round(exact_grand_total / split_ways)
        for i in range(split_ways):
            inv = Invoice(
                order_id=order.id,
                invoice_number=f"INV-{order.id}-P{i+1}-{datetime.utcnow().strftime('%H%M%S')}",
                subtotal=total_subtotal / split_ways,
                discount=discount / split_ways,
                gst_percent=5.0,
                gst_amount=total_gst / split_ways,
                round_off=0.0,
                delivery_charge=order.delivery_charge / split_ways,
                total=split_amount,
                payment_method='due',
                split_type='portion',
                split_metadata=json.dumps({"part": i+1, "total_parts": split_ways})
            )
            invoices.append(inv)
            
    elif split_type == 'percentage':
        if sum(percentages) != 100: return jsonify({'success': False, 'message': 'Percentages must add up to 100'})
        for i, pct in enumerate(percentages):
            ratio = pct / 100.0
            split_amount = round(exact_grand_total * ratio)
            inv = Invoice(
                order_id=order.id,
                invoice_number=f"INV-{order.id}-Pct{i+1}-{datetime.utcnow().strftime('%H%M%S')}",
                subtotal=total_subtotal * ratio,
                discount=discount * ratio,
                gst_percent=5.0,
                gst_amount=total_gst * ratio,
                round_off=0.0,
                delivery_charge=order.delivery_charge * ratio,
                total=split_amount,
                payment_method='due',
                split_type='percentage',
                split_metadata=json.dumps({"part": i+1, "percentage": pct})
            )
            invoices.append(inv)
            
    elif split_type == 'item':
        if not item_parts: return jsonify({'success': False, 'message': 'No items assigned'})
        for part in item_parts:
            part_num = part.get('part')
            items = part.get('items', [])
            part_subtotal = sum(i['price'] for i in items)
            
            # Pro-rate discount and delivery charge
            ratio = part_subtotal / total_subtotal if total_subtotal > 0 else 0
            part_discount = discount * ratio
            part_taxable = part_subtotal - part_discount + (order.delivery_charge * ratio)
            part_gst = part_taxable * 0.05
            part_exact = part_taxable + part_gst
            
            inv = Invoice(
                order_id=order.id,
                invoice_number=f"INV-{order.id}-Itm{part_num}-{datetime.utcnow().strftime('%H%M%S')}",
                subtotal=part_subtotal,
                discount=part_discount,
                gst_percent=5.0,
                gst_amount=part_gst,
                round_off=round(part_exact) - part_exact,
                delivery_charge=order.delivery_charge * ratio,
                total=round(part_exact),
                payment_method='due',
                split_type='item_wise',
                split_metadata=json.dumps({"part": part_num, "items": items})
            )
            invoices.append(inv)
            
    for inv in invoices:
        db.session.add(inv)
        
    if order.table_id:
        table = Table.query.get(order.table_id)
        if table:
            table.status = 'vacant'
            table.session_start_time = None
            
    order.status = 'completed'
    db.session.commit()
    
    socketio.emit('table_update', {}, namespace='/')
    
    try:
        invoices_created = [inv.id for inv in invoices]
        log_activity('bill_split', f"Split Order {order_id} into {len(invoices)} ways.")
        return jsonify({'success': True, 'invoice_ids': invoices_created})
    except Exception:
        return jsonify({'success': True})

@app.route('/api/call_waiter', methods=['POST'])
@csrf.exempt
@limiter.limit("20 per minute")
def call_waiter():
    data = request.json or {}
    table_name = data.get('table_name')
    order_id = data.get('order_id')
    
    print(f"DEBUG API: /api/call_waiter hit. Table: {table_name}, Order: {order_id}", flush=True)
    
    call = WaiterCall(table_name=table_name or "Unknown", order_id=order_id, status='pending')
    db.session.add(call)
    db.session.commit()
    
    # Safe fetch of time
    time_str = call.created_at.strftime('%I:%M %p') if call.created_at else "Just now"
    
    payload = {
        'id': call.id,
        'table_name': call.table_name,
        'order_id': order_id,
        'time': time_str
    }
    
    try:
        socketio.emit('new_waiter_call', payload)
        print(f"DEBUG API: new_waiter_call emitted: {payload}", flush=True)
    except Exception as e:
        print(f"DEBUG API: EMIT FAILED: {e}", flush=True)
    
    return jsonify({'success': True, 'call_id': call.id})

@app.route('/api/pending_waiter_calls', methods=['GET'])
@login_required
def get_pending_waiter_calls():
    calls = WaiterCall.query.filter_by(status='pending').order_by(WaiterCall.created_at.desc()).limit(20).all()
    return jsonify({
        'success': True,
        'calls': [{
            'id': c.id,
            'table_name': c.table_name,
            'order_id': c.order_id,
            'time': c.created_at.strftime('%I:%M %p') if c.created_at else "Just now"
        } for c in calls]
    })

@app.route('/api/resolve_call/<int:call_id>', methods=['POST'])
@login_required
def resolve_call(call_id):
    call = WaiterCall.query.get(call_id)
    if call:
        call.status = 'resolved'
        db.session.commit()
        try:
            socketio.emit('waiter_call_resolved', {'id': call_id, 'table_name': call.table_name})
        except Exception as e:
            print(f"Socket emit error on resolve_call: {e}")
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

# --- Soul Sip POS APIS & ROUTES ---

@app.route('/admin/settings/outlet')
@login_required
@role_required('admin')
def outlet_settings():
    all_settings = OutletSetting.query.all()
    settings_dict = {s.key: s.value for s in all_settings}
    return render_template('admin/outlet_settings.html', settings=settings_dict, active_page='outlet_settings')

@app.route('/api/settings/outlet/save', methods=['POST'])
@login_required
@role_required('admin')
def save_outlet_settings():
    data = request.json or {}
    for k, v in data.items():
        s = OutletSetting.query.filter_by(key=k).first()
        if not s:
            s = OutletSetting(key=k, value=str(v))
            db.session.add(s)
        else:
            s.value = str(v)
            s.updated_at = datetime.utcnow()
    log_activity('outlet_settings', f"{current_user.name} updated outlet POS configurations")
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/expenses')
@login_required
@role_required('admin', 'manager', 'cashier')
def admin_expenses():
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    expenses = Expense.query.order_by(Expense.created_at.desc()).all()
    today_expenses = [e for e in expenses if e.created_at >= today_start]
    total_today_expense = sum(e.amount for e in today_expenses)
    return render_template('admin/expenses.html', expenses=expenses, total_today_expense=total_today_expense, active_page='expenses')

@app.route('/admin/expenses/add', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'cashier')
def add_expense():
    category = request.form.get('category')
    amount = float(request.form.get('amount', 0))
    payment_mode = request.form.get('payment_mode', 'cash')
    note = request.form.get('description', '') or request.form.get('note', '')
    
    if amount > 0:
        exp = Expense(
            category=category,
            amount=amount,
            payment_mode=payment_mode,
            note=note,
            recorded_by=current_user.id
        )
        db.session.add(exp)
        log_activity('expense', f"Recorded expense ₹{amount} for {category} by {current_user.name}")
        db.session.commit()
        flash('Expense recorded successfully!')
    return redirect(url_for('admin_expenses'))

@app.route('/admin/cashflow')
@login_required
@role_required('admin', 'manager', 'cashier')
def admin_cashflow():
    cashflows = CashFlow.query.order_by(CashFlow.created_at.desc()).all()
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_cf = [c for c in cashflows if c.created_at >= today_start]
    
    opening_rec = next((c for c in today_cf if c.type in ['opening', 'opening_cash']), None)
    opening_balance = opening_rec.amount if opening_rec else 0.0
    
    total_cash_in = sum(c.amount for c in today_cf if c.type in ['in', 'cash_top_up'])
    total_cash_out = sum(c.amount for c in today_cf if c.type in ['out', 'withdrawal'])
    net_drawer_balance = opening_balance + total_cash_in - total_cash_out
    
    return render_template('admin/cashflow.html', 
                           cashflows=cashflows, 
                           opening_balance=opening_balance, 
                           total_cash_in=total_cash_in, 
                           total_cash_out=total_cash_out, 
                           net_drawer_balance=net_drawer_balance,
                           active_page='cashflow')

@app.route('/admin/cashflow/add', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'cashier')
def add_cashflow():
    flow_type = request.form.get('flow_type', 'in')
    amount = float(request.form.get('amount', 0))
    reason = request.form.get('reason', '')
    
    if amount > 0:
        cf = CashFlow(
            type=flow_type,
            amount=amount,
            reason=reason,
            recorded_by=current_user.id
        )
        db.session.add(cf)
        log_activity('cashflow', f"{current_user.name} recorded drawer {flow_type.upper()} ₹{amount} ({reason})")
        db.session.commit()
        flash('Cash flow transaction recorded successfully!')
    return redirect(url_for('admin_cashflow'))

@app.route('/api/search_bill')
@login_required
def api_search_bill():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'invoices': []})
    
    invs = Invoice.query.filter(
        (Invoice.invoice_number.ilike(f'%{q}%')) | 
        (Invoice.customer_name.ilike(f'%{q}%')) | 
        (Invoice.customer_phone.ilike(f'%{q}%'))
    ).order_by(Invoice.created_at.desc()).limit(15).all()
    
    result = [{
        'id': i.id,
        'invoice_number': i.invoice_number,
        'date': i.created_at.strftime('%d %b %Y, %I:%M %p'),
        'customer': i.customer_name or i.customer_phone or 'Walk-in',
        'payment_method': i.payment_method,
        'total': f"{i.total:.2f}"
    } for i in invs]
    return jsonify({'invoices': result})

@app.route('/api/search_kot')
@login_required
def api_search_kot():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'kots': []})
    
    # Search OrderItems with kot_number or Table name or Order id
    orders = Order.query.join(Table, Order.table_id == Table.id, isouter=True).filter(
        (Table.name.ilike(f'%{q}%')) | 
        (Order.id == int(q) if q.isdigit() else False)
    ).order_by(Order.created_at.desc()).limit(15).all()
    
    res = []
    for o in orders:
        kot_nums = set(item.kot_number for item in o.items if item.kot_number)
        if not kot_nums:
            kot_nums = {1}
        for kn in sorted(kot_nums, reverse=True):
            items_summary = ", ".join([f"{it.item.name} x{it.quantity}" for it in o.items if it.kot_number == kn])
            res.append({
                'order_id': o.id,
                'kot_number': kn,
                'table_name': o.table.name if o.table else 'Parcel',
                'status': o.status.upper(),
                'items_summary': items_summary or 'No items'
            })
    return jsonify({'kots': res})

@app.route('/api/all_items_status')
@login_required
def api_all_items_status():
    items = MenuItem.query.join(Category).order_by(Category.name, MenuItem.name).all()
    return jsonify({
        'items': [{
            'id': itm.id,
            'name': itm.name,
            'category': itm.category.name if itm.category else 'General',
            'price': itm.price,
            'is_available': itm.is_available
        } for itm in items]
    })

@app.route('/api/toggle_item', methods=['POST'])
@login_required
def api_toggle_item():
    data = request.json or {}
    item_id = data.get('item_id')
    is_available = data.get('is_available', True)
    itm = MenuItem.query.get(item_id)
    if itm:
        itm.is_available = bool(is_available)
        db.session.commit()
        log_activity('item_toggle', f"{current_user.name} toggled '{itm.name}' availability to {is_available}")
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Item not found'})

@app.route('/api/recent_invoices')
@login_required
def api_recent_invoices():
    invs = Invoice.query.order_by(Invoice.created_at.desc()).limit(8).all()
    now = datetime.utcnow()
    res = []
    for i in invs:
        diff_mins = int((now - i.created_at).total_seconds() / 60)
        time_ago = f"{diff_mins}m ago" if diff_mins < 60 else f"{diff_mins // 60}h ago"
        res.append({
            'id': i.id,
            'invoice_number': i.invoice_number,
            'total': f"{i.total:.2f}",
            'payment_method': i.payment_method,
            'time_ago': time_ago
        })
    return jsonify({'invoices': res})

@app.route('/api/hold_orders')
@login_required
def api_hold_orders():
    orders = Order.query.filter(Order.status.in_(['new', 'preparing', 'served'])).order_by(Order.created_at.desc()).all()
    res = []
    for o in orders:
        total = sum(it.price_at_order * it.quantity for it in o.items)
        res.append({
            'id': o.id,
            'table_name': o.table.name if o.table else (o.customer_name or 'Parcel'),
            'status': o.status,
            'items_count': sum(it.quantity for it in o.items),
            'total_amount': f"{total:.2f}"
        })
    return jsonify({'orders': res})



# --- SOCKET EVENTS ---


from sqlalchemy import text

def auto_migrate():
    with app.app_context():
        # Ensure new tables are created robustly
        try:
            db.create_all()
        except Exception as e:
            print(f"Error creating tables in auto_migrate: {e}")
        
        # Phase 22C
        try:
            db.session.execute(text('ALTER TABLE order_items ADD COLUMN kot_number INTEGER DEFAULT 1'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE order_items ADD COLUMN added_at DATETIME'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        # Phase 22D Order Fields
        try:
            db.session.execute(text('ALTER TABLE orders ADD COLUMN discount_reason VARCHAR(200)'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE orders ADD COLUMN discount_type VARCHAR(20)'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE orders ADD COLUMN discount_value FLOAT DEFAULT 0.0'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        # Phase 22D Invoice Fields
        try:
            db.session.execute(text('ALTER TABLE invoices ADD COLUMN custom_payment_method VARCHAR(50)'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE invoices ADD COLUMN payment_note TEXT'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE invoices ADD COLUMN customer_paid FLOAT DEFAULT 0.0'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE invoices ADD COLUMN change_returned FLOAT DEFAULT 0.0'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE invoices ADD COLUMN tip_amount FLOAT DEFAULT 0.0'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE invoices ADD COLUMN split_type VARCHAR(20)'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            db.session.execute(text('ALTER TABLE invoices ADD COLUMN split_metadata TEXT'))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Phase 22F Order Fields
        try:
            db.session.execute(text('ALTER TABLE orders ADD COLUMN created_by INTEGER'))
            db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            db.session.execute(text('ALTER TABLE orders ADD COLUMN covers INTEGER DEFAULT 1'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        # Phase 23
        try:
            db.session.execute(text('ALTER TABLE customers ADD COLUMN loyalty_points INTEGER DEFAULT 0'))
            db.session.commit()
        except Exception:
            db.session.rollback()

# Run migration on startup safely
try:
    auto_migrate()
except Exception as e:
    print(f"Auto-migrate warning: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
@app.route('/admin/force_reset_now_magic')
def force_reset_now_magic():
    try:
        CreditLedger.query.delete()
        Refund.query.delete()
        Invoice.query.delete()
        OrderItem.query.delete()
        WaiterCall.query.delete()
        Feedback.query.delete()
        Order.query.delete()
        DayEndRecord.query.delete()
        Expense.query.delete()
        CashFlow.query.delete()
        InventoryLog.query.delete()
        ActivityLog.query.delete()
        for t in Table.query.all():
            t.status = 'vacant'
            t.session_start_time = None
        db.session.commit()
        return "<h2>SUCCESS! All orders and bills have been deleted. The system is now fresh and ZERO!</h2><br><a href='/admin/dashboard'>Click here to go back to Dashboard</a>"
    except Exception as e:
        db.session.rollback()
        return f"ERROR: {str(e)}"



@app.route('/admin/magic_add_menu')
def magic_add_menu():
    try:
        OrderItem.query.delete()
        MenuItem.query.delete()
        Category.query.delete()
        
        menu_dict = {'Hot Beverages / Coffee': [('Black Coffee', 39, 'Bold espresso, pure & unsweetened', False), ('Regular Coffee', 49, 'Classic milk coffee, smooth & comforting', False), ('Filter Coffee', 59, 'South-Indian brew, frothy & aromatic', False), ('Hot Chocolate', 99, 'Velvety dark cocoa, served piping hot', False)], 'Cold Beverages': [('Fresh Lime Soda', 49, 'Sweet, salted or mixed - your choice', False), ('Cold Coffee (Classic)', 69, 'Chilled, frothy coffee over ice', False), ('Cold Coffee w/ Ice Cream', 79, 'Vanilla scoop & chocolate drizzle', False), ('Lemon Iced Tea', 79, 'Black tea, fresh lemon, served chilled', False)], 'Mocktails': [('Jaljeera Fizz', 89, 'Spiced jaljeera, soda & crunchy boondi', False), ('Virgin Mojito', 99, 'Muddled mint, lime & soda', False), ('Blue Lagoon', 109, 'Blue curacao flavour, tangy lemonade', False), ('Watermelon Mint Cooler', 109, 'Watermelon, lime & crushed ice', False), ('Green Apple Fizz', 109, 'Crisp green apple, citrus splash', False), ('Strawberry Basil Smash', 119, 'Strawberry & torn basil, topped with soda', False), ('Blueberry Basil Lemonade', 119, 'Blueberry-basil twist on classic lemonade', False), ('Passion Fruit Mojito', 129, 'Passion fruit, mint, lime & soda', True)], 'Regular Shakes': [('Vanilla Shake', 89, 'Classic vanilla bean & chilled milk', False), ('Strawberry Shake', 99, 'Ripe strawberry, smooth & creamy', False), ('Mango Shake (Seasonal)', 99, 'Silky mango blended with cool milk', False), ('Butterscotch Shake', 109, 'Creamy butterscotch-caramel crunch', False), ('Kesar Pista Shake', 119, 'Saffron & crushed pistachio, chilled milk', False)], 'Thick / Loaded Shakes': [('Oreo Thick Shake', 139, 'Crushed Oreo & creamy ice cream', False), ('KitKat Thick Shake', 149, 'Loaded with crispy wafer chunks', False), ('Belgian Chocolate Thick Shake', 159, 'Rich, dark Belgian chocolate fix', False), ('Ferrero Rocher Thick Shake', 169, 'Golden Ferrero Rocher & roasted hazelnut', False), ('Nutella Brownie Thick Shake', 179, 'Fudgy brownie meets creamy Nutella', False), ('Lotus Biscoff Thick Shake', 179, 'Crushed Biscoff & spiced cookie butter', True)], 'Fries': [('Salted Normal Fries', 79, 'Golden fries, classic sea salt', False), ('Peri Peri Fries', 99, 'Bold, spicy peri peri seasoning', False), ('Salted Cheese Fries', 119, 'Smothered in warm melted cheese', False), ('Peri Peri Cheese Fries', 129, 'Peri peri spice meets melted cheese', False), ('Nachos French Fries', 149, 'Nacho chips, cheese & jalapenos', False), ('Special Loaded Long Fries', 279, 'Extra-long fries, cheese, sauces & jalapenos', True)], 'Garlic Bread & Toast': [('Salted Masala Toast', 99, 'Garlic butter & Indian spice blend', False), ('Normal Cheese Garlic Bread', 109, 'Garlic butter baked under melted cheese', False), ('Roasted Onion Pepper Toast', 109, 'Caramelized onion & roasted bell pepper', False), ('Grilled Chilli Toast', 109, 'Garlic toast, spicy green chillies & cheese', False), ('Cheese Corn Toast', 119, 'Sweet corn & melted cheese', False), ('Schezwan Toast', 119, 'Fiery schezwan sauce & melted cheese', False), ('5-Flavour Garlic Toast', 179, 'Five seasoned toppings, one showstopper platter', True)], 'Momos': [('Veg Steam Momos', 99, 'Steamed, stuffed with fresh vegetables', False), ('Fry Veg Momos', 109, 'Golden fried, spiced veg filling', False), ('Veg Paneer Steam Momos', 109, 'Steamed, soft paneer & veggie mix', False), ('Cheese Steam Momos', 119, 'Steamed, gooey melted cheese filling', False), ('Fry Paneer / Cheese Momos', 119, 'Deep-fried, paneer or cheese filling', False), ('Tandoori Peri Peri Momos', 179, 'Smoky tandoori marinade, peri peri kick', False)], 'Frankie / Wraps': [('Aloo Tikki Frankie', 59, 'Spiced potato patty, tangy chutneys', False), ('Veg Cheese Frankie', 69, 'Melted cheese & fresh veggies in a soft warm roll', False), ('Tandoori Veg Frankie', 89, 'Smoky tandoori veggies in a soft roll', False), ('Cheese Corn Frankie', 89, 'Sweet corn & gooey melted cheese', False), ('Paneer Frankie', 99, 'Spiced paneer, crunchy veggies & sauces', False), ('Mexican Veg Frankie', 119, 'Mixed veg, salsa & Mexican spice', False), ('Paneer Tikka Frankie', 119, 'Tandoori paneer tikka, onions & chutney', False), ('Schezwan Paneer Frankie', 119, 'Paneer tossed in bold schezwan sauce', False), ('Double Cheese Paneer Frankie', 129, 'Spiced paneer, double melted cheese blast', True)], 'Sandwich': [('Bread Butter Sandwich', 49, 'Soft bread, creamy butter', False), ('Cheese Jam Sandwich', 69, 'Sweet jam meets rich cheese', False), ('Cheese Bread Butter', 69, 'Buttered bread with a cheese slice', False), ('Veg Sandwich', 79, 'Fresh veggies, creamy cheese layers', False), ('Mini Cheese Grill', 89, 'Toasted pockets, melted cheese & herbs', False), ('Veg Cheese Sandwich', 99, 'Sliced vegetables, smooth melted cheese', False), ('Cheese Aloo Sandwich', 99, 'Spiced potato filling & melted cheese', False), ('Open Cheese Toast', 99, 'Golden toast loaded with gooey cheese', False), ('Veg Cheese Grill Sandwich', 109, 'Grilled, crunchy veg & melted cheese', False), ('Garlic Cheese Open Toast', 109, 'Garlic butter, bubbly melted cheese', False), ('Corn Cheese Open Toast', 109, 'Sweet corn & melted cheese, open-faced', False), ('Cheesy Spicy Open Toast', 119, 'Melted cheese, spicy chillies & herbs', False), ('Bombay Grill Sandwich', 129, 'Street-style, spiced potato & green chutney', False), ('Tandoori Paneer Sandwich', 139, 'Smoky tandoori paneer, grilled', False), ('Special Protein Sandwich', 149, 'Protein-rich grilled filling, fitness-focused & fresh', False), ('Matka Sandwich (Veg / Paneer)', 149, 'Chefs special served in an earthen pot', True)], 'Burger': [('Standard Veg Burger', 79, 'Potato-veggie patty, lettuce & mayo', False), ('Crispy Crunch Burger', 95, 'Extra-crunchy patty, tangy signature sauce', False), ('Red Hot Spicy Burger', 99, 'Fiery patty, hot chilli mayo', False), ('Farm House Burger', 109, 'Garden-fresh veggies, tomato & cheese', False), ('Tandoori Paneer Burger', 139, 'Smoky paneer steak, mint mayo', False), ('Original Double Tikki Burger', 149, 'Two crispy patties, melted cheese & sauces', True)], 'Pizza': [('Peri Peri Paneer Pizza', 109, 'Spiced peri peri paneer, onions & melted cheese', False), ('Margherita Pizza', 129, 'Tomato sauce, mozzarella & fresh basil', False), ('Cheese Corn Pizza', 139, 'Sweet corn, thick layer of cheese', False), ('Spicy Tangy Pizza', 169, 'Zesty sauces, fiery jalapenos', False), ('Farm House Pizza', 209, 'Onion, capsicum, tomato & mushroom', False), ('Tandoori Paneer Pizza', 279, 'Tandoori paneer, capsicum, onion & cheese', True)], 'Mayo Pav': [('Solid Masti Pav', 59, 'Buttery pav, seasoned veggie patty', False), ('Cream Onion Pav', 69, 'Caramelized onion, velvety sour cream', False), ('Veggie House Pav', 79, 'Garden veggies, house-special spread', False), ('Hot Spicy Pav', 79, 'Fiery red chilli spice & jalapenos', False), ('Tandoori Paneer Pav', 99, 'Smoky tandoori paneer, crisp onions', False)], 'Pasta': [('Red Sauce Pasta', 139, 'Tangy tomato-basil, garlic & herbs', False), ('White Sauce Pasta', 159, 'Silky garlic-cream sauce, melted cheese', False), ('Pink Sauce Pasta', 169, 'Tomato marinara meets creamy white sauce', False)], 'Maggi': [('Masala Maggi', 69, 'Classic noodles, savoury Indian spice', False), ('Veggie Maggi', 89, 'Sauteed garden vegetables', False), ('Cheesy Sauce Maggi', 99, 'Rich, velvety cheese sauce', False), ('Schezwan Cheese Maggi', 109, 'Fiery schezwan spice, melted cheese', False), ('Vegetable Cheese Maggi', 109, 'Sauteed mixed vegetables in creamy cheese sauce', False), ('Extra Cheese Maggie', 129, 'Extra velvety cheese sauce, ultra creamy', False)], 'Desserts': [('Ice Cream (2 Scoops)', 79, 'Classic flavour, cold & creamy', False), ('Chocolate Lava Cake', 79, 'Molten cocoa centre, oozes with every bite', False), ('Brownie (Plain)', 99, 'Rich, dense, fudgy chocolate brownie', False), ('Brownie with Ice Cream', 129, 'Warm brownie, chilled vanilla scoop', False), ('Belgian Waffle (Choco / Nutella)', 149, 'Golden-crisp, deep pockets & airy centre', False), ('Waffle with Ice Cream', 179, 'Crispy waffle, chocolate/Nutella & ice cream', True)]}
        
        idx = 0
        for cat_name, items in menu_dict.items():
            cat = Category(name=cat_name, sort_order=idx)
            db.session.add(cat)
            db.session.flush()
            
            for itm in items:
                mi = MenuItem(category_id=cat.id, name=itm[0], price=itm[1], description=itm[2], is_favorite=itm[3], food_type='veg')
                db.session.add(mi)
            idx += 1
            
        db.session.commit()
        return "SUCCESS! Old menu deleted, new menu added!"
    except Exception as e:
        db.session.rollback()
        return f"ERROR: {str(e)}"


@app.route('/admin/magic_update_admin')
def magic_update_admin():
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(role='admin').first()
    if admin:
        admin.mobile = '8141005168'
        admin.password = generate_password_hash('soulsip@2000')
        db.session.commit()
        return 'Admin updated successfully! New mobile: 8141005168'
    return 'Admin not found.'
