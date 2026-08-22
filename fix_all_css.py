import os

for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'inset: 0;' in content:
                content = content.replace('inset: 0;', 'top: 0; left: 0; right: 0; bottom: 0; width: 100%; height: 100%;')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed {filepath}")
