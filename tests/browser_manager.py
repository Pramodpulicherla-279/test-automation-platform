from playwright.async_api import async_playwright

class BrowserManager:
    async def start(self):
        self.p = await async_playwright().start()
        self.browser = await self.p.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        return self.page

    async def stop(self):
        await self.browser.close()
        await self.p.stop()