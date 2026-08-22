from jinja2 import Template
import json

template_str = """
data-item="{{ {
  'id': item.id,
  'name': item.name,
  'price': item.price
}|tojson|forceescape }}"
"""
t = Template(template_str)

class Item:
    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price

print(t.render(item=Item(1, "Chef's special", 69.0)))
