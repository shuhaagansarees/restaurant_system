from jinja2 import Template

t = Template('''<button data-item="{{ data | tojson | forceescape }}"></button>''')

print("Single Quote:", t.render(data={'name': "Chef's special"}))
print("Double Quote:", t.render(data={'name': 'Chef"s special'}))
