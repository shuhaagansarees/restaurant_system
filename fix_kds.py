import os

with open('templates/admin/kds.html', 'r', encoding='utf-8') as f:
    html = f.read()

# We need to replace the entire <script> block content except checkEmpty and markServed
# Actually, it's easier to just regex or string replace.
script_start = html.find('let lastUpdateCheck = Date.now() / 1000;')
script_end = html.find('function checkEmpty()')

if script_start != -1 and script_end != -1:
    new_script = """
    const socket = io({transports: ['websocket', 'polling']});
    
    function playBeeps() {
        if (!document.getElementById('sound-toggle').checked) return;
        const audio = document.getElementById('notif-sound');
        let playCount = 0;
        function playBeep() {
            if (playCount < 3) {
                audio.play().catch(e => console.log(e));
            }
        }
        audio.onended = () => {
            playCount++;
            setTimeout(playBeep, 500); // 0.5s gap
        };
        playBeep(); // Start the first beep
    }
    
    async function reloadKDS() {
        try {
            // Add a cache-busting parameter to ensure we fetch fresh HTML
            const htmlResp = await fetch(window.location.pathname + '?_t=' + new Date().getTime());
            const htmlText = await htmlResp.text();
            const doc = new DOMParser().parseFromString(htmlText, 'text/html');
            document.querySelector('.kds-grid').innerHTML = doc.querySelector('.kds-grid').innerHTML;
        } catch(e) { window.location.reload(); }
    }

    socket.on('new_order', function(data) {
        playBeeps();
        reloadKDS();
    });
    
    socket.on('order_status_update', function(data) {
        reloadKDS();
    });
    
    socket.on('table_update', function(data) {
        reloadKDS();
    });
    
    """
    html = html[:script_start] + new_script + html[script_end:]
    
    # Also add the socket.io script tag before our script
    if 'socket.io.js' not in html:
        html = html.replace('<script>', '<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>\n    <script>')

    with open('templates/admin/kds.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Replaced polling with Socket.IO in kds.html")
else:
    print("Could not find script block to replace")
