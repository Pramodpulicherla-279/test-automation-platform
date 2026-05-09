import json
import os
import traceback
from pathlib import Path
import random
import logging

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
#  STEP TRACKER  —  prints TC context + step number for every action
# ══════════════════════════════════════════════════════════════════
class StepTracker:
    def set_tc(self, tc_id, description):
        self.current_tc  = tc_id
        self.step_num    = 0
        self.results     = {}
        logger.info(f"\n{'═'*65}")
        logger.info(f"  ▶  {tc_id}  —  {description}")
        logger.info(f"{'═'*65}")

    def step(self, msg):
        self.step_num += 1
        logger.info(f"  [{self.current_tc}] Step {self.step_num:02d} ▷ {msg}")

    def passed(self):
        logger.info(f"  ✅  {self.current_tc} PASSED")
        self.results[self.current_tc] = True

    def failed(self, err):
        logger.error(f"  ❌  {self.current_tc} FAILED at Step {self.step_num:02d} — {err}")
        self.results[self.current_tc] = False

# ══════════════════════════════════════════════════════════════════
#  PAGE OBJECT
# ══════════════════════════════════════════════════════════════════
class OnboardingPage:
    def __init__(self, page):
        self.page     = page
        self.locators = self._load_locators()
        self.tracker  = StepTracker()
        os.makedirs("screenshots", exist_ok=True)

    def _load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "onboarding.json"
        with open(path) as f:
            return json.load(f)

    def generate_mobile_number(self):
        first_digit      = str(random.randint(1, 5))
        remaining_digits = "".join(str(random.randint(0, 9)) for _ in range(9))
        return first_digit + remaining_digits

    # ── screenshot helper ────────────────────────────────────────
    async def _shot(self, name: str):
        path = f"screenshots/{name}.png"
        await self.page.screenshot(path=path)
        print(f"     📸 {path}", flush=True)

    # ── TC runner wrapper ────────────────────────────────────────
    async def _run_tc(self, tc_id: str, description: str, coro):
        """Sets TC context, awaits coro, catches and records result.
        A failed TC saves a screenshot and continues to the next TC."""
        self.tracker.set_tc(tc_id, description)
        try:
            await coro
            self.tracker.passed()
        except Exception as e:
            self.tracker.failed(e)
            await self._shot(f"{tc_id}_FAILED")

    # ════════════════════════════════════════════════════════════
    #  ATOMIC ACTIONS
    #  Every method calls tracker.step() so the console shows
    #  exactly which TC + step number was executing when it failed
    # ════════════════════════════════════════════════════════════

    # ── Sidebar / Navigation ─────────────────────────────────────
    async def open_hamburger_menu(self):
        self.tracker.step("Open hamburger menu")
        await self.page.wait_for_selector(self.locators["hamburger_menu_icon"], state="visible")
        await self.page.click(self.locators["hamburger_menu_icon"])

    async def click_current_season(self):
        self.tracker.step("Click Current Season")
        element = self.page.locator(self.locators["current_season"])
        await element.wait_for(state="visible", timeout=10000)
        await self.page.wait_for_timeout(1200)
        await element.click()

    async def click_organization(self):
        self.tracker.step("Click Organization")
        element = self.page.locator(self.locators["organization"])
        await element.wait_for(state="visible", timeout=10000)
        await self.page.wait_for_timeout(2200)
        await element.click()

    async def click_farmer_list(self):
        self.tracker.step("Click Farmer List")
        await self.page.wait_for_selector(self.locators["farmer_list"], state="visible")
        await self.page.click(self.locators["farmer_list"])

    async def click_add(self):
        self.tracker.step("Click Add button")
        await self.page.wait_for_selector(self.locators["add_button"], state="visible")
        await self.page.click(self.locators["add_button"])

    async def click_add_new_farmer(self):
        self.tracker.step("Click Add New Farmer")
        await self.page.wait_for_selector(self.locators["add_new_farmer"], state="visible")
        await self.page.click(self.locators["add_new_farmer"])

    # ── Add Farmer form ──────────────────────────────────────────
    async def get_add_farmer_screen_text(self):
        self.tracker.step("Verify Add Farmer page loaded")
        selector = self.locators["add_farmer"]["add_farmer_text"]
        await self.page.wait_for_url("**/add-farmer", timeout=15000)
        print(f"     URL: {self.page.url}", flush=True)
        for attempt in range(3):
            try:
                element = self.page.locator(selector)
                await element.wait_for(state="visible", timeout=5000)
                text = await element.inner_text()
                print(f"     Add Farmer text: '{text}'", flush=True)
                return text
            except Exception as e:
                print(f"     Retry {attempt+1}/3 failed: {e}", flush=True)
                await self.page.wait_for_timeout(2000)
        await self._shot("add_farmer_text_not_found")
        raise Exception("Add Farmer text not found after 3 retries")

    async def fill_farmer_name(self, name: str):
        self.tracker.step(f"Fill Farmer Name → '{name}'")
        await self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(self.locators["add_farmer"]["farmer_name"])
        await element.wait_for(state="visible")
        await element.fill(name)

    async def fill_mobile_number(self, mobile_number: str):
        self.tracker.step(f"Fill Mobile Number → {mobile_number}")
        await self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(self.locators["add_farmer"]["mobile_number"])
        await element.wait_for(state="visible")
        await element.fill(mobile_number)

    async def click_business_unit_field(self):
        self.tracker.step("Click Business Unit field")
        await self.page.wait_for_selector(self.locators["add_farmer"]["business_unit_input"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_farmer"]["business_unit_input"])

    async def click_business_unit_option(self):
        self.tracker.step("Select Business Unit option")
        await self.page.wait_for_selector(self.locators["add_farmer"]["business_unit_option"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_farmer"]["business_unit_option"])

    async def click_field_agent_input(self):
        self.tracker.step("Click Field Agent input")
        await self.page.wait_for_selector(self.locators["add_farmer"]["field_agent_input"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_farmer"]["field_agent_input"])

    async def fill_field_agent(self, field_agent: str):
        self.tracker.step(f"Fill Field Agent → '{field_agent}'")
        element = self.page.locator(self.locators["add_farmer"]["field_agent_input"])
        await element.wait_for(state="visible")
        await self.page.wait_for_timeout(800)
        await element.fill(field_agent)
        await self.page.wait_for_timeout(800)
        await element.press("Escape")

    async def click_save_farmer(self):
        self.tracker.step("Click Save Farmer")
        await self.page.wait_for_selector(self.locators["add_farmer"]["save_button"], state="visible")
        await self.page.click(self.locators["add_farmer"]["save_button"])

    # ── Add Farm ─────────────────────────────────────────────────
    async def click_save_farm(self):
        self.tracker.step("Click Save Farm")
        await self.page.wait_for_selector(self.locators["add_farm"]["save_farm_btn"], state="visible")
        await self.page.wait_for_timeout(4000)
        await self.page.click(self.locators["add_farm"]["save_farm_btn"])

    async def click_add_farm_btn(self):
        self.tracker.step("Click Add Farm button")
        await self.page.wait_for_selector(self.locators["add_farm"]["add_farm_btn"], state="visible")
        await self.page.wait_for_timeout(3000)
        await self.page.click(self.locators["add_farm"]["add_farm_btn"])

    # ── Add Crop form ────────────────────────────────────────────
    async def click_crop_input(self):
        self.tracker.step("Click Crop input")
        await self.page.wait_for_selector(self.locators["add_crop"]["crop_input"], state="visible")
        await self.page.click(self.locators["add_crop"]["crop_input"])

    async def click_crop_option(self):
        self.tracker.step("Select Crop option")
        await self.page.wait_for_selector(self.locators["add_crop"]["crop_option"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_crop"]["crop_option"])

    async def click_crop_duration_input(self):
        self.tracker.step("Click Crop Duration input")
        await self.page.wait_for_selector(self.locators["add_crop"]["crop_duration_input"], state="visible")
        await self.page.wait_for_timeout(1000)
        await self.page.click(self.locators["add_crop"]["crop_duration_input"])

    async def click_crop_duration_option(self):
        self.tracker.step("Select Crop Duration option")
        await self.page.wait_for_selector(self.locators["add_crop"]["crop_duration_option"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_crop"]["crop_duration_option"])

    async def click_sowing_type_input(self):
        self.tracker.step("Click Sowing Type input")
        await self.page.wait_for_selector(self.locators["add_crop"]["sowing_type_input"], state="visible")
        await self.page.click(self.locators["add_crop"]["sowing_type_input"])

    async def click_sowing_type_option(self):
        self.tracker.step("Select Sowing Type option")
        await self.page.wait_for_selector(self.locators["add_crop"]["sowing_type_option"], state="visible")
        await self.page.click(self.locators["add_crop"]["sowing_type_option"])

    async def click_sowing_date_input(self):
        self.tracker.step("Click Sowing Date input")
        await self.page.wait_for_selector(self.locators["add_crop"]["sowing_date_input"], state="visible")
        await self.page.wait_for_timeout(3000)
        await self.page.click(self.locators["add_crop"]["sowing_date_input"])

    # ── Date picker via flatpickr JS API ─────────────────────────
    async def click_sowing_date_option(self, aria_label: str = "May 1, 2026"):
        self.tracker.step(f"Select Sowing Date → '{aria_label}'")

        # 1. Open calendar via flatpickr JS instance (bypasses readonly attr)
        print("     Opening flatpickr via JS...", flush=True)
        await self.page.evaluate("""
            () => {
                const input = document.querySelector(
                    'input.flatpickr-basic.add_crop_target_sowing_date_picker'
                );
                if (!input) throw new Error('Flatpickr input NOT found in DOM');
                if (input._flatpickr) {
                    input._flatpickr.open();
                } else {
                    console.warn('No _flatpickr instance — falling back to click');
                    input.click();
                }
            }
        """)
        await self.page.wait_for_timeout(1000)
        await self._shot(f"{self.tracker.current_tc}_calendar_open")

        # 2. Confirm day element exists; dump all labels if not found
        day_selector = f"span[aria-label='{aria_label}']"
        count = await self.page.locator(day_selector).count()
        print(f"     Day spans matching '{aria_label}': {count}", flush=True)

        if count == 0:
            all_spans = await self.page.locator("span[aria-label]").all()
            print("     ⚠ Available aria-labels in DOM:", flush=True)
            for span in all_spans:
                label = await span.get_attribute("aria-label")
                print(f"       → '{label}'", flush=True)
            await self._shot(f"{self.tracker.current_tc}_date_not_found")
            raise Exception(f"Date '{aria_label}' not found in calendar DOM")

        # 3. Set date via flatpickr API — nothing can intercept this
        print("     Calling flatpickr.setDate()...", flush=True)
        await self.page.evaluate(f"""
            () => {{
                const input = document.querySelector(
                    'input.flatpickr-basic.add_crop_target_sowing_date_picker'
                );
                if (input && input._flatpickr) {{
                    input._flatpickr.setDate('{aria_label}', true, 'F j, Y');
                }} else {{
                    const span = document.querySelector("span[aria-label='{aria_label}']");
                    if (span) span.click();
                }}
            }}
        """)
        await self.page.wait_for_timeout(500)

        # 4. Verify input value was actually updated
        value = await self.page.input_value(
            "input.flatpickr-basic.add_crop_target_sowing_date_picker"
        )
        print(f"     Input value after selection: '{value}'", flush=True)
        await self._shot(f"{self.tracker.current_tc}_date_selected")

        if not value:
            raise Exception(f"Date '{aria_label}' was NOT written to input — setDate() had no effect")

    async def click_save_crop(self):
        self.tracker.step("Click Save Crop")
        await self.page.wait_for_selector(self.locators["add_crop"]["save_crop_btn"], state="visible")
        await self.page.click(self.locators["add_crop"]["save_crop_btn"])

    async def click_skip_crop(self):
        self.tracker.step("Click Skip Crop")
        await self.page.wait_for_selector(self.locators["add_crop"]["skip_crop_btn"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_crop"]["skip_crop_btn"])

    # ── Farmer row ───────────────────────────────────────────────
    async def click_farmer(self):
        self.tracker.step("Click Farmer row")
        await self.page.wait_for_timeout(3000)
        await self.page.wait_for_selector(self.locators["select_farmer"], state="visible")
        await self.page.click(self.locators["select_farmer"])

    # ── Pending Farms ────────────────────────────────────────────
    async def click_pending_farms_btn(self):
        self.tracker.step("Click Pending Farms")
        await self.page.wait_for_selector(self.locators["pending_farms_btn"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["pending_farms_btn"])

    async def click_type_dropdown(self):
        self.tracker.step("Click Type dropdown")
        await self.page.wait_for_selector(self.locators["farm_type_dropdown"], state="visible")
        await self.page.wait_for_timeout(3000)
        await self.page.click(self.locators["farm_type_dropdown"])

    async def click_only_farms_option(self):
    
        self.tracker.step("Select Only Farms")
    
        dropdown = self.page.locator(
            self.locators["farm_type_dropdown"]
        )
    
        await dropdown.wait_for(state="visible")
    
        await dropdown.select_option(value="only_farm")
    
        print("Only Farms option selected", flush=True)

    async def click_search_in_pending_farms(self):
        self.tracker.step("Click Search in Pending Farms")
        await self.page.wait_for_selector(self.locators["search_pending_farms_btn"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["search_pending_farms_btn"])

    async def click_three_dots_pending_farm(self):
        self.tracker.step("Click Three Dots on pending farm")
        await self.page.wait_for_selector(self.locators["three_dots_pending_farm"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["three_dots_pending_farm"])

    async def click_add_crop_btn_pending_farms(self):
        self.tracker.step("Click Add Crop (pending farms menu)")
        await self.page.wait_for_selector(self.locators["add_crop_btn"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_crop_btn"])

    async def click_add_boundary_btn_pending_farms(self):
        self.tracker.step("Click Add Boundary (pending farms menu)")
        await self.page.wait_for_selector(self.locators["add_boundary_btn"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_boundary_btn"])

    async def click_cancel_crop(self):
        self.tracker.step("Click Cancel Crop")
        await self.page.wait_for_selector(self.locators["cancel_btn"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["cancel_btn"])

    # ── Boundary / Map ───────────────────────────────────────────
    async def click_map_canvas(self):
        self.tracker.step("Click Map canvas")
        await self.page.wait_for_selector(self.locators["add_boundary"]["map_canvas"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_boundary"]["map_canvas"])

    async def draw_polygon(self):
        self.tracker.step("Draw polygon on map")
        await self.page.wait_for_selector(".mapboxgl-canvas")
        canvas = self.page.locator(".mapboxgl-canvas")
        box = await canvas.bounding_box()
        for x, y in [(200, 200), (350, 220), (400, 350), (250, 400)]:
            await self.page.mouse.click(box["x"] + x, box["y"] + y)
            await self.page.wait_for_timeout(500)
        await self.page.mouse.dblclick(box["x"] + 250, box["y"] + 400)
        print("     Polygon drawn", flush=True)

    async def click_save_boundary_btn(self):
        self.tracker.step("Click Save Boundary")
        await self.page.wait_for_selector(self.locators["add_boundary"]["save_boundary_btn"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_boundary"]["save_boundary_btn"])

    async def click_cancel_boundary_btn(self):
        self.tracker.step("Click Cancel Boundary")
        await self.page.wait_for_selector(self.locators["add_boundary"]["cancel_boundary_btn"], state="visible")
        await self.page.wait_for_timeout(2000)
        await self.page.click(self.locators["add_boundary"]["cancel_boundary_btn"])

    

    # ════════════════════════════════════════════════════════════
    #  SHARED FLOWS  (reusable step sequences)
    # ════════════════════════════════════════════════════════════
    async def _flow_add_farmer(self, name: str = "pramod", field_agent: str = "Ahmed033"):
        await self.click_farmer_list()
        await self.click_add()
        await self.click_add_new_farmer()
        await self.fill_farmer_name(name)
        await self.fill_mobile_number(self.generate_mobile_number())
        await self.click_business_unit_field()
        await self.click_business_unit_option()
        await self.fill_field_agent(field_agent)
        await self.click_save_farmer()

    async def _flow_navigate_farmer_farms(self):
        await self.click_farmer_list()
        await self.click_farmer()
        # await self.click_add_farm_btn()

    async def _flow_add_crop(self):
        await self.click_crop_input()
        await self.click_crop_option()
        await self.click_crop_duration_input()
        await self.click_crop_duration_option()
        await self.click_sowing_date_input()
        await self.click_sowing_date_option()
        await self.click_save_crop()

    async def _flow_add_boundary(self):
        await self.click_map_canvas()
        await self.draw_polygon()
        await self.click_save_boundary_btn()

    async def _flow_pending_farms_to_menu(self):
        await self.click_pending_farms_btn()
        await self.click_type_dropdown()
        await self.click_only_farms_option()
        await self.click_search_in_pending_farms()
        await self.click_three_dots_pending_farm()

    # ════════════════════════════════════════════════════════════
    #  INDIVIDUAL TEST CASES
    #  Each is isolated — one failure does NOT stop the rest
    # ════════════════════════════════════════════════════════════
    async def tc_001(self):
        async def _run():
            await self.open_hamburger_menu()
            await self.click_current_season()
            await self._flow_add_farmer()
            await self.click_save_farm()
        await self._run_tc("TC_001", "Add Farmer → Add Farm", _run())

    async def tc_002(self):
        async def _run():
            await self.click_current_season()
            await self._flow_add_farmer()
            await self.click_save_farm()
            await self._flow_add_crop()
            await self.click_cancel_boundary_btn()
        await self._run_tc("TC_002", "Add Farmer → Add Farm → Add Crop", _run())

    async def tc_003(self):
        async def _run():
            await self._flow_navigate_farmer_farms()
            await self.click_add_farm_btn()
            await self.click_save_farm()
            await self.click_skip_crop()
            await self.click_cancel_boundary_btn()
        await self._run_tc("TC_003", "Farmer List → Farmer Farms → Add Farm", _run())

    async def tc_004(self):
        async def _run():
            await self._flow_navigate_farmer_farms()
            await self.click_add_farm_btn()
            await self.click_save_farm()
            await self._flow_add_crop()
            await self.click_cancel_boundary_btn()
        await self._run_tc("TC_004", "Farmer Farms → Add Farm → Add Crop", _run())

    async def tc_005(self):
        async def _run():
            await self.page.wait_for_timeout(6000) 
            await self._flow_navigate_farmer_farms()
            await self.click_add_farm_btn()
            await self.click_save_farm()
            await self._flow_add_crop()
            await self._flow_add_boundary()
        await self._run_tc("TC_005", "Add Farm → Add Crop → Add Boundary", _run())

    async def tc_006(self):
        async def _run():
            await self._flow_navigate_farmer_farms()
            await self.click_add_farm_btn()
            await self.click_save_farm()
            await self.click_skip_crop()
            await self._flow_add_boundary()
        await self._run_tc("TC_006", "Add Farm → Skip Crop → Add Boundary", _run())

    async def tc_007(self):
        async def _run():
            await self._flow_pending_farms_to_menu()
            await self.click_add_crop_btn_pending_farms()
            await self._flow_add_crop()
            await self._flow_add_boundary()
        await self._run_tc("TC_007", "Pending Farms → Add Crop → Add Boundary", _run())

    async def tc_008(self):
        async def _run():
            await self.page.wait_for_timeout(6000)
            await self._flow_pending_farms_to_menu()
            await self.click_add_boundary_btn_pending_farms()
            await self._flow_add_boundary()
        await self._run_tc("TC_008", "Pending Farms → Add Boundary", _run())

    async def tc_009(self):
        async def _run():
            await self._flow_add_farmer()
        await self._run_tc("TC_009", "Add Single Farmer", _run())

    async def tc_010(self):
        async def _run():
            await self._flow_navigate_farmer_farms()
            await self.click_add_farm_btn()
            await self.click_save_farm()
            await self._flow_add_crop()
        await self._run_tc("TC_010", "Farmer Farms → Add Farm → Add Crop", _run())

    # ════════════════════════════════════════════════════════════
    #  MAIN ENTRY POINT
    # ════════════════════════════════════════════════════════════
    async def complete_onboarding_flow(self):
        for tc in [
            self.tc_001, self.tc_002, self.tc_003, self.tc_004, self.tc_005, self.tc_006,
            self.tc_007, 
            self.tc_008, self.tc_009, self.tc_010,
        ]:
            await tc()

        # self.tracker.print_summary()