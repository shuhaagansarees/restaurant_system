import os

files_to_fix = [
    'templates/admin/categories.html',
    'templates/admin/reports.html',
    'templates/admin/live_tables.html'
]

for file_path in files_to_fix:
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    modal_start = html.find('<!-- Edit Category Modal -->')
    if modal_start == -1:
        modal_start = html.find('<div id="editCatModal"')
    if modal_start == -1:
        modal_start = html.find('<div class="modal" id="resetModal"')
    if modal_start == -1:
        modal_start = html.find('<div id="liveTableQRModal"')
        
    if modal_start != -1:
        modal_end = html.find('{% endblock %}', modal_start)
        if modal_end != -1:
            modal_content = html[modal_start:modal_end]
            html = html[:modal_start] + html[modal_end:]
            
            # append to modals block or create one
            if '{% block modals %}' in html:
                pass # Already appended manually? No, we didn't.
            else:
                modals_block = f"\n{{% block modals %}}\n{modal_content}\n{{% endblock %}}\n"
                html = html + modals_block
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Moved modal in {file_path}")
