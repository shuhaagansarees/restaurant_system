import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('templates/customer/status.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'Call Waiter' in line:
            # Print the context lines around the button
            print("--- HTML OUTPUT: CALL WAITER BUTTON ---")
            print("".join(lines[i-2:i+3]))
            print("--------------------------------------")
            break
            
with open('templates/customer/status.html', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'showToast' in content:
        print("Confirmed: showToast() is being used instead of alert()")
