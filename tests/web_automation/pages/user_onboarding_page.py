import json
import os
import random
import allure
from pathlib import Path


class UserOnboardingPage:
    def __init__(self, page):
        self.page     = page
        self.locators = self._load_locators()
        os.makedirs("screenshots", exist_ok=True)

    def _load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "user_onboarding.json"
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
    

    ### Add user flow ###
    def open_hamburger_menu(self):
        with allure.step("Open hamburger menu"):
            self.page.wait_for_selector(self.locators["hamburger_menu_icon"], state="visible")
            self.page.click(self.locators["hamburger_menu_icon"])

    def click_organization(self):
        with allure.step("Click Organization"):
             self.page.locator(self.locators["organization"]).wait_for(state="visible", timeout=1200)
             self.page.wait_for_timeout(1200)
             self.page.click(self.locators["organization"])
 
    
    def click_users(self):
        with allure.step("Click Users"):
             self.page.wait_for_selector(self.locators["users"], state="visible")
             self.page.click(self.locators["users"])
     

    def click_add(self):
        with allure.step("Click Add Button"):
          self.page.wait_for_selector(self.locators["add_button"], state="visible")
          self.page.click(self.locators["add_button"])
        

    def click_add_single_user(self):
        with allure.step("Click Add Single User"):
             self.page.wait_for_selector(self.locators["add_single_user"], state="visible")
             self.page.click(self.locators["add_single_user"])
            
    def fill_user_name(self, name: str):
        with allure.step(f"Fill User Name → '{name}'"):
             el = self.page.locator(self.locators["add_user"]["user_name"])
             el.wait_for(state="visible")
             el.fill(name)
    
    def fill_mobile_number(self, mobile_number: str):
        with allure.step(f"Fill Mobile → {mobile_number}"):
            el = self.page.locator(self.locators["add_user"]["mobile_number"])
            el.wait_for(state="visible")
            el.fill(mobile_number)

    def click_business_unit_field(self):
        with allure.step("Click Business Unit field"):
            self.page.wait_for_selector(self.locators["add_user"]["business_unit_input"], state="visible")
            self.page.wait_for_timeout(2000)
            self.page.click(self.locators["add_user"]["business_unit_input"])
 
    def click_business_unit_option(self):
        with allure.step("Select Business Unit option"):
            self.page.wait_for_selector(self.locators["add_user"]["business_unit_option"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.locators["add_user"]["business_unit_option"])

    def click_user_role_field(self):
        with allure.step("Click User Role field"):
            self.page.wait_for_selector(self.locators["add_user"]["user_role_input"], state="visible")
            self.page.wait_for_timeout(3000)
            self.page.click(self.locators["add_user"]["user_role_input"])

    def click_user_role_option(self, role):
        with allure.step(f"Select User Role option: {role}"):
             role_locator = self.page.get_by_text(role, exact=True)
             role_locator.wait_for(state="visible")
             self.page.wait_for_timeout(2000)
             role_locator.click()
             print(f"Selected role: {role}", flush=True)

    def click_save(self):
        with allure.step("Click Save Button"):
            self.page.wait_for_selector(self.locators["add_user"]["save_btn"], state="visible")
            self.page.click(self.locators["add_user"]["save_btn"])

    def _fill_number_input(self):
        self.fill_mobile_number(self.generate_mobile_number())
