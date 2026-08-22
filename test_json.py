import json

str_from_dom = '{"name": "5\\" Pizza"}'
try:
    parsed = json.loads(str_from_dom)
    print("Success:", parsed)
except Exception as e:
    print("Error:", e)
