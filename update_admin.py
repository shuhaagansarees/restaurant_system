import requests
import time

url = 'https://restaurant-system-z5m7.onrender.com/admin/magic_update_admin'
print("Waiting for deploy to finish...")
time.sleep(60)

for _ in range(10):
    try:
        r = requests.get(url)
        print("Status:", r.status_code, "Response:", r.text)
        if r.status_code == 200 and 'updated successfully' in r.text:
            print("Successfully updated admin credentials!")
            break
    except Exception as e:
        print("Error:", e)
    time.sleep(20)
