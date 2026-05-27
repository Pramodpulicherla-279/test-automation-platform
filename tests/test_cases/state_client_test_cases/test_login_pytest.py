import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_click
# from utils.ocr_utils import extract_text_with_coordinates
import json
import os
# from selenium.common.exceptions import WebDriverException
# from utils.wait_utils import find_and_click


@allure.epic("Login Flow")
@allure.feature("Authentication")
class TestLogin:

    @allure.story("Successful Login")
    @allure.title("Verify user can login with valid credentials")
    def test_login_success(self, driver):
        # This list will store the details of each step in the test flow
        test_flow_steps = []

         # Compute project root (…/test-automation-platform)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "state_client.json")

        with open(locators_path, 'r') as f:
            xpaths = json.load(f)

        
        # --- Locators ---
        login_screen_xpaths = xpaths.get("login_screen", {})
        language_next_xpath = login_screen_xpaths.get("next_button_language_login")
        allow_picture_button_xpath = login_screen_xpaths.get("allow_picture_button")
        allow_location_button_xpath = login_screen_xpaths.get("allow_location_button")
        allow_audio_button_xpath = login_screen_xpaths.get("allow_audio_button")
        allow_notifications_button_xpath = login_screen_xpaths.get("allow_notifications_button")
        phone_number_input_xpath = login_screen_xpaths.get("phone_number_input")
        next_button_login_xpath = login_screen_xpaths.get("next_button_login")
        verify_button_login_xpath = login_screen_xpaths.get("verify_button_login")

        try:     
        
            with allure.step("1. Allow picture"):
                if not smart_click(driver, "While using the app (allow picture)", allow_picture_button_xpath, "While using the app"):
                    pytest.fail("Could not find or click the 'Allow picture' button.")
                test_flow_steps.append({"step": "Allow picture permission", "status": "Success"})
            
            with allure.step("2. Allow location"):
                if not smart_click(driver, "While using (allow location)", allow_location_button_xpath, "While using"):
                    pytest.fail("Could not find or click the 'Allow location' button.")
                test_flow_steps.append({"step": "Allow location permission", "status": "Success"})

            with allure.step("3. Allow audio"):
                if not smart_click(driver, "While using the app (allow audio)", allow_audio_button_xpath, "While using the app"):
                    pytest.fail("Could not find or click the 'Allow audio' button.")
                test_flow_steps.append({"step": "Allow audio permission", "status": "Success"})

            with allure.step("4. Allow notifications"):
                if not smart_click(driver, "Allow notifications", allow_notifications_button_xpath, "Allow"):
                    pytest.fail("Could not find or click the 'Allow notifications' button.")
                test_flow_steps.append({"step": "Allow notifications permission", "status": "Success"})

            with allure.step("5. Next button on language selection screen"):
                # Use smart_click for robust finding (XPath -> DOM Text -> OCR)
                if not smart_click(driver, "Next Button (Language)", language_next_xpath, "Next"):
                    pytest.fail("Could not find or click the 'Next button on language selection' button.")
                test_flow_steps.append({"step": "Click Next button on language selection", "status": "Success"})
            
            with allure.step("6. Enter phone number"):
                phone_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, phone_number_input_xpath))
                )
                phone_input.clear()
                phone_input.send_keys("8179605618")
                test_flow_steps.append({"step": "Enter valid phone number", "status": "Success", "value": "8179605618"})
            
            with allure.step("7. Tap next button"):
                if not smart_click(driver, "Next (login)", next_button_login_xpath, "Next"):
                    pytest.fail("Could not find or click the 'Next' button after entering phone number.")
                test_flow_steps.append({"step": "Click Next after entering phone number", "status": "Success"})
            
            with allure.step("8. Wait for OTP and verify"):
                time.sleep(20)
                
                if not smart_click(driver, "Verify (login)", verify_button_login_xpath, "Verify"):
                    pytest.fail("Could not find or click the 'Verify' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

        finally:
            # Save the captured flow to a file
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/login_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)
