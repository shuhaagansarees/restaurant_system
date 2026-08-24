import re

with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add to Add Modal
add_image_field = '''<div class="form-group">
                <label>Image URL (Optional)</label>
                <input type="text" name="image_url" placeholder="/static/img/menu/xyz.jpg or https://...">
            </div>'''
html = html.replace('<div class="form-group" style="margin-top: 15px;">\n                <label style="display: flex; align-items: center; gap: 8px; font-weight: 500;">\n                    <input type="checkbox" name="is_combo"', add_image_field + '\n            <div class="form-group" style="margin-top: 15px;">\n                <label style="display: flex; align-items: center; gap: 8px; font-weight: 500;">\n                    <input type="checkbox" name="is_combo"')

# Add to Edit Modal
edit_image_field = '''<div class="form-group">
                <label>Image URL (Optional)</label>
                <input type="text" name="image_url" id="edit_image_url" placeholder="/static/img/menu/xyz.jpg or https://..." style="width:100%; padding:10px; border:1px solid var(--border-color); border-radius:6px;">
            </div>'''
html = html.replace('<div class="form-group" style="margin-top: 15px;">\n                <label style="display: flex; align-items: center; gap: 8px; font-weight: 500;">\n                    <input type="checkbox" name="is_combo" id="edit_is_combo"', edit_image_field + '\n            <div class="form-group" style="margin-top: 15px;">\n                <label style="display: flex; align-items: center; gap: 8px; font-weight: 500;">\n                    <input type="checkbox" name="is_combo" id="edit_is_combo"')

# Update editJS
html = html.replace("document.getElementById('edit_is_combo').checked = item.is_combo === 'True' || item.is_combo === true;", "document.getElementById('edit_is_combo').checked = item.is_combo === 'True' || item.is_combo === true;\n        document.getElementById('edit_image_url').value = item.image_url || '';")
html = html.replace("is_combo: this.dataset.is_combo,", "is_combo: this.dataset.is_combo, image_url: this.dataset.image_url,")
html = html.replace('data-is_combo="{{ item.is_combo }}"', 'data-is_combo="{{ item.is_combo }}" data-image_url="{{ item.image_url or \'\' }}"')


with open('templates/admin/items.html', 'w', encoding='utf-8') as f:
    f.write(html)
