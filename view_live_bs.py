from bs4 import BeautifulSoup
with open('live_items.html', 'r', encoding='utf-8') as f:
    html = f.read()
soup = BeautifulSoup(html, 'html.parser')
buttons = soup.find_all('button', title='Edit Item')
for b in buttons[:2]:
    print(str(b))
    print("---")
