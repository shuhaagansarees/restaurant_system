import os

for root, _, files in os.walk('templates/admin'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            orig = content
            # Fix open
            content = content.replace("modal.style.display = 'flex'", "modal.classList.add('active'); modal.style.display = ''")
            content = content.replace("document.getElementById('editCatModal').style.display = 'flex'", "document.getElementById('editCatModal').classList.add('active')")
            content = content.replace("document.getElementById('liveTableQRModal').style.display = 'flex'", "document.getElementById('liveTableQRModal').classList.add('active')")
            
            # Fix close
            content = content.replace("modal.style.display = 'none'", "modal.classList.remove('active')")
            content = content.replace("document.getElementById('editCatModal').style.display = 'none'", "document.getElementById('editCatModal').classList.remove('active')")
            content = content.replace("document.getElementById('liveTableQRModal').style.display = 'none'", "document.getElementById('liveTableQRModal').classList.remove('active')")
            
            if orig != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed {filepath}")
