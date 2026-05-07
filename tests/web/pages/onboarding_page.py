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

### Add farmer flow ###
    async def open_hamburger_menu(self):
        await self.page.wait_for_selector(self.locators["hamburger_menu_icon"], state="visible")
        await self.page.click(self.locators["hamburger_menu_icon"])
        print("Hamburger menu clicked", flush=True)

    async def click_current_season(self):
        selector = self.locators["current_season"]
        element = self.page.locator(selector)
    
        print("[SIDEBAR] Waiting for sidebar to stabilize...", flush=True)
    
        await element.wait_for(state="visible", timeout=10000)
        # ✅ small delay for animation (best practical fix)
        await self.page.wait_for_timeout(800)
    
        await element.click()
    
        print("[SIDEBAR] Current season clicked", flush=True)

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

## wait till add farmer page loads

    async def get_add_farmer_screen_text(self):
        selector = self.locators["add_farmer"]["add_farmer_text"]
        print(f"\n[Add farmer screen] Waiting for Add farmer page...", flush=True)
    
        # ✅ Ensure we are on dashboard
        await self.page.wait_for_url("**/add-farmer", timeout=15000)
        print(f"[Add farmer screen] URL confirmed: {self.page.url}", flush=True)
    
        # ❌ Remove domcontentloaded (not useful for SPA)
    
        # ✅ Retry logic (VERY IMPORTANT)
        for attempt in range(3):
            try:
                print(f"[Add farmer screen] {attempt+1}: Waiting for element {selector}", flush=True)    
                element = self.page.locator(selector)

                await element.wait_for(state="visible", timeout=5000)
                text = await element.inner_text()
                print(f"[Add farmer screen] ✅ Add farmer text: {text}", flush=True)

                return text
    
            except Exception as e:
                print(f"[RETRY] Attempt {attempt+1} failed: {e}", flush=True)
                await self.page.wait_for_timeout(2000)
    
        # Debugging
        await self.page.screenshot(path="add_farmer_failure.png")
        print(await self.page.content())
    
        raise Exception("❌ Add farmer text not found")

    async def fill_farmer_name(self, name: str):
        await self.page.wait_for_load_state("domcontentloaded")
    
        element = self.page.locator(self.locators["add_farmer"]["farmer_name"])
    
        await element.wait_for(state="visible")
        await element.fill(name)
    
        print(f"farmer_name filled: {name}", flush=True)

    async def fill_mobile_number(self, mobile_number: str):
        await self.page.wait_for_load_state("domcontentloaded")
    
        element = self.page.locator(self.locators["add_farmer"]["mobile_number"])
    
        await element.wait_for(state="visible")
        await element.fill(mobile_number)
    
        print(f"mobile_number filled: {mobile_number}", flush=True)

    async def click_business_unit_field(self):
        await self.page.wait_for_selector(self.locators["add_farmer"]["business_unit_input"], state="visible")
        await self.page.click(self.locators["add_farmer"]["business_unit_input"])
        print("Business unit field clicked", flush=True)

    async def click_business_unit_option(self):
        await self.page.wait_for_selector(self.locators["add_farmer"]["business_unit_option"], state="visible")
        await self.page.click(self.locators["add_farmer"]["business_unit_option"])
        print("Business unit option clicked", flush=True)

    async def click_field_agent_input(self):
        await self.page.wait_for_selector(self.locators["add_farmer"]["field_agent_input"], state="visible")
        await self.page.click(self.locators["add_farmer"]["field_agent_input"])
        print("Field agent input clicked", flush=True)

    async def fill_field_agent(self, field_agent: str):
        await self.page.wait_for_load_state("domcontentloaded")
    
        element = self.page.locator(self.locators["add_farmer"]["field_agent_input"])
    
        await element.wait_for(state="visible")
        await self.page.wait_for_timeout(800)
        await element.fill(field_agent)
        await self.page.wait_for_timeout(800)
        await element.press("Escape")
    
        print(f"field_agent filled: {field_agent}", flush=True)

    async def click_save(self):
        await self.page.wait_for_selector(self.locators["add_farmer"]["save_button"], state="visible")
        await self.page.click(self.locators["add_farmer"]["save_button"])
        print("Save button clicked", flush=True)


    async def complete_onboarding_flow(self):
        ##add farmer flow
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_add()
        await self.click_add_new_farmer()
        await self.fill_farmer_name("pramod")
        await self.fill_mobile_number("1204567890")
        await self.click_business_unit_field()
        await self.click_business_unit_option()
        await self.fill_field_agent("Ahmed033")
        await self.click_save()
        
        ##add farm  flow
