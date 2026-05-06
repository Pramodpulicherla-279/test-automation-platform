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
    
        print(f"[LOGIN] Navigation complete, current URL: {self.page.url}", flush=True)

    async def get_dashboard_text(self):
        selector = self.locators["dashboard_text"]
        print(f"\n[LOGIN] Waiting for URL to change from /login...", flush=True)
    
        # ✅ Wait for navigation away from login page first
        await self.page.wait_for_url("**/login", state="hidden")  # wrong — use below
        await self.page.wait_for_function("window.location.pathname !== '/login'", timeout=15000)
        print(f"[LOGIN] URL changed to: {self.page.url}", flush=True)
    
        # ✅ Now wait for page to fully load
        await self.page.wait_for_load_state("networkidle")
        print(f"[LOGIN] Page settled at: {self.page.url}", flush=True)
    
        # ✅ Now find the dashboard element
        print(f"[LOGIN] Waiting for dashboard element: {selector}", flush=True)
        await self.page.wait_for_selector(selector, state="visible", timeout=15000)
        text = await self.page.inner_text(selector)
        print(f"[LOGIN] Dashboard element found, text: '{text}'", flush=True)
        return text