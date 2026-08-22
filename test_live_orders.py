import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        # Clear cookies to force login
        await context.clear_cookies()
        page = await context.new_page()

        print('Navigating to login...')
        await page.goto('http://127.0.0.1:5000/admin/login')
        await page.fill('input[name="mobile"]', '7999620244')
        await page.fill('input[name="password"]', 'soulsip@2000')
        await page.click('button[type="submit"]')
        
        print('Logged in successfully.')

        print('Creating a new order via POS...')
        await page.goto('http://127.0.0.1:5000/admin/new_dinein')
        
        # Make sure we actually click a menu item
        await page.wait_for_selector('.menu-item-card button:has-text("+")')
        await page.click('.menu-item-card button:has-text("+")')
        await page.click('button:has-text("Save Order")')
        
        print('Navigated to live orders.')
        await page.goto('http://127.0.0.1:5000/admin/live_orders')

        card = await page.wait_for_selector('#list-new .order-card')
        order_id = await card.get_attribute('data-id')
        print(f'Order ID found: {order_id}')
        
        # Click Start Preparing
        print('Clicking Start Preparing...')
        await page.click(f'#list-new .order-card[data-id="{order_id}"] button:has-text("Start Preparing")')
        
        # Wait for the card to move to the Preparing list
        await page.wait_for_selector(f'#list-preparing .order-card[data-id="{order_id}"]')
        print('Card successfully moved to Preparing column!')
        await page.screenshot(path='artifacts/step2_preparing.png')
        
        # Click Mark Served (use wait_for_selector to ensure it's there)
        print('Clicking Mark Served...')
        served_btn = await page.wait_for_selector(f'#list-preparing .order-card[data-id="{order_id}"] button:has-text("Mark Served")')
        await served_btn.click()
        
        # Wait for the card to move to the Served list
        await page.wait_for_selector(f'#list-served .order-card[data-id="{order_id}"]')
        print('Card successfully moved to Served column!')
        await page.screenshot(path='artifacts/step3_served.png')

        # Click Complete
        print('Clicking Complete...')
        complete_btn = await page.wait_for_selector(f'#list-served .order-card[data-id="{order_id}"] button:has-text("Complete")')
        await complete_btn.click()

        # Wait for the card to move to the Completed list
        await page.wait_for_selector(f'#list-completed .order-card[data-id="{order_id}"]')
        print('Card successfully moved to Completed column!')
        await page.screenshot(path='artifacts/step4_completed.png')
        
        # Go to billing
        print('Navigating to billing...')
        await page.goto('http://127.0.0.1:5000/admin/billing')
        
        # Confirm it is in billing list
        billing_row = await page.wait_for_selector(f'tr:has-text("#{order_id}")')
        if billing_row:
            print(f'Order #{order_id} successfully found in Billing screen!')
            await page.screenshot(path='artifacts/step5_billing.png')
        else:
            print(f'Order #{order_id} not found in Billing!')
            
        await browser.close()

asyncio.run(main())
