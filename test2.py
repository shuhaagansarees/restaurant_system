import json
data = {"name": "Chef's special"}
# emulate tojson|forceescape
s = json.dumps(data).replace('"', '&#34;').replace("'", "&#39;")
print(f'<button data-item="{s}" id="btn"></button>')
