import time
import allure
import pytest
import json
import os
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction

# --- IMPORT CUSTOM UTILITIES ---
# Ensure these files exist in tests/utils/ as created previously
from tests.utils.touch_utils import tap_at_coordinates, perform_scroll
from tests.utils.wait_utils import scroll_to_find
from tests.utils.ui_actions import smart_click, smart_send_keys, smart_select_dropdown

@allure.epic("Login Flow")
@allure.feature("Authentication")
class TestLogin:

    # --- CONFIGURATION ---
    LOGIN_METHOD = "EMAIL"  # Options: "EMAIL" or "PHONE"

    @allure.story("Login User")
    @allure.title("Verify user can login successfully")
    def test_login(self, driver):
        
        print(f"\n--- STARTING LOGIN TEST WITH METHOD: {self.LOGIN_METHOD} ---\n")
        
        test_flow_steps = []

        # --- Load JSON Locators ---
        # Tries to find 'regular_client.json' in various folders
        filename = 'regular_client.json'
        possible_paths = [
            os.path.join('locators', filename),
            os.path.join('tests', 'locators', filename),
            os.path.join(os.getcwd(), 'locators', filename),
        ]
        json_path = next((p for p in possible_paths if os.path.exists(p)), None)
        if not json_path: raise FileNotFoundError(f"Could not find '{filename}'")

        with open(json_path, 'r') as f: data = json.load(f)

        # Extract specific screen data
        login_xpaths = data.get("login_screen", {})
        login_coords = data.get("coordinates", {}).get("login_screen", {})

        try:
            # ========================================================
            # PART 1: LANGUAGE & PRE-LOGIN PERMISSIONS
            # ========================================================
            
            with allure.step("1. Language Selection"):
                key = "next_button_language_login"
                # smart_click handles looking up XPath or using Coordinates if XPath fails
                smart_click(driver, login_xpaths.get(key), login_coords.get(key), key)

            with allure.step("2. Allow Notifications"):
                key = "allow_notifications_button"
                smart_click(driver, login_xpaths.get(key), login_coords.get(key), key, timeout=3)

            # ========================================================
            # PART 2: AUTHENTICATION (EMAIL OR PHONE)
            # ========================================================
            login_performed = False
            
            if self.LOGIN_METHOD == "PHONE":
                # Add Phone logic here if needed
                login_performed = True
                pass

            elif self.LOGIN_METHOD == "EMAIL":
                login_performed = True
                with allure.step("3a. Select Email Tab"):
                    smart_click(driver, login_xpaths.get("tab_email_login"), login_coords.get("tab_email_login"), "Email Tab")
                
                with allure.step("3b. Enter Email"):
                    smart_send_keys(driver, login_xpaths.get("email_input"), "fa1@yopmail.com", "Email Input")
                
                with allure.step("3c. Enter Password"):
                    smart_send_keys(driver, login_xpaths.get("password_input"), "Fa1@2025", "Password Input")
                
                with allure.step("3d. Click Submit"):
                    key = "submit_login_button"
                    if not smart_click(driver, login_xpaths.get(key), login_coords.get(key), key):
                        raise Exception("Submit button failed")

            if not login_performed: 
                raise ValueError("Login method not implemented")

            # ========================================================
            # PART 3: POST-LOGIN PERMISSIONS
            # ========================================================
            permissions_to_handle = [
                ("allow_picture_button", "Allow Picture"),
                ("allow_location_button", "Allow Location"),
                ("allow_audio_button", "Allow Audio")
            ]
            
            for key, desc in permissions_to_handle:
                with allure.step(f"4. Post-Login Permission: {desc}"):
                    smart_click(driver, login_xpaths.get(key), login_coords.get(key), key, timeout=3)
            
            # Success Logging
            allure.attach("Login Successful", name="Result", attachment_type=allure.attachment_type.TEXT)
            test_flow_steps.append({"step": "Login", "status": "Success"})
            print("Login flow completed!")
            time.sleep(10)

        except Exception as e:
            # Failure Handling - Take Screenshot
            print(f"Test Failed: {e}")
            try: 
                allure.attach(driver.get_screenshot_as_png(), name="Login_Failure_Screenshot", attachment_type=allure.attachment_type.PNG)
            except: 
                pass
            raise e

        finally:
            # Save flow results
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/login_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)