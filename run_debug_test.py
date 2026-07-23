import threading
import time
import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Run server in background
def start_server():
    from app import app, socketio as sio
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    print("Starting Flask-SocketIO test server on port 5006...")
    sio.run(app, host='127.0.0.1', port=5006, use_reloader=False, log_output=False)

t = threading.Thread(target=start_server, daemon=True)
t.start()

time.sleep(3) # Wait for server to start

print("Hitting /api/call_waiter...")
try:
    res = requests.post('http://127.0.0.1:5006/api/call_waiter', json={
        'table_name': 'T-RAW-TEST',
        'order_id': 1
    })
    print("API Response Code:", res.status_code)
    print("API JSON Response:", res.json())
except Exception as e:
    print("Error hitting API:", e)

print("Test complete.")
