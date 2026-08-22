from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))
t = env.get_template('admin/items.html')

class Cat:
    id = 1
    name = 'Cat1'
class Item:
    id = 1
    name = 'Cold Coffee (Classic)'
    name_hi = ''
    name_gu = ''
    category_id = 1
    price = 69.0
    variant_name = ''
    food_type = 'veg'
    short_code = ''
    is_favorite = False
    is_combo = False
    description = ''
    desc_hi = ''
    desc_gu = ''
    category = Cat()

def csrf_token():
    return 'token'

try:
    rendered = t.render(items=[Item()], categories=[Cat()], active_page='items', csrf_token=csrf_token)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(rendered, 'html.parser')
    edit_btn = soup.find('button', title='Edit Item')
    print("Edit button HTML:")
    print(edit_btn)
    
    data_item = edit_btn['data-item']
    print("\ndata-item content:")
    print(data_item)
    
    import json
    parsed = json.loads(data_item)
    print("\nParsed JSON:")
    print(parsed)
except Exception as e:
    print("Error:", e)
