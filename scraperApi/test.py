from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        