import os
for root, _, files in os.walk('templates/admin'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            orig = content
            content = content.replace('style="display: none;', 'style="')
            
            if orig != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Removed inline display: none from {filepath}")
