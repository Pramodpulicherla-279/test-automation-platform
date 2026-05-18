import json
import os
import allure
from pathlib import Path


class Field_Update_Page:
    def __init__(self, page):
        self.page     = page
        self.a_locators = self.a_load_locators()
        self.b_locators = self.b_load_locators()
        os.makedirs("screenshots", exist_ok=True)

    def a_load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "onboarding.json"
        with open(path) as f:
            return json.load(f)

    def b_load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "field_updates.json"
        with open(path) as f:
            return json.load(f)

    def _shot(self, name: str):
        path = f"screenshots/{name}.png"
        self.page.screenshot(path=path)
        with open(path, "rb") as f:
            allure.attach(f.read(), name=name, attachment_type=allure.attachment_type.PNG)

    # ── Atomic actions ────────────────────────────────────────────────
    def open_hamburger_menu(self):
        with allure.step("Open hamburger menu"):
            self.page.wait_for_selector(self.a_locators["hamburger_menu_icon"], state="visible")
            self.page.click(self.a_locators["hamburger_menu_icon"])

    def click_current_season(self):
        with allure.step("Click Current Season"):
            self.page.locator(self.a_locators["current_season"]).wait_for(state="visible", timeout=10_000)
            self.page.wait_for_timeout(1200)
            self.page.click(self.a_locators["current_season"])

    def click_farmer_list(self):
        with allure.step("Click Farmer List"):
            self.page.wait_for_selector(self.a_locators["farmer_list"], state="visible")
            self.page.click(self.a_locators["farmer_list"])

    def click_farmer(self):
        with allure.step("Click Farmer row"):
            self.page.wait_for_selector(self.a_locators["select_farmer"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.a_locators["select_farmer"])

    def click_three_dots(self):
        with allure.step("Click Three Dots"):
            self.page.wait_for_selector(self.b_locators["three_dots"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.b_locators["three_dots"])

    def click_overview_option(self):
        with allure.step("Click Overview option"):
            self.page.wait_for_selector(self.b_locators["overview_option"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.b_locators["overview_option"])

    def click_field_updates_tab(self):
        with allure.step("Click Field Updates tab"):
            self.page.wait_for_selector(self.b_locators["field_updates_tab"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.b_locators["field_updates_tab"])

    def click_add_field_update_btn(self):
        with allure.step("Click Add Field Update button"):
            self.page.wait_for_selector(self.b_locators["add_field_update_btn"], state="visible")
            self.page.click(self.b_locators["add_field_update_btn"])
 
    def click_date_input(self):
        with allure.step("Click Date input"):
            self.page.wait_for_selector(self.b_locators["date_input"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.b_locators["date_input"])

    def upload_files(self, file_paths):
        with allure.step("Upload media files"):
            files = [str(Path(file).resolve()) for file in file_paths]
            self.page.set_input_files(
                self.b_locators["upload_files_btn"],
                files
            )
            print(f"Uploaded files: {files}", flush=True)
    
    def click_date_option(self, date_value: str = "2026-05-01"):
        with allure.step("Date option clicked"):
            print("Opening flatpickr via JS...", flush=True)
            self.page.evaluate(f"""
                () => {{
        
                    const input = document.querySelector('#updateDateInput');
        
                    if (!input)
                        throw new Error('Date input not found');
        
                    // Open calendar
                    input.click();
        
                    // Wait for flatpickr instance
                    if (!input._flatpickr)
                        throw new Error('Flatpickr instance not found');
        
                    // Set date directly
                    input._flatpickr.setDate('{date_value}', true);
        
                    // Trigger events
                    input.dispatchEvent(
                        new Event('input', {{ bubbles: true }})
                    );
        
                    input.dispatchEvent(
                        new Event('change', {{ bubbles: true }})
                    );
        
                    // Close calendar
                    input._flatpickr.close();
                }}
            """)
        
            self.page.wait_for_timeout(1000)
            value = self.page.input_value("#updateDateInput")
            print(f"Selected Date: {value}", flush=True)
        
            if not value:
                raise Exception("Date was not selected")
        
    def fill_notes_input(self, notes_str):
        with allure.step("Fill Notes input"):
            self.page.wait_for_selector(self.b_locators["general_remarks_input"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.fill(self.b_locators["general_remarks_input"], notes_str)

    def click_save_updates(self):
        with allure.step("Click Save Updates"):
            self.page.wait_for_selector(self.b_locators["save_btn"], state="visible")
            self.page.click(self.b_locators["save_btn"])

    def verify_farmer_details_text(self):
        with allure.step("Verify Farmer Details text"):
            text = self.page.locator("text=Farmer Details").first
            self.page.wait_for_timeout(40000)
            text.wait_for(state="visible")
            assert text.is_visible(), \
                "Farmer Details text is NOT visible"

    def click_cross_icon(self):
        with allure.step("Click Cross icon to close modal"):
            close_btn = self.page.locator(
                self.b_locators["cross_icon"]
            ).last
            close_btn.wait_for(state="visible", timeout=15000)
            self.page.wait_for_timeout(4000)
            close_btn.click(force=True)

    def _flow_navigate_farmer_farms(self):
        self.click_farmer_list()
        self.click_farmer()
