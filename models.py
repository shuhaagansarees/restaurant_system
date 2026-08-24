from datetime import datetime, timedelta

def ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

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
    license_key = db.Column(db.String(255), nullable=True) # Per-client watermark
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
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    name_hi = db.Column(db.String(150))
    name_gu = db.Column(db.String(150))
    description = db.Column(db.Text)
    desc_hi = db.Column(db.Text)
    desc_gu = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)
    food_type = db.Column(db.String(20), default="veg") # veg, non-veg, egg
    short_code = db.Column(db.String(10), nullable=True)
    variant_name = db.Column(db.String(50)) # e.g. Small/Medium/Large
    is_combo = db.Column(db.Boolean, default=False)
    combo_items = db.Column(db.Text)
    image_url = db.Column(db.String(255), nullable=True) # JSON string of what's included
    is_available = db.Column(db.Boolean, default=True, index=True)

    def get_combo_items(self):
        if self.is_combo and self.combo_items:
            return json.loads(self.combo_items)
        return []

class Table(db.Model):
    __tablename__ = 'tables'
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False, index=True)
    name = db.Column(db.String(20), nullable=False) # e.g. "T-1"
    section = db.Column(db.String(50), default="Main") # Ground Floor, Party Hall, etc.
    seats = db.Column(db.Integer, default=2)
    qr_code = db.Column(db.String(255)) # Path or base64
    status = db.Column(db.String(20), default='vacant') # vacant, occupied, needs_cleaning
    session_start_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False, index=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True, index=True) # null for parcel
    type = db.Column(db.String(20), nullable=False, index=True) # dine-in/parcel/home-delivery
    status = db.Column(db.String(20), default='new', index=True) # new/preparing/served/completed/cancelled
    customer_name = db.Column(db.String(100))
    customer_mobile = db.Column(db.String(15))
    coupon_code = db.Column(db.String(50), nullable=True)
    delivery_address = db.Column(db.Text, nullable=True)
    landmark = db.Column(db.String(100), nullable=True)
    delivery_charge = db.Column(db.Float, default=0.0)
    discount_reason = db.Column(db.String(200), nullable=True)
    discount_type = db.Column(db.String(20), nullable=True) # 'percent', 'fixed'
    discount_value = db.Column(db.Float, default=0.0)
    delivery_staff_id = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now, index=True)
    has_new_items = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True, index=True)
    covers = db.Column(db.Integer, default=1)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    table = db.relationship('Table')
    creator = db.relationship('User', foreign_keys=[created_by])
    delivery_staff = db.relationship('User', foreign_keys=[delivery_staff_id])

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False, index=True)
    variant = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_order = db.Column(db.Float, nullable=False)
    kot_number = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=ist_now)
    
    menu_item = db.relationship('MenuItem')

class DayEndRecord(db.Model):
    __tablename__ = 'day_end_records'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=lambda: ist_now().date(), index=True)
    closed_by = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=False, index=True)
    closed_at = db.Column(db.DateTime, default=ist_now)
    total_sales = db.Column(db.Float, default=0.0)
    total_orders = db.Column(db.Integer, default=0)
    expected_cash = db.Column(db.Float, default=0.0)
    total_tips = db.Column(db.Float, default=0.0)

    closer = db.relationship('User', foreign_keys=[closed_by])

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True) # Or session_id if multiple orders per table
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True) # e.g. MB-00020
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    gst_percent = db.Column(db.Float, default=5.0)
    gst_amount = db.Column(db.Float, default=0.0)
    round_off = db.Column(db.Float, default=0.0)
    delivery_charge = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20)) # cash/upi/card/settled/credit/part/other
    custom_payment_method = db.Column(db.String(50), nullable=True) # e.g. Google Pay
    payment_note = db.Column(db.Text, nullable=True)
    customer_paid = db.Column(db.Float, default=0.0)
    change_returned = db.Column(db.Float, default=0.0)
    tip_amount = db.Column(db.Float, default=0.0)
    split_type = db.Column(db.String(20), nullable=True) # portion/percentage/item_wise
    split_metadata = db.Column(db.Text, nullable=True) # JSON string
    coupon_code = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now, index=True)
    
    order = db.relationship('Order')

class CreditLedger(db.Model):
    __tablename__ = 'credit_ledger'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_mobile = db.Column(db.String(15), nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='outstanding') # outstanding/paid
    
    invoice = db.relationship('Invoice')

class Refund(db.Model):
    __tablename__ = 'refunds'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(100))
    returned_via = db.Column(db.String(20)) # cash/upi/card
    note = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # pending/completed
    created_at = db.Column(db.DateTime, default=ist_now)
    
    invoice = db.relationship('Invoice')

class User(db.Model, UserMixin):
    __tablename__ = 'staff_users'
    id = db.Column(db.Integer, primary_key=True)
    mobile = db.Column(db.String(15), unique=True, nullable=False, index=True)
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
    user_id = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=ist_now)
    
    user = db.relationship('User')

class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(10), nullable=False) # flat, percent
    discount_value = db.Column(db.Float, nullable=False)
    min_order_amount = db.Column(db.Float, default=0.0)
    expiry_date = db.Column(db.DateTime, nullable=True)
    max_usage_limit = db.Column(db.Integer, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

class CustomerProfile(db.Model):
    __tablename__ = 'customers'
    mobile = db.Column(db.String(15), primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    loyalty_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=ist_now)

class WaiterCall(db.Model):
    __tablename__ = 'waiter_calls'
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(20), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    status = db.Column(db.String(20), default='pending') # pending/resolved
    created_at = db.Column(db.DateTime, default=ist_now)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 to 5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now)
    
    order = db.relationship('Order')

class RawMaterial(db.Model):
    __tablename__ = 'raw_materials'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False) # kg, litre, pieces, packet
    current_stock = db.Column(db.Float, default=0.0)
    low_stock_threshold = db.Column(db.Float, default=5.0)
    created_at = db.Column(db.DateTime, default=ist_now)
    
    logs = db.relationship('InventoryLog', backref='raw_material', lazy=True, cascade="all, delete-orphan")

class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'
    id = db.Column(db.Integer, primary_key=True)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_materials.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False) # add, deduct, adjustment
    quantity = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now)
    
    user = db.relationship('User')

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False) # e.g. Grocery, Vegetables, Maintenance, Salary, Petty Cash
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.String(20), default='cash') # cash, upi, card, bank
    note = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now)
    
    recorder = db.relationship('User', foreign_keys=[recorded_by])

class CashFlow(db.Model):
    __tablename__ = 'cash_flow'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(30), nullable=False) # opening_cash, cash_top_up, withdrawal, closing_cash
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('staff_users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now)
    
    recorder = db.relationship('User', foreign_keys=[recorded_by])

class OutletSetting(db.Model):
    __tablename__ = 'outlet_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False) # JSON or string
    description = db.Column(db.String(255), nullable=True)
