with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
# We want to replace the broken confirm dialog with a working one
broken_form = r'''<form method="POST" action="/admin/items/delete/{{ item.id }}" onsubmit="return confirm('Are you sure you want to delete \'{{\s*item.name.*?}}\'\?');" style="display: inline-block; margin: 0;">'''

def fix_form(match):
    return '''<form method="POST" action="/admin/items/delete/{{ item.id }}" onsubmit="return confirm('Are you sure you want to delete \\'{{ item.name|replace(\\"'\\", \\"\\\\\\'\\") }}\\ '?');" style="display: inline-block; margin: 0;">'''

# Actually, the simplest way is to pass item.name as JSON to the onsubmit handler!
# <form onsubmit='return confirm("Are you sure you want to delete " + {{ item.name|tojson }} + "?");'>

new_form = """<form method="POST" action="/admin/items/delete/{{ item.id }}" data-name="{{ item.name|tojson|forceescape }}" onsubmit="return confirm('Are you sure you want to delete ' + JSON.parse(this.dataset.name) + '?');" style="display: inline-block; margin: 0;">"""

html = re.sub(r'<form method="POST" action="/admin/items/delete/{{ item\.id }}" onsubmit="return confirm.*?</form>', new_form + '\n                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>\n                                <button type="submit" style="background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 0.85rem;" title="Delete Item">\n                                    🗑️ Delete\n                                </button>\n                            </form>', html, flags=re.DOTALL)

with open('templates/admin/items.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Fixed items.html')
