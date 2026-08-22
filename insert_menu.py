import os
import requests

from app import app, db, Category, MenuItem, OrderItem, log_activity

with app.app_context():
    # ... Wait, if I do this locally, it modifies the LOCAL database.
    pass
