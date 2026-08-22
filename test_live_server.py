import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        print('Navigating to live login...')
        await page.goto('https://restaurant-system-z5m7.onrender.com/admin/login')
        
        # Check if already logged in or need to fill form
        if 'login' in page.url:
            await page.fill('input[name="mobile"]', '7999620244')
            await page.fill('input[name="password"]', 'soulsip@2000')
            await page.click('button[type="submit"]')
        
        print('Logged in successfully.')

        print('Creating a new order via POS...')
        await page.goto('https://restaurant-system-z5m7.onrender.com/admin/new_dinein')
        await page.wait_for_selector('.menu-item-card button:has-text("+")')
        await page.click('.menu-item-card button:has-text("+")')
        await page.click('button:has-text("Save Order")')
        
        print('Navigated to live orders.')
        await page.goto('https://restaurant-system-z5m7.onrender.com/admin/live_orders')

        card = await page.wait_for_selector('#list-new .order-card')
        order_id = await card.get_attribute('data-id')
        print(f'Order ID found: {order_id}')
        
        # Click Start Preparing
        print('Clicking Start Preparing on live server...')
        await page.click(f'#list-new .order-card[data-id="{order_id}"] button:has-text("Start Preparing")')
        
        # Wait for the card to move to the Preparing list
        await page.wait_for_selector(f'#list-preparing .order-card[data-id="{order_id}"]')
        print('Card successfully moved to Preparing column on live server!')
        
        await browser.close()

asyncio.run(main())
