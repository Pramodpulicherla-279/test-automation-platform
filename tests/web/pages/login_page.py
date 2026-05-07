import json
from pathlib import Path

class LoginPage:
    def __init__(self, page):
        self.page = page
        self.locators = self.load_locators()

    def load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "login.json"
        with open(path) as f:
            return json.load(f)

    async def navigate(self, url):
        print(f"\n[LOGIN] Navigating to: {url}", flush=True)
        await self.page.goto(url)
        print(f"[LOGIN] Page loaded: {self.page.url}", flush=True)

    async def login(self, username, password):
        print(f"[LOGIN] Waiting for email input: {self.locators['email_input']}", flush=True)
        await self.page.wait_for_selector(self.locators["email_input"], state="visible")
        await self.page.fill(self.locators["email_input"], username)
        print(f"[LOGIN] Email filled: {username}", flush=True)
    
        await self.page.wait_for_selector(self.locators["password_input"], state="visible")
        await self.page.fill(self.locators["password_input"], password)
        print(f"[LOGIN] Password filled", flush=True)
    
        print(f"[LOGIN] Clicking login button: {self.locators['login_button']}", flush=True)
        await self.page.wait_for_selector(self.locators["login_button"], state="visible")
    
        # ✅ Click and wait for navigation together
        async with self.page.expect_navigation(timeout=15000):
            await self.page.click(self.locators["login_button"])

            # Wait for URL change instead of navigation
            await self.page.wait_for_url("**/home-4", timeout=15000)
    
        print(f"[LOGIN] Navigation complete, current URL: {self.page.url}", flush=True)

    async def get_dashboard_text(self):
        selector = self.locators["dashboard_text"]
        print(f"\n[LOGIN] Waiting for dashboard page...", flush=True)
    
        # ✅ Ensure we are on dashboard
        await self.page.wait_for_url("**/home-4", timeout=15000)
        print(f"[LOGIN] URL confirmed: {self.page.url}", flush=True)
    
        # ❌ Remove domcontentloaded (not useful for SPA)
    
        # ✅ Retry logic (VERY IMPORTANT)
        for attempt in range(3):
            try:
                print(f"[LOGIN] {attempt+1}: Waiting for element {selector}", flush=True)    
                element = self.page.locator(selector)

                await element.wait_for(state="visible", timeout=5000)
                text = await element.inner_text()
                print(f"[LOGIN] ✅ Dashboard text: {text}", flush=True)

                return text
    
            except Exception as e:
                print(f"[RETRY] Attempt {attempt+1} failed: {e}", flush=True)
                await self.page.wait_for_timeout(2000)
    
        # Debugging
        await self.page.screenshot(path="dashboard_failure.png")
        print(await self.page.content())
    
        raise Exception("❌ Dashboard element not found")