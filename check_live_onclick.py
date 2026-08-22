from bs4 import BeautifulSoup
import re
with open('live_items.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
buttons = soup.find_all('button', title='Edit Item')
if buttons:
    print("Found button!")
    print(buttons[0].get('onclick'))
else:
    print("No buttons found using BS4. Using regex...")
    match = re.search(r'onclick="(openEditItemModal[^"]+)"', html)
    if match:
        print(match.group(1))
    else:
        print("Not found with regex either.")
