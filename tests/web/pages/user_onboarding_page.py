import json
from pathlib import Path

class UserOnboardingPage:
    def __init__(self, page):
        self.page = page
        self.locators = self.load_locators()

    def load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "user_onboarding.json"
        with open(path) as f:
            return json.load(f)
        
    ### Add user flow ###
    async def open_hamburger_menu(self):
        await self.page.wait_for_selector(self.locators["hamburger_menu_icon"], state="visible")
        await self.page.click(self.locators["hamburger_menu_icon"])
        print("Hamburger menu clicked", flush=True)

    async def click_organization(self):
        selector = self.locators["organization"]
        element = self.page.locator(selector)
        print("[SIDEBAR] Waiting for sidebar to stabilize...", flush=True)

        await element.wait_for(state="visible", timeout=10000)
        # ✅ small delay for animation (best practical fix)
        await self.page.wait_for_timeout(2200)
        await element.click()
        print("[SIDEBAR] Organization clicked", flush=True)
 
    
    async def click_users(self):
        await self.page.wait_for_selector(self.locators["users"], state="visible")
        await self.page.click(self.locators["users"])
        print("Users clicked", flush=True)

    async def click_add(self):
        await self.page.wait_for_selector(self.locators["add_button"], state="visible")
        await self.page.click(self.locators["add_button"])
        print("Add button clicked", flush=True)

    async def click_add_single_user(self):
        await self.page.wait_for_selector(self.locators["add_single_user"], state="visible")
        await self.page.click(self.locators["add_single_user"])
        print("Add single user clicked", flush=True)

    async def get_add_user_screen_text(self):
        selector = self.locators["add_user"]["add_user_text"]
        print(f"\n[Add user screen] Waiting for Add user page...", flush=True)
    
        # ✅ Ensure we are on dashboard
        await self.page.wait_for_url("**/add-user", timeout=15000)
        print(f"[Add user screen] URL confirmed: {self.page.url}", flush=True)
    
        # ❌ Remove domcontentloaded (not useful for SPA)
    
        # ✅ Retry logic (VERY IMPORTANT)
        for attempt in range(3):
            try:
                print(f"[Add user screen] {attempt+1}: Waiting for element {selector}", flush=True)    
                element = self.page.locator(selector)

                await element.wait_for(state="visible", timeout=5000)
                text = await element.inner_text()
                print(f"[Add user screen] ✅ Add user text: {text}", flush=True)

                return text
    
            except Exception as e:
                print(f"[RETRY] Attempt {attempt+1} failed: {e}", flush=True)
                await self.page.wait_for_timeout(2000)
    
        # Debugging
        await self.page.screenshot(path="add_user_failure.png")
        print(await self.page.content())
    
        raise Exception("❌ Add user text not found")

    async def fill_user_name(self, name: str):
        await self.page.wait_for_load_state("domcontentloaded")
    
        element = self.page.locator(self.locators["add_user"]["user_name"])
    
        await element.wait_for(state="visible")
        await element.fill(name)
    
        print(f"user_name filled: {name}", flush=True)

    async def fill_mobile_number(self, mobile_number: str):
        await self.page.wait_for_load_state("domcontentloaded")
    
        element = self.page.locator(self.locators["add_user"]["mobile_number"])
    
        await element.wait_for(state="visible")
        await element.fill(mobile_number)
    
        print(f"mobile_number filled: {mobile_number}", flush=True)

    async def click_business_unit_field(self):
        await self.page.wait_for_selector(self.locators["add_user"]["business_unit_input"], state="visible")
        await self.page.click(self.locators["add_user"]["business_unit_input"])
        print("Business unit field clicked", flush=True) 

     
    async def click_business_unit_option(self):
        await self.page.wait_for_selector(self.locators["add_user"]["business_unit_option"], state="visible")
        await self.page.click(self.locators["add_user"]["business_unit_option"])
        print("Business unit option clicked", flush=True)

    
    async def click_user_role_field(self):
        await self.page.wait_for_selector(self.locators["add_user"]["user_role_input"], state="visible")
        await self.page.click(self.locators["add_user"]["user_role_input"])
        print("User role field clicked", flush=True) 
    
    async def click_user_role_option(self):
        await self.page.wait_for_selector(self.locators["add_user"]["user_role_option"], state="visible")
        await self.page.click(self.locators["add_user"]["user_role_option"])
        print("User role option clicked", flush=True)

    async def click_save(self):
        await self.page.wait_for_selector(self.locators["add_user"]["save_button"], state="visible")
        await self.page.click(self.locators["add_user"]["save_button"])
        print("Save button clicked", flush=True)

#######################################################################################
    async def complete_user_onboarding_flow(self):
        ##add user flow
        await self.open_hamburger_menu()
        await self.click_organization()
        await self.click_users()
        await self.click_add()
        await self.click_add_single_user()
        await self.fill_user_name("pramod")
        await self.fill_mobile_number("1204567890")
        await self.click_business_unit_field()
        await self.click_business_unit_option()
        await self.click_user_role_field()
        await self.click_user_role_option()
        await self.click_save()

        
        ##add farm  flow