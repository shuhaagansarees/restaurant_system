from jinja2 import Template
import html

t = Template('''
<button data-item="{{ data | tojson | forceescape }}"></button>
''')
res = t.render(data={'name': "Chef's special", "description": "This is \"very\" good \n and tasty! 'Really'."})
print("HTML:", res)

# Simulate what the browser does to read dataset
import re
match = re.search(r'data-item="(.*)"', res)
if match:
    attr = match.group(1)
    dom_string = html.unescape(attr)
    print("DOM STRING:", dom_string)
    import json
    try:
        parsed = json.loads(dom_string)
        print("PARSED:", parsed)
    except Exception as e:
        print("PARSE ERROR:", e)
