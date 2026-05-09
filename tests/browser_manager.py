from playwright.async_api import async_playwright

class BrowserManager:

    async def start(self):

        self.p = await async_playwright().start()

        self.browser = await self.p.chromium.launch(
            headless=False,
            args=["--use-fake-ui-for-media-stream"]
        )

        self.context = await self.browser.new_context(
            geolocation={
                "latitude": 17.3850,
                "longitude": 78.4867
            },
            permissions=["geolocation"]
        )

        self.page = await self.context.new_page()

        return self.page

    async def stop(self):
        await self.browser.close()
        await self.p.stop()