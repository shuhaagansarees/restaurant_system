import requests
import time
url = 'https://restaurant-system-z5m7.onrender.com/admin/magic_update_admin'
print("Waiting for deploy...")
time.sleep(90)
for _ in range(10):
    try:
        r = requests.get(url)
        print(r.text)
        if 'updated successfully' in r.text or 'Admin not found' in r.text:
            break
    except Exception as e:
        pass
    time.sleep(20)
