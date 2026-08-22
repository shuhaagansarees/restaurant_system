from jinja2 import Template
try:
    t = Template("{{ item_name|replace(\"'\", \"\\\\'\") }}")
    print(t.render(item_name="Chef's special"))
except Exception as e:
    print("Error:", e)
