import re

with open('templates/admin/inventory.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the topbar_actions block
html = re.sub(r'{% block topbar_actions %}.*?{% endblock %}', '', html, flags=re.DOTALL)

# Insert the buttons at the beginning of the content block
buttons_html = '''
<div style="display: flex; gap: 10px; margin-bottom: 20px; justify-content: flex-end;">
    <a href="{{ url_for('sync_menu_inventory') }}" class="btn-secondary" style="display: inline-flex; align-items: center; gap: 6px; text-decoration: none; padding: 8px 14px; font-size: 0.85rem; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 6px; color: #1e293b;">
        <i class="fa-solid fa-arrows-rotate"></i> Sync All Menu Items
    </a>
    <button class="btn-primary" onclick="openModal('newMaterialModal')" style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; font-size: 0.85rem; font-weight: 600; border-radius: 6px;">
        <i class="fa-solid fa-plus"></i> New Material
    </button>
</div>
'''

html = html.replace('{% block content %}', '{% block content %}\n' + buttons_html)

with open('templates/admin/inventory.html', 'w', encoding='utf-8') as f:
    f.write(html)
