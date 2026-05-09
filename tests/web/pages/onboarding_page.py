import json
from pathlib import Path
import random

class OnboardingPage:
    def __init__(self, page):
        self.page = page
        self.locators = self.load_locators()

    def load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "onboarding.json"
        with open(path) as f:
            return json.load(f)

    def generate_mobile_number(self):
        first_digit = str(random.randint(1, 5))
        remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(9))

        return first_digit + remaining_digits

    async def fill_mobile_number(self):
        mobile_number = self.generate_mobile_number()

        await self.page.fill(
            self.locators["mobile_number"],
            mobile_number
        )

        print(f"Entered Mobile Number: {mobile_number}", flush=True)
        
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
        await self.page.wait_for_timeout(1200)
    
        await element.click()
    
        print("[SIDEBAR] Current season clicked", flush=True)

    async def click_organization(self):
        selector = self.locators["organization"]
        element = self.page.locator(selector)
        print("[SIDEBAR] Waiting for sidebar to stabilize...", flush=True)
    
        await element.wait_for(state="visible", timeout=10000)
        # ✅ small delay for animation (best practical fix)
        await self.page.wait_for_timeout(2200)
        await element.click()
        print("[SIDEBAR] Organization clicked", flush=True)

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
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_farmer"]["business_unit_input"])
        print("Business unit field clicked", flush=True)

    async def click_business_unit_option(self):
        await self.page.wait_for_selector(self.locators["add_farmer"]["business_unit_option"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_farmer"]["business_unit_option"])
        print("Business unit option clicked", flush=True)

    async def click_field_agent_input(self):
        await self.page.wait_for_selector(self.locators["add_farmer"]["field_agent_input"], state="visible")
        await self.page.wait_for_timeout(2000)
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

    async def click_save_farmer(self):
        await self.page.wait_for_selector(self.locators["add_farmer"]["save_button"], state="visible")
        await self.page.click(self.locators["add_farmer"]["save_button"])
        print("Save button clicked", flush=True)

    ###### add farm flow ######

    async def click_save_farm(self):
        await self.page.wait_for_selector(self.locators["add_farm"]["save_farm_btn"], state="visible")
        await self.page.wait_for_timeout(4000)
        await self.page.click(self.locators["add_farm"]["save_farm_btn"])
        print("Save farm button clicked", flush=True)

    ##### Add crop flow ######

    async def click_crop_input(self):
        await self.page.wait_for_selector(self.locators["add_crop"]["crop_input"], state="visible")
        await self.page.click(self.locators["add_crop"]["crop_input"])
        print("Crop input clicked", flush=True)

    async def click_crop_option(self):
        await self.page.wait_for_selector(self.locators["add_crop"]["crop_option"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_crop"]["crop_option"])
        print("Crop option clicked", flush=True)

    async def click_crop_duration_input(self):
        await self.page.wait_for_selector(self.locators["add_crop"]["crop_duration_input"], state="visible")
        await self.page.wait_for_timeout(1000)
        await self.page.click(self.locators["add_crop"]["crop_duration_input"])
        print("Crop duration input clicked", flush=True)

    async def click_crop_duration_option(self):
        await self.page.wait_for_selector(self.locators["add_crop"]["crop_duration_option"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_crop"]["crop_duration_option"])
        print("Crop duration option clicked", flush=True)

    async def click_sowing_type_input(self):
        await self.page.wait_for_selector(self.locators["add_crop"]["sowing_type_input"], state="visible")
        await self.page.click(self.locators["add_crop"]["sowing_type_input"])
        print("Sowing type input clicked", flush=True)

    async def click_sowing_type_option(self):
        await self.page.wait_for_selector(self.locators["add_crop"]["sowing_type_option"], state="visible")
        await self.page.click(self.locators["add_crop"]["sowing_type_option"])
        print("Sowing type option clicked", flush=True)

    async def click_sowing_date_input(self):
        await self.page.wait_for_selector(self.locators["add_crop"]["sowing_date_input"], state="visible")
        await self.page.wait_for_timeout(3000)
        await self.page.click(self.locators["add_crop"]["sowing_date_input"])
        print("Sowing date input clicked", flush=True)

    # async def click_sowing_date_option(self):
    #     await self.page.wait_for_selector(self.locators["add_crop"]["sowing_date_option"], state="visible")
    #     await self.page.wait_for_timeout(2000)
    #     await self.page.click(self.locators["add_crop"]["sowing_date_option"])
    #     print("Sowing date option clicked", flush=True)

    # Wait for calendar to fully open    
    async def click_sowing_date_option(self, aria_label: str = "May 1, 2026"):
        print("Step 1: Opening calendar via flatpickr JS instance...", flush=True)
        
        # Trigger flatpickr open via its JS instance — most reliable approach
        await self.page.evaluate("""
            () => {
                const input = document.querySelector('input.flatpickr-basic.add_crop_target_sowing_date_picker');
                if (input && input._flatpickr) {
                    input._flatpickr.open();
                } else {
                    input.click(); // fallback
                }
            }
        """)
        
        await self.page.wait_for_timeout(1000)
        await self.page.screenshot(path="debug_calendar_open.png")
        print("Step 2: Calendar opened", flush=True)
    
        # Now wait for the day span directly
        day_selector = f"span[aria-label='{aria_label}']"
        
        count = await self.page.locator(day_selector).count()
        print(f"Step 3: Matching day elements found: {count}", flush=True)
        
        if count == 0:
            # Print all available labels
            all_spans = await self.page.locator("span[aria-label]").all()
            print("Available aria-labels:", flush=True)
            for span in all_spans:
                label = await span.get_attribute("aria-label")
                print(f"  -> {label}", flush=True)
            raise Exception(f"Date '{aria_label}' not found in calendar")
    
        # Click via flatpickr JS instance — bypasses all DOM interception
        await self.page.evaluate(f"""
            () => {{
                const input = document.querySelector('input.flatpickr-basic.add_crop_target_sowing_date_picker');
                if (input && input._flatpickr) {{
                    input._flatpickr.setDate('{aria_label}', true, 'F j, Y');
                }}
            }}
        """)
        
        await self.page.wait_for_timeout(500)
        await self.page.screenshot(path="debug_after_click.png")
        
        # Verify date was set
        value = await self.page.input_value("input.flatpickr-basic.add_crop_target_sowing_date_picker")
        print(f"Step 4: Input value after selection: '{value}'", flush=True)
    async def click_save_crop(self):
        await self.page.wait_for_selector(self.locators["add_crop"]["save_crop_btn"], state="visible")
        await self.page.click(self.locators["add_crop"]["save_crop_btn"])
        print("Save crop button clicked", flush=True)

    async def click_farmer(self):
        await self.page.wait_for_selector(self.locators["select_farmer"], state="visible")
        await self.page.click(self.locators["select_farmer"])
        print("Farmer clicked", flush=True)

    async def click_add_farm_btn(self):
            await self.page.wait_for_selector(self.locators["add_farm"]["add_farm_btn"], state="visible")
            await self.page.wait_for_timeout(3000)
            await self.page.click(self.locators["add_farm"]["add_farm_btn"])
            print("Add farm button clicked", flush=True)
    
    async def click_pending_farms_btn(self):
            await self.page.wait_for_selector(self.locators["pending_farms_btn"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["pending_farms_btn"])
            print("Pending farms button clicked", flush=True)
    
    async def click_type_dropdown(self):
            await self.page.wait_for_selector(self.locators["type_dropdown"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["type_dropdown"])
            print("Type dropdown clicked", flush=True)

    async def click_only_farms_option(self):
            await self.page.wait_for_selector(self.locators["only_farms_option"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["only_farms_option"])
            print("Only farms option clicked", flush=True)

    async def click_search_in_pending_farms(self):
            await self.page.wait_for_selector(self.locators["search_pending_farms_btn"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["search_pending_farms_btn"])
            print("Search pending farms button clicked", flush=True)    

    async def click_three_dots_pending_farm(self):
            await self.page.wait_for_selector(self.locators["three_dots_pending_farm"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["three_dots_pending_farm"])
            print("Three dots pending farm clicked", flush=True) 

    async def click_add_crop_btn_pending_farms(self):
            await self.page.wait_for_selector(self.locators["add_crop_btn"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["add_crop_btn"])
            print("Add crop button clicked", flush=True) 

    async def click_add_boundary_btn_pending_farms(self):
            await self.page.wait_for_selector(self.locators["add_boundary_btn"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["add_boundary_btn"])
            print("Add boundary button clicked", flush=True) 

    async def click_cancel_crop(self):
            await self.page.wait_for_selector(self.locators["cancel_btn"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["cancel_btn"])
            print("Cancel crop button clicked", flush=True) 

    async def click_skip_crop(self):
            await self.page.wait_for_selector(self.locators["add_crop"]["skip_crop_btn"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["add_crop"]["skip_crop_btn"])
            print("Skip crop button clicked", flush=True) 

    async def click_map_canvas(self):
            await self.page.wait_for_selector(self.locators["add_boundary"]["map_canvas"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["add_boundary"]["map_canvas"])
            print("Map canvas clicked", flush=True) 

    async def draw_polygon(self):
        await self.page.wait_for_selector(".mapboxgl-canvas")
        canvas = self.page.locator(".mapboxgl-canvas")
        box = await canvas.bounding_box()
        points = [
            (200, 200),
            (350, 220),
            (400, 350),
            (250, 400)
        ]
        for x, y in points:
            await self.page.mouse.click(
                box["x"] + x,
                box["y"] + y
            )
            await self.page.wait_for_timeout(500)
    
        # Finish polygon
        await self.page.mouse.dblclick(
            box["x"] + 250,
            box["y"] + 400
        )
        print("Polygon drawn successfully", flush=True)

    async def click_save_boundary_btn(self):
            await self.page.wait_for_selector(self.locators["add_boundary"]["save_boundary_btn"], state="visible")
            await self.page.wait_for_timeout(2000)
            await self.page.click(self.locators["add_boundary"]["save_boundary_btn"])
            print("Save boundary button clicked", flush=True) 

#####################################################################################################################
    async def complete_onboarding_flow(self):
        # TC_001 -- add farmer > add farm 
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_add()
        await self.click_add_new_farmer()
        await self.fill_farmer_name("pramod")
        await self.fill_mobile_number(self.generate_mobile_number())
        await self.click_business_unit_field()
        await self.click_business_unit_option()
        await self.fill_field_agent("Ahmed033")
        await self.click_save_farmer()
        
        ##add farm  flow
        await self.click_save_farm()

        # TC_002 -- add farmer > add farm > add crop
        ##add farmer flow
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_add()
        await self.click_add_new_farmer()
        await self.fill_farmer_name("pramod")
        await self.fill_mobile_number(self.generate_mobile_number())
        await self.click_business_unit_field()
        await self.click_business_unit_option()
        await self.fill_field_agent("Ahmed033")
        await self.click_save_farmer()
        
        ##add farm  flow
        await self.click_save_farm()

        ### add crop flow
        await self.click_crop_input()
        await self.click_crop_option()
        await self.click_crop_duration_input()
        await self.click_crop_duration_option()
        # await self.click_sowing_type_input()
        # await self.click_sowing_type_option()
        await self.click_sowing_date_input()
        await self.click_sowing_date_option()
        await self.click_save_crop()

        #TC_003 -- farmer list > farmer farms > add farm
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_farmer()
        await self.click_add_farm_btn()
        await self.click_save_farm()

        #TC_004 -- farmer list > farmer farms > add farm > add crop
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_farmer()
        await self.click_add_farm_btn()
        await self.click_save_farm()
        await self.click_crop_input()
        await self.click_crop_option()
        await self.click_crop_duration_input()
        await self.click_crop_duration_option()
        # await self.click_sowing_type_input()
        # await self.click_sowing_type_option()
        await self.click_sowing_date_input()
        await self.click_sowing_date_option()
        await self.click_save_crop()

        #TC_005 -- farmer list > farmer farms > add farm > add crop > add boundary
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_farmer()
        await self.click_add_farm_btn()
        await self.click_save_farm()
        await self.click_crop_input()
        await self.click_crop_option()
        await self.click_crop_duration_input()
        await self.click_crop_duration_option()
        # await self.click_sowing_type_input()
        # await self.click_sowing_type_option()
        await self.click_sowing_date_input()
        await self.click_sowing_date_option()
        await self.click_save_crop()
        await self.click_map_canvas()
        await self.draw_polygon()
        await self.click_save_boundary_btn()

        #TC_006 -- farmer list > farmer farms > add farm > skip crop > add boundary
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_farmer()
        await self.click_add_farm_btn()
        await self.click_save_farm()
        await self.click_skip_crop()
        await self.click_map_canvas()
        await self.draw_polygon()
        await self.click_save_boundary_btn()

        #TC_007 -- pending farms > add crop >  add boundary
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_pending_farms_btn()
        await self.click_type_dropdown()
        await self.click_only_farms_option()
        await self.click_search_in_pending_farms()
        await self.click_three_dots_pending_farm()
        await self.click_add_crop_btn_pending_farms()
        await self.click_crop_input()
        await self.click_crop_option()
        await self.click_crop_duration_input()
        await self.click_crop_duration_option()
        # await self.click_sowing_type_input()
        # await self.click_sowing_type_option()
        await self.click_sowing_date_input()
        await self.click_sowing_date_option()
        await self.click_save_crop()
        await self.click_map_canvas()
        await self.draw_polygon()
        await self.click_save_boundary_btn()

        #TC_008 -- pending farms > add boundary
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_pending_farms_btn()
        await self.click_type_dropdown()
        await self.click_only_farms_option()
        await self.click_search_in_pending_farms()
        await self.click_three_dots_pending_farm()
        await self.click_add_boundary_btn_pending_farms()
        await self.click_map_canvas()
        await self.draw_polygon()
        await self.click_save_boundary_btn()

        #TC_009 -- farmer list > Add single Farmer
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_add()
        await self.click_add_new_farmer()
        await self.fill_farmer_name("pramod")
        await self.fill_mobile_number(self.generate_mobile_number())
        await self.click_business_unit_field()
        await self.click_business_unit_option()
        await self.fill_field_agent("Ahmed033")
        await self.click_save_farmer()

        #TC_010 -- farmer farms > add farm > add crop
        await self.open_hamburger_menu()
        await self.click_current_season()
        await self.click_farmer_list()
        await self.click_farmer()
        await self.click_add_farm_btn()
        await self.click_save_farm()
        await self.click_crop_input()
        await self.click_crop_option()
        await self.click_crop_duration_input()
        await self.click_crop_duration_option()
        await self.click_sowing_date_input()
        await self.click_sowing_date_option()
        await self.click_save_crop() 





