from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    tables = db.relationship('Table', backref='branch', lazy=True)
    users = db.relationship('User', backref='branch', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_hi = db.Column(db.String(150))
    name_gu = db.Column(db.String(150))
    sort_order = db.Column(db.Integer, default=0)
    items = db.relationship('MenuItem', backref='category', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    name_hi = db.Column(db.String(150))
    name_gu = db.Column(db.String(150))
    description = db.Column(db.Text)
    desc_hi = db.Column(db.Text)
    desc_gu = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    variant_name = db.Column(db.String(50)) # e.g. Small/Medium/Large
    is_combo = db.Column(db.Boolean, default=False)
    combo_items = db.Column(db.Text) # JSON string of what's included
    is_available = db.Column(db.Boolean, default=True)

    def get_combo_items(self):
        if self.is_combo and self.combo_items:
            return json.loads(self.combo_items)
        return []

class Table(db.Model):
    __tablename__ = 'tables'
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    name = db.Column(db.String(20), nullable=False) # e.g. "T-1"
    seats = db.Column(db.Integer, default=2)
    qr_code = db.Column(db.String(255)) # Path or base64
    status = db.Column(db.String(20), default='vacant') # vacant, occupied, needs_cleaning
    session_start_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True) # null for parcel
    type = db.Column(db.String(20), nullable=False) # dine-in/parcel/home-delivery
    status = db.Column(db.String(20), default='new') # new/preparing/served/completed/cancelled
    customer_name = db.Column(db.String(100))
    customer_mobile = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    table = db.relationship('Table')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    variant = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_order = db.Column(db.Float, nullable=False)
    
    menu_item = db.relationship('MenuItem')

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False) # Or session_id if multiple orders per table
    invoice_number = db.Column(db.String(50), unique=True, nullable=False) # e.g. MB-00020
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    gst_percent = db.Column(db.Float, default=5.0)
    gst_amount = db.Column(db.Float, default=0.0)
    round_off = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20)) # cash/upi/card/settled/credit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order = db.relationship('Order')

class CreditLedger(db.Model):
    __tablename__ = 'credit_ledger'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_mobile = db.Column(db.String(15), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='outstanding') # outstanding/paid
    
    invoice = db.relationship('Invoice')

class Refund(db.Model):
    __tablename__ = 'refunds'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(100))
    returned_via = db.Column(db.String(20)) # cash/upi/card
    note = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # pending/completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    invoice = db.relationship('Invoice')

class User(db.Model, UserMixin):
    __tablename__ = 'staff_users'
    id = db.Column(db.Integer, primary_key=True)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin/manager/waiter/chef/cashier
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True) # Null for superadmin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
