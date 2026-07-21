import io
import zipfile
import os
from app import app, db
from models import User

os.environ['BACKUP_SECRET_KEY'] = 'test-key'
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SERVER_NAME'] = 'localhost.localdomain'

c = app.test_client()

with app.app_context():
    # Login as admin to test the download route
    admin_user = User.query.filter_by(mobile='7999620244').first()
    if not admin_user:
        print("Test user not found, running auto-seed might be needed if DB is empty.")
    
    with c.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True

    # 1. Test /admin/download_backup
    print("\n--- Testing /admin/download_backup ---")
    res = c.get('/admin/download_backup')
    print("Status Code:", res.status_code)
    print("Content-Type:", res.headers.get('Content-Type'))
    print("File Size (bytes):", len(res.data))
    
    if res.status_code == 200 and len(res.data) > 0:
        # Extract and verify zip contents
        zip_data = io.BytesIO(res.data)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            file_list = zf.namelist()
            print("\nFiles found in ZIP:")
            for f in file_list:
                print(f" - {f}")
            
            print(f"\nTotal files: {len(file_list)} / 8")
            
            if 'categories.csv' in file_list:
                print("\n--- Contents of categories.csv ---")
                csv_content = zf.read('categories.csv').decode('utf-8')
                print(csv_content.strip())
            else:
                print("\ncategories.csv missing!")
