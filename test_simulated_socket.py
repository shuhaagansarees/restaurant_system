import threading
import time
import requests
import socketio
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Global list to collect admin socket events
admin_events = []

def run_server():
    from app import app, socketio as sio
    # Disable flask output to avoid clutter
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    sio.run(app, host='127.0.0.1', port=5005, use_reloader=False, log_output=False)

def test_waiter_call():
    print("--- Starting Socket E2E Test ---")
    
    # 1. Start server in a background thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)  # Wait for server to boot
    
    # 2. Start admin socket client
    sio_admin = socketio.Client()
    
    @sio_admin.on('new_waiter_call')
    def on_new_waiter_call(data):
        admin_events.append(f"Admin received new_waiter_call: {data}")
        
    try:
        sio_admin.connect('http://127.0.0.1:5005', namespaces=['/'])
        print("Admin connected to socket.")
    except Exception as e:
        print(f"Failed to connect admin socket: {e}")
        return
        
    time.sleep(1)
    
    # 3. Simulate customer clicking "Call Waiter"
    print("Customer sending Waiter Call via API...")
    res = requests.post('http://127.0.0.1:5005/api/call_waiter', json={
        'table_name': 'T-E2E',
        'order_id': 999
    })
    print(f"Customer API response: {res.json()}")
    
    # Wait to receive socket event
    time.sleep(2)
    sio_admin.disconnect()
    
    print("\n--- Event Verification ---")
    if admin_events:
        for ev in admin_events:
            print(f"[SUCCESS] {ev}")
    else:
        print("[FAIL] Admin did not receive new_waiter_call event!")
        
if __name__ == '__main__':
    test_waiter_call()
