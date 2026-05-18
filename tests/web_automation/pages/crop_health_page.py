import json
import os
import allure
from pathlib import Path


class Crop_Health_Page:
    def __init__(self, page):
        self.page = page
        self.a_locators = self.a_load_locators()
        self.c_locators = self.c_load_locators()
        os.makedirs("screenshots", exist_ok=True)

    # ---------------------------------------------------
    # Load Locator Files
    # ---------------------------------------------------

    def a_load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "onboarding.json"
        with open(path) as f:
            return json.load(f)
        
    def c_load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "crop_health.json"
        with open(path) as f:
            return json.load(f)

    # ---------------------------------------------------
    # Screenshot Utility
    # ---------------------------------------------------

    def _shot(self, name: str):
        path = f"screenshots/{name}.png"
        self.page.screenshot(path=path)
        with open(path, "rb") as f:
            allure.attach(
                f.read(), name=name, attachment_type=allure.attachment_type.PNG
            )

    # ---------------------------------------------------
    # Navigation Flow
    # ---------------------------------------------------

    def open_hamburger_menu(self):
        with allure.step("Open hamburger menu"):
            self.page.wait_for_selector(self.a_locators["hamburger_menu_icon"], state="visible")
            self.page.wait_for_timeout(4000)
            self.page.click(self.a_locators["hamburger_menu_icon"])

    def click_historical_tab(self):
        with allure.step("Click Historical tab"):
            self.page.locator(self.a_locators["sidebar"]["historical_tab"]).wait_for(state="visible", timeout=10000)
            self.page.wait_for_timeout(4000)
            self.page.click(self.a_locators["sidebar"]["historical_tab"])

    def click_farmer_list(self):
        with allure.step("Click Farmer List"):
            self.page.wait_for_selector(self.a_locators["sidebar"]["historical_farmers"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.a_locators["sidebar"]["historical_farmers"])

    def click_farmer(self):
        with allure.step("Click Farmer row"):
            self.page.wait_for_selector(
                self.a_locators["ram_farmer"], state="visible"
            )
            self.page.wait_for_timeout(2000)
            self.page.click(self.a_locators["ram_farmer"])
    # ---------------------------------------------------
    # Crop Health Navigation
    # ---------------------------------------------------

    def click_crop_health_button(self):
        with allure.step("Click Crop Health Button"):
            self.page.wait_for_selector(
                self.c_locators["crop_health_btn"], state="visible"
            )
            self.page.wait_for_timeout(3000)
            self.page.click(self.c_locators["crop_health_btn"])

    def wait_for_crop_health_page_load(self):
        with allure.step(
            "Wait for Crop Health page to load"
        ):
            # Wait for network requests
            self.page.wait_for_load_state(
                "networkidle"
            )
            # Wait for unique element
            self.page.wait_for_selector(
                self.c_locators["data_1"]["crop_name"],
                state="visible",
                timeout=30000
            )
            # Optional small stabilization
            self.page.wait_for_timeout(2000)

    # ---------------------------------------------------
    # Generic Get Text Method
    # ---------------------------------------------------

    def get_text(self, locator):
        self.page.wait_for_selector(locator, state="visible")
        return self.page.locator(locator).inner_text().strip()

    # ---------------------------------------------------
    # Crop Health Data
    # ---------------------------------------------------

    def get_crop_health_data(self):
        with allure.step("Get Crop Health screen data"):
            return {
                "crop_name": self.get_text(self.c_locators["data_1"]["crop_name"]),
                "farmer_name": self.get_text(self.c_locators["data_1"]["farmer_name"]),
                "crop_id": self.get_text(self.c_locators["data_1"]["crop_id"]),
                "acreage": self.get_text(self.c_locators["data_1"]["acreage"]),
                "sowing_date": self.get_text(self.c_locators["data_1"]["sowing_date"]),
                "last_clear_image": self.get_text(self.c_locators["data_1"]["last_clear_image"]),
                "last_update_date": self.get_text(self.c_locators["data_1"]["last_update_date"]),
                "caution": self.get_text(self.c_locators["data_1"]["caution_percentage"]),
                "warnings": self.get_text(self.c_locators["data_1"]["warning_percentage"]),
                "stressed": self.get_text(self.c_locators["data_1"]["stressed_percentage"]),
                "severely_stressed": self.get_text(self.c_locators["data_1"]["severely_stressed_percentage"]),
                "crop_stage": self.get_text(self.c_locators["data_1"]["crop_stage"]),
                "wind_speed": self.get_text(self.c_locators["data_1"]["wind_speed"]),
                "date": self.get_text(self.c_locators["data_1"]["date"]),
            }

    # ---------------------------------------------------
    # Common Navigation Flow
    # ---------------------------------------------------

    def navigate_to_crop_health_screen(self):
        # self.open_hamburger_menu()
        self.click_historical_tab()
        self.click_farmer_list()
        self.click_farmer()
        self.click_crop_health_button()
