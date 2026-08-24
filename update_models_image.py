import re

with open('models.py', 'r', encoding='utf-8') as f:
    models_code = f.read()

if 'image_url = db.Column' not in models_code:
    models_code = models_code.replace("combo_items = db.Column(db.Text)", "combo_items = db.Column(db.Text)\n    image_url = db.Column(db.String(255), nullable=True)")
    
    with open('models.py', 'w', encoding='utf-8') as f:
        f.write(models_code)
        print("Added image_url to models.py")
