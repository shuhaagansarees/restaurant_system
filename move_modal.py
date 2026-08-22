import re

with open('templates/admin/base.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add block modals just before </body>
html = html.replace('</body>', '    {% block modals %}{% endblock %}\n</body>')

with open('templates/admin/base.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated base.html")

with open('templates/admin/items.html', 'r', encoding='utf-8') as f:
    items_html = f.read()

# Find the Edit Item Modal
modal_start = items_html.find('<!-- Edit Item Modal -->')
if modal_start != -1:
    modal_end = items_html.find('{% endblock %}', modal_start)
    if modal_end != -1:
        modal_content = items_html[modal_start:modal_end]
        
        # Remove modal from current block
        items_html = items_html[:modal_start] + items_html[modal_end:]
        
        # Add it to block modals
        modals_block = f"\n{{% block modals %}}\n{modal_content}\n{{% endblock %}}\n"
        items_html = items_html + modals_block
        
        with open('templates/admin/items.html', 'w', encoding='utf-8') as f:
            f.write(items_html)
        print("Moved modal in items.html")
