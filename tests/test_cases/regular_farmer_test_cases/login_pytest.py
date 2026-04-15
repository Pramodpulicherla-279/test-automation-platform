import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_find_element
from utils.ocr_utils import extract_text_with_coordinates
import json
import os
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput, Interaction
from utils.api_validator import APIValidator

@allure.epic("Login Flow")
@allure.feature("Authentication")
class TestLogin:

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize API validator for this test class"""
        self.api = APIValidator(base_url="http://localhost:8000")
        yield

    @allure.story("Successful Login")
    @allure.title("Verify user can login with valid credentials")
    def test_login_success(self, driver):
        # This list will store the details of each step in the test flow
        test_flow_steps = []

         # Compute project root (…/test-automation-platform)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, 'r') as f:
            xpaths = json.load(f)

        # --- Locators ---
        login_screen_xpaths = xpaths.get("login_screen", {})
        dashboard_xpaths = xpaths.get("dashboard", {})
        language_next_xpath = login_screen_xpaths.get("next_button_language_login")
        allow_picture_button_xpath = login_screen_xpaths.get("allow_picture_button")
        allow_location_button_xpath = login_screen_xpaths.get("allow_location_button")
        allow_audio_button_xpath = login_screen_xpaths.get("allow_audio_button")
        allow_notifications_button_xpath = login_screen_xpaths.get("allow_notifications_button")
        phone_number_input_xpath = login_screen_xpaths.get("phone_number_input")
        next_button_login_xpath = login_screen_xpaths.get("next_button_login")
        verify_button_login_xpath = login_screen_xpaths.get("verify_button_login")
        dashboard_title_xpath = dashboard_xpaths.get("dashboard_title")   

        try:
            with allure.step("1. Language Selection"):
                el, used_ocr = smart_find_element(driver, "language_next", language_next_xpath, fallback_text="Next")
                if el: el.click()
                elif not used_ocr: pytest.fail("Could not find Language Next button")
                test_flow_steps.append({"step": "Language Selection", "status": "Success"})

            with allure.step("2. Allow picture"):
                el, used_ocr = smart_find_element(driver, "allow_picture", allow_picture_button_xpath, fallback_text="While using")
                if el: el.click()
                elif not used_ocr: pytest.fail("Could not find Allow Picture button")
                test_flow_steps.append({"step": "Allow picture permission", "status": "Success"})
            
            with allure.step("3. Allow location"):
                el, used_ocr = smart_find_element(driver, "allow_location", allow_location_button_xpath, fallback_text="While using")
                if el: el.click()
                elif not used_ocr: pytest.fail("Could not find Allow Location button")
                test_flow_steps.append({"step": "Allow location permission", "status": "Success"})

            with allure.step("4. Allow audio"):
                el, used_ocr = smart_find_element(driver, "allow_audio", allow_audio_button_xpath, fallback_text="While using")
                if el: el.click()
                elif not used_ocr: pytest.fail("Could not find Allow Audio button")
                test_flow_steps.append({"step": "Allow audio permission", "status": "Success"})
            
            with allure.step("5. Allow notifications"):
                el, used_ocr = smart_find_element(driver, "allow_notifications", allow_notifications_button_xpath, fallback_text="Allow")
                if el: el.click()
                elif not used_ocr: pytest.fail("Could not find Allow Notifications button")
                test_flow_steps.append({"step": "Allow notifications permission", "status": "Success"})

            with allure.step("6. Enter phone number"):
                # For input fields, we prefer the Element loop. OCR click handles focus, but sending keys is tricky.
                phone_input, used_ocr = smart_find_element(driver, "phone_input", phone_number_input_xpath, fallback_text="Phone")
                
                if phone_input:
                    phone_input.clear()
                    phone_input.send_keys("7660852538")
                elif used_ocr:
                    # If OCR clicked it, it should be focused. Try general keyboard input.
                    actions = ActionBuilder(driver)
                    actions.pointer_action.click() # Ensure touch
                    actions.key_action.send_keys("7660852538")
                    actions.perform()
                else:
                    pytest.fail("Could not access Phone Number input")

                test_flow_steps.append({"step": "Enter valid phone number", "status": "Success", "value": "7660852538"})
            
            with allure.step("7. Tap next button"):
                el, used_ocr = smart_find_element(driver, "next_button", next_button_login_xpath, fallback_text="Next")
                if el: el.click()
                elif not used_ocr: pytest.fail("Could not find Next button")
                test_flow_steps.append({"step": "Click Next after entering phone number", "status": "Success"})
            
            with allure.step("8. Wait for OTP and verify"):
                time.sleep(20) # Wait for human/system OTP
                el, used_ocr = smart_find_element(driver, "verify_button", verify_button_login_xpath, fallback_text="Verify")
                if el: el.click()
                elif not used_ocr: pytest.fail("Could not find Verify button")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

            with allure.step("9. Verify session via API"):
                """Verify that user is authenticated by checking backend API"""
                self.api.assert_endpoint(
                    method="GET",
                    endpoint="/api/auth/verify",
                    expected_status=200,
                    description="Verify user session is active after login"
                )
                test_flow_steps.append({"step": "Verify session via API", "status": "Success"})

            with allure.step("10. Verify user profile via API"):
                """Verify that user profile is accessible"""
                self.api.assert_endpoint(
                    method="GET",
                    endpoint="/api/user/profile",
                    expected_status=200,
                    description="Get user profile from backend"
                )
                test_flow_steps.append({"step": "Verify user profile via API", "status": "Success"})

            with allure.step("11. Validate all API tests passed"):
                """Assert that all API validation checks passed"""
                summary = self.api.get_summary()
                assert summary["failed"] == 0, f"API validation failed: {summary}"
                test_flow_steps.append({"step": "All API validations passed", "status": "Success"})

            with allure.step("12. Verify Dashboard"):
               print("[INFO] Waiting for dashboard screen...")
               dashboard = None
               timeout = 15  # seconds
               poll_interval = 2
               start_time = time.time()
               ocr_dashboard_found = False
               
               while time.time() - start_time < timeout:
                   found_element, used_ocr = smart_find_element(
                       driver,
                       name="dashboard_title",
                       xpath=dashboard_title_xpath, 
                       fallback_text="Pramod" 
                   )
                   
                   if found_element or used_ocr:
                       print(f"[INFO] Dashboard found via {'OCR' if used_ocr else 'XPath/DOM'}.")
                       dashboard = found_element
                       ocr_dashboard_found = used_ocr 
                       break
                   
                   # Manual Fallback: Check for robust keywords (Only if smart_find_element completely failed)
                   try:
                       screenshot_path = "screenshots/dashboard_check.png"
                       os.makedirs("screenshots", exist_ok=True)
                       driver.save_screenshot(screenshot_path)
                       ocr_text = extract_text_with_coordinates(screenshot_path)
                       
                       detected_texts = [item.get("text", "").lower() for item in ocr_text]
                       
                       valid_keywords = ["total records", "business unit"]
                       
                       matched_keyword = next((k for k in valid_keywords if any(k in t for t in detected_texts)), None)
                       
                       if matched_keyword:
                           ocr_dashboard_found = True
                           print(f"[INFO] Dashboard detected by OCR. Keyword found: '{matched_keyword}'")
                           break
                   except Exception as e:
                       print(f"[WARN] OCR Check failed: {e}")
                       
                   time.sleep(poll_interval)
               
               if dashboard is None and not ocr_dashboard_found:
                   # Capture failure screenshot
                   allure.attach(driver.get_screenshot_as_png(), name="Dashboard Missing", attachment_type=allure.attachment_type.PNG)
                   pytest.fail(f"❌ Login Verification Failed: Dashboard did not appear within {timeout} seconds.")
               
               test_flow_steps.append({"step": "Dashboard Verified", "status": "Success"})

        finally:
            # Save the captured flow to a file
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/login_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)