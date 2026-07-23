import re

with open('templates/admin/live_orders.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add audio element for waiter chime
audio_html = """<!-- Audio for notification -->
<audio id="notif-sound" src="/static/audio/beep.wav" preload="auto"></audio>
<audio id="waiter-sound" src="/static/audio/chime.wav" preload="auto"></audio>"""
content = content.replace('<!-- Audio for notification -->\n<audio id="notif-sound" src="/static/audio/beep.wav" preload="auto"></audio>', audio_html)

# 2. Update new_waiter_call listener to use waiter-sound
content = content.replace("const audio = document.getElementById('notif-sound');\n        if (audio) {", "const audio = document.getElementById('waiter-sound');\n        if (audio) {")

with open('templates/admin/live_orders.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Sound patched in live_orders.html")
