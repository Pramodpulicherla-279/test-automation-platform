import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_click, wait_for_otp, wait_for_element, wait_and_click, wait_for_otp_filled
import json
import os
from selenium.common.exceptions import WebDriverException
import sys
sys.dont_write_bytecode = True

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
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

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
            with allure.step("1. Next button on language selection screen"):
                # Use smart_click for robust finding (XPath -> DOM Text -> OCR)
                if not smart_click(driver, "Next Button (Language)", language_next_xpath, "Next"):
                    pytest.fail("Could not find or click the 'Next button on language selection' button.")
                test_flow_steps.append({"step": "Click Next button on language selection", "status": "Success"})

            
            with allure.step("2. Allow picture"):
                if not smart_click(driver, "While using the app (allow picture)", allow_picture_button_xpath, "While using the app"):
                    pytest.fail("Could not find or click the 'Allow picture' button.")
                test_flow_steps.append({"step": "Allow picture permission", "status": "Success"})
            
            with allure.step("3. Allow location"):
                if not smart_click(driver, "While using (allow location)", allow_location_button_xpath, "While using"):
                    pytest.fail("Could not find or click the 'Allow location' button.")
                test_flow_steps.append({"step": "Allow location permission", "status": "Success"})

            with allure.step("4. Allow audio"):
                if not smart_click(driver, "While using the app (allow audio)", allow_audio_button_xpath, "While using the app"):
                    pytest.fail("Could not find or click the 'Allow audio' button.")
                test_flow_steps.append({"step": "Allow audio permission", "status": "Success"})
            
            with allure.step("5. Allow notifications"):
                if not smart_click(driver, "Allow notifications", allow_notifications_button_xpath, "Allow"):
                    pytest.fail("Could not find or click the 'Allow notifications' button.")
                test_flow_steps.append({"step": "Allow notifications permission", "status": "Success"})

            with allure.step("6. Enter phone number"):
                phone_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, phone_number_input_xpath))
                )
                phone_input.clear()
                phone_input.send_keys("7660852538")
                test_flow_steps.append({"step": "Enter valid phone number", "status": "Success", "value": "9618574550"})

            with allure.step("7. Tap next button"):
                if not smart_click(driver, "Next (login)", next_button_login_xpath, "Next"):
                    pytest.fail("Could not find or click the 'Next' button after entering phone number.")
                test_flow_steps.append({"step": "Click Next after entering phone number", "status": "Success"})
            
            with allure.step("8. Wait for OTP and verify"):
                wait_for_otp_filled(driver, "//android.widget.EditText[contains(@resource-id,'otp_input')]", expected_length=4)
                assert smart_click(driver, "Verify", verify_button_login_xpath, "Verify")
                test_flow_steps.append({"step": "Verify OTP", "status": "Success"})

            # with allure.step("9. Verify Dashboard"):
            #    print("[INFO] Waiting for dashboard screen...")
            #    dashboard = None
            #    timeout = 15  # seconds
            #    poll_interval = 2
            #    start_time = time.time()
            #    ocr_dashboard_found = False
               
            #    while time.time() - start_time < timeout:
            #        # FIX: Use text that ACTUALLY appears on the dashboard (from your logs)
            #        found_element, used_ocr = smart_find_element(
            #            driver,
            #            name="dashboard_title",
            #            xpath=dashboard_title_xpath, 
            #            fallback_text="Pramod" 
            #        )
                   
            #        if found_element or used_ocr:
            #            print(f"[INFO] Dashboard found via {'OCR' if used_ocr else 'XPath'}.")
            #            dashboard = found_element
            #            ocr_dashboard_found = used_ocr 
            #            break
                   
            #        # Manual Fallback: Check for robust keywords
            #        try:
            #            screenshot_path = "screenshots/dashboard_check.png"
            #            os.makedirs("screenshots", exist_ok=True)
            #            driver.save_screenshot(screenshot_path)
            #            ocr_text = extract_text_with_coordinates(screenshot_path)
                       
            #            detected_texts = [item.get("text", "").lower() for item in ocr_text]
                       
            #            # FIX: Removed "pramod" and "agent". Only allow distinct dashboard elements.
            #            valid_keywords = ["total records", "business unit"]
                       
            #            matched_keyword = next((k for k in valid_keywords if any(k in t for t in detected_texts)), None)
                       
            #            if matched_keyword:
            #                ocr_dashboard_found = True
            #                print(f"[INFO] Dashboard detected by OCR. Keyword found: '{matched_keyword}'")
            #                break
            #        except Exception as e:
            #            print(f"[WARN] OCR Check failed: {e}")
                       
            #        time.sleep(poll_interval)
               
            #    if dashboard is None and not ocr_dashboard_found:
            #        # Capture failure screenshot
            #        allure.attach(driver.get_screenshot_as_png(), name="Dashboard Missing", attachment_type=allure.attachment_type.PNG)
            #        pytest.fail(f"❌ Login Verification Failed: Dashboard did not appear within {timeout} seconds.")
               
            #    test_flow_steps.append({"step": "Dashboard Verified", "status": "Success"})


        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/login_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)