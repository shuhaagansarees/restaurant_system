import re

# 1. Update base.html to add global toast
with open('templates/customer/base.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

toast_html = """
    <!-- Global Toast Container -->
    <div id="toast-container" style="position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; display: flex; flex-direction: column; gap: 10px; width: 90%; max-width: 400px; pointer-events: none;"></div>
    <style>
        @keyframes fadein { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeout { from { opacity: 1; } to { opacity: 0; } }
        .toast-msg { background: #1f2937; color: white; padding: 12px 20px; border-radius: 8px; font-size: 0.95rem; font-weight: 500; box-shadow: 0 4px 12px rgba(0,0,0,0.15); animation: fadein 0.3s, fadeout 0.3s 2.7s; text-align: center; pointer-events: auto; }
    </style>
    <script>
        function showToast(message) {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = 'toast-msg';
            toast.innerText = message;
            container.appendChild(toast);
            setTimeout(() => { toast.remove(); }, 3000);
        }
    </script>
"""
if "toast-container" not in base_html:
    base_html = base_html.replace('<div class="app-container">', toast_html + '\n    <div class="app-container">')
    with open('templates/customer/base.html', 'w', encoding='utf-8') as f:
        f.write(base_html)

# 2. Update status.html
with open('templates/customer/status.html', 'r', encoding='utf-8') as f:
    status_html = f.read()

old_button = """<button onclick="callWaiter('{{ order.table.name }}', {{ order.id }})" class="btn-primary" style="background: var(--brand-orange); border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%;">
            🛎️ Call Waiter
        </button>"""
new_button = """<button onclick="callWaiter('{{ order.table.name }}', {{ order.id }})" class="btn-primary" style="background-color: var(--danger); width: 100%; display: block; text-align: center; text-decoration: none; font-size: 1.1rem; padding: 14px;">
            🛎️ Call Waiter
        </button>"""
status_html = status_html.replace(old_button, new_button)
status_html = status_html.replace("alert('Waiter has been called!');", "showToast('🛎️ Waiter has been called to your table!');")

with open('templates/customer/status.html', 'w', encoding='utf-8') as f:
    f.write(status_html)

# 3. Update menu.html
with open('templates/customer/menu.html', 'r', encoding='utf-8') as f:
    menu_html = f.read()

menu_html = menu_html.replace("alert('Waiter has been called to your table!');", "showToast('🛎️ Waiter has been called to your table!');")
# We also update the button in menu.html to look nice if needed, but the user complained about status.html. Let's make sure menu.html button uses var(--danger).
menu_html = menu_html.replace("background: #ef4444;", "background-color: var(--danger);")

with open('templates/customer/menu.html', 'w', encoding='utf-8') as f:
    f.write(menu_html)

print("UI Patched successfully")
