import json
from pathlib import Path

class OnboardingPage:
    def __init__(self, page):
        self.page = page
        self.locators = self.load_locators()

    def load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "onboarding.json"
        with open(path) as f:
            return json.load(f)

    async def open_hamburger_menu(self):
        await self.page.wait_for_selector(self.locators["bell_icon"], state="visible")
        await self.page.click(self.locators["bell_icon"])
        print("Hamburger menu clicked", flush=True)

    async def click_current_season(self):
        # ✅ Wait for menu to actually open and item to appear
        await self.page.wait_for_selector(self.locators["current_season"], state="visible")
        await self.page.click(self.locators["current_season"])
        print("Current season clicked", flush=True)

    async def click_farmer_list(self):
        await self.page.wait_for_selector(self.locators["farmer_list"], state="visible")
        await self.page.click(self.locators["farmer_list"])
        print("Farmer list clicked", flush=True)

    async def click_add(self):
        await self.page.wait_for_selector(self.locators["add_button"], state="visible")
        await self.page.click(self.locators["add_button"])
        print("Add button clicked", flush=True)

    async def click_add_new_farmer(self):
        await self.page.wait_for_selector(self.locators["add_new_farmer"], state="visible")
        await self.page.click(self.locators["add_new_farmer"])
        print("Add new farmer clicked", flush=True)

    async def complete_onboarding_flow(self):
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_add()
        await self.click_add_new_farmer()