import json
import os
import random
import allure
from pathlib import Path


class OnboardingPage:
    def __init__(self, page):
        self.page     = page
        self.locators = self._load_locators()
        os.makedirs("screenshots", exist_ok=True)

    def _load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "onboarding.json"
        with open(path) as f:
            return json.load(f)

    def generate_mobile_number(self) -> str:
        return str(random.randint(1, 5)) + "".join(str(random.randint(0, 9)) for _ in range(9))

    def _shot(self, name: str):
        path = f"screenshots/{name}.png"
        self.page.screenshot(path=path)
        with open(path, "rb") as f:
            allure.attach(f.read(), name=name, attachment_type=allure.attachment_type.PNG)

    # ── Atomic actions ────────────────────────────────────────────────
    def open_hamburger_menu(self):
        with allure.step("Open hamburger menu"):
            self.page.wait_for_selector(self.locators["hamburger_menu_icon"], state="visible")
            self.page.click(self.locators["hamburger_menu_icon"])

    def click_current_season(self):
        with allure.step("Click Current Season"):
            self.page.locator(self.locators["current_season"]).wait_for(state="visible", timeout=10_000)
            self.page.wait_for_timeout(1200)
            self.page.click(self.locators["current_season"])

    def click_farmer_list(self):
        with allure.step("Click Farmer List"):
            self.page.wait_for_timeout(5000)
            self.page.wait_for_selector(self.locators["farmer_list"], state="visible")
            self.page.click(self.locators["farmer_list"])

    def click_add(self):
        with allure.step("Click Add button"):
            self.page.wait_for_timeout(3000)
            self.page.wait_for_selector(self.locators["add_button"], state="visible")
            self.page.click(self.locators["add_button"])

    def click_add_new_farmer(self):
        with allure.step("Click Add New Farmer"):
            self.page.wait_for_selector(self.locators["add_new_farmer"], state="visible")
            self.page.click(self.locators["add_new_farmer"])

    def fill_farmer_name(self, name: str):
        with allure.step(f"Fill Farmer Name → '{name}'"):
            el = self.page.locator(self.locators["add_farmer"]["farmer_name"])
            el.wait_for(state="visible")
            el.fill(name)

    def fill_mobile_number(self, mobile: str):
        with allure.step(f"Fill Mobile → {mobile}"):
            el = self.page.locator(self.locators["add_farmer"]["mobile_number"])
            el.wait_for(state="visible")
            el.fill(mobile)

    def click_business_unit_field(self):
        with allure.step("Click Business Unit field"):
            self.page.wait_for_selector(self.locators["add_farmer"]["business_unit_input"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_farmer"]["business_unit_input"])

    def click_business_unit_option(self):
        with allure.step("Select Business Unit option"):
            self.page.wait_for_selector(self.locators["add_farmer"]["business_unit_option"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_farmer"]["business_unit_option"])

    def fill_field_agent(self, field_agent: str):
        with allure.step(f"Fill Field Agent → '{field_agent}'"):
            el = self.page.locator(self.locators["add_farmer"]["field_agent_input"])
            el.wait_for(state="visible")
            self.page.wait_for_timeout(800)
            el.fill(field_agent)
            self.page.wait_for_timeout(800)
            el.press("Escape")

    def click_save_farmer(self):
        with allure.step("Click Save Farmer"):
            self.page.wait_for_selector(self.locators["add_farmer"]["save_button"], state="visible")
            self.page.click(self.locators["add_farmer"]["save_button"])

    def click_save_farm(self):
        with allure.step("Click Save Farm"):
            self.page.wait_for_selector(self.locators["add_farm"]["save_farm_btn"], state="visible")
            self.page.wait_for_timeout(4000)
            self.page.click(self.locators["add_farm"]["save_farm_btn"])

    def click_add_farm_btn(self):
        with allure.step("Click Add Farm button"):
            self.page.wait_for_selector(self.locators["add_farm"]["add_farm_btn"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.locators["add_farm"]["add_farm_btn"])

    def click_farmer(self):
        with allure.step("Click Farmer row"):
            self.page.wait_for_selector(self.locators["select_farmer"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.locators["select_farmer"])

    def click_crop_input(self):
        with allure.step("Click Crop input"):
            self.page.wait_for_timeout(3000)
            self.page.wait_for_selector(self.locators["add_crop"]["crop_input"], state="visible")
            self.page.click(self.locators["add_crop"]["crop_input"])

    def click_crop_option(self):
        with allure.step("Select Crop option"):
            self.page.wait_for_selector(self.locators["add_crop"]["crop_option"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.locators["add_crop"]["crop_option"])

    def click_crop_duration_input(self):
        with allure.step("Click Crop Duration input"):
            self.page.wait_for_selector(self.locators["add_crop"]["crop_duration_input"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.locators["add_crop"]["crop_duration_input"])

    def click_crop_duration_option(self):
        with allure.step("Select Crop Duration option"):
            self.page.wait_for_selector(self.locators["add_crop"]["crop_duration_option"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.locators["add_crop"]["crop_duration_option"])

    def click_sowing_date_input(self):
        with allure.step("Click Sowing Date input"):
            self.page.wait_for_selector(self.locators["add_crop"]["sowing_date_input"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.locators["add_crop"]["sowing_date_input"])

    def click_sowing_date_option(self, aria_label: str = "May 1, 2026"):
        # self.tracker.step(f"Select Sowing Date → '{aria_label}'")

        # 1. Open calendar via flatpickr JS instance (bypasses readonly attr)
        print("     Opening flatpickr via JS...", flush=True)
        self.page.evaluate("""
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
        self.page.wait_for_timeout(1000)
        # self._shot(f"{self.tracker.current_tc}_calendar_open")

        # 2. Confirm day element exists; dump all labels if not found
        day_selector = f"span[aria-label='{aria_label}']"
        count = self.page.locator(day_selector).count()
        # print(f"     Day spans matching '{aria_label}': {count}", flush=True)

        if count == 0:
            all_spans = self.page.locator("span[aria-label]").all()
            # print("     ⚠ Available aria-labels in DOM:", flush=True)
            for span in all_spans:
                label = span.get_attribute("aria-label")
                # print(f"       → '{label}'", flush=True)
            self._shot(f"{self.tracker.current_tc}_date_not_found")
            raise Exception(f"Date '{aria_label}' not found in calendar DOM")

        # 3. Set date via flatpickr API — nothing can intercept this
        # print("     Calling flatpickr.setDate()...", flush=True)
        self.page.evaluate(f"""
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
        self.page.wait_for_timeout(500)

        # 4. Verify input value was actually updated
        value = self.page.input_value(
            "input.flatpickr-basic.add_crop_target_sowing_date_picker"
        )
        # print(f"     Input value after selection: '{value}'", flush=True)
        # self._shot(f"{self.tracker.current_tc}_date_selected")

        if not value:
            raise Exception(f"Date '{aria_label}' was NOT written to input — setDate() had no effect")

    def click_save_crop(self):
        with allure.step("Click Save Crop"):
            self.page.wait_for_selector(self.locators["add_crop"]["save_crop_btn"], state="visible")
            self.page.click(self.locators["add_crop"]["save_crop_btn"])

    def click_skip_crop(self):
        with allure.step("Click Skip Crop"):
            self.page.wait_for_selector(self.locators["add_crop"]["skip_crop_btn"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_crop"]["skip_crop_btn"])

    def click_cancel_boundary_btn(self):
        with allure.step("Click Cancel Boundary"):
            self.page.wait_for_selector(self.locators["add_boundary"]["cancel_boundary_btn"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_boundary"]["cancel_boundary_btn"])

    def click_pending_farms_btn(self):
        with allure.step("Click Pending Farms"):
            self.page.wait_for_selector(self.locators["pending_farms_btn"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["pending_farms_btn"])

    def click_type_dropdown(self):
        with allure.step("Click Type dropdown"):
            self.page.wait_for_selector(self.locators["farm_type_dropdown"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["farm_type_dropdown"])

    def click_only_farms_option(self):    
        dropdown = self.page.locator(
            self.locators["farm_type_dropdown"]
        )
        dropdown.wait_for(state="visible")
        dropdown.select_option(value="only_farm")

    def click_search_in_pending_farms(self):
        with allure.step("Search in Pending Farms"):
            self.page.wait_for_selector(self.locators["search_pending_farms_btn"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["search_pending_farms_btn"])

    def click_three_dots_pending_farm(self):
        with allure.step("Click Three Dots on Pending Farm"):
            self.page.wait_for_selector(self.locators["three_dots_pending_farm"], state="visible")
            self.page.wait_for_timeout(4000)
            self.page.click(self.locators["three_dots_pending_farm"])

    def click_add_crop_btn_pending_farms(self):
        with allure.step("Click Add Crop (Pending Farms)"):
            self.page.wait_for_selector(self.locators["add_crop_btn_pending_farms"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_crop_btn_pending_farms"])

    def click_add_boundary_btn_pending_farms(self):
        with allure.step("Click Add Boundary (Pending Farms)"):
            self.page.wait_for_selector(self.locators["add_boundary_btn"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_boundary_btn"])

    def click_map_canvas(self):
        with allure.step("Click Map canvas"):
            self.page.wait_for_selector(self.locators["add_boundary"]["map_canvas"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_boundary"]["map_canvas"])

    def draw_polygon(self):
        with allure.step("Draw polygon on map"):
            self.page.wait_for_selector(".mapboxgl-canvas")
            canvas = self.page.locator(".mapboxgl-canvas")
            box = canvas.bounding_box()
            for x, y in [(200, 200), (350, 220), (400, 350), (250, 400)]:
                self.page.mouse.click(box["x"] + x, box["y"] + y)
                self.page.wait_for_timeout(500)
            self.page.mouse.dblclick(box["x"] + 250, box["y"] + 400)

    def click_save_boundary_btn(self):
        with allure.step("Click Save Boundary"):
            self.page.wait_for_selector(self.locators["add_boundary"]["save_boundary_btn"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_boundary"]["save_boundary_btn"])

    # ── Shared flows ──────────────────────────────────────────────────
    def _flow_add_farmer(self, name="pramod", field_agent="Ram User"):
        self.click_farmer_list()
        self.click_add()
        self.click_add_new_farmer()
        self.fill_farmer_name(name)
        self.fill_mobile_number(self.generate_mobile_number())
        self.click_business_unit_field()
        self.click_business_unit_option()
        self.fill_field_agent(field_agent)
        self.click_save_farmer()

    def _flow_navigate_farmer_farms(self):
        self.click_farmer_list()
        self.click_farmer()

    def _flow_add_crop(self):
        self.click_crop_input()
        self.click_crop_option()
        self.click_crop_duration_input()
        self.click_crop_duration_option()
        self.click_sowing_date_input()
        self.click_sowing_date_option()
        self.click_save_crop()

    def _flow_add_boundary(self):
        self.click_map_canvas()
        self.draw_polygon()
        self.click_save_boundary_btn()

    def _flow_pending_farms_to_menu(self):
        self.click_pending_farms_btn()
        self.click_type_dropdown()
        self.click_only_farms_option()
        self.click_search_in_pending_farms()
        self.click_three_dots_pending_farm()