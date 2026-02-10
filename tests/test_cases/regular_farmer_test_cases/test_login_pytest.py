import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_find_element, smart_click
from utils.ocr_utils import extract_text_with_coordinates
import json
import os
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import find_and_click


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
        dashboard_xpaths = xpaths.get("dashboard_screen", {})
        add_farm_button_xpath = dashboard_xpaths.get("add_farm_button")
        determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
        draw_on_map_button_xpath = determine_boundary_modal_xpaths.get("draw_on_map_button")
        add_farm_screen_xpaths = xpaths.get("add_farm_screen", {})
        submit_button_xpath = add_farm_screen_xpaths.get("submit_button")
        add_crop_screen_xpaths = xpaths.get("add_crop_screen", {})
        skip_button_xpath = add_crop_screen_xpaths.get("skip_button")
        draw_on_map_screen_xpaths = xpaths.get("draw_on_map_screen", {})
        save_approve_button_xpath = draw_on_map_screen_xpaths.get("save_approve_button")
        back_arrow_icon_xpath = draw_on_map_screen_xpaths.get("back_arrow_icon")

        try:
            # with allure.step("1. Next button on language selection screen"):
            #     next_button_language_login, used_ocr = smart_find_element(
            #         driver, name="next_button_language_login", xpath=language_next_xpath, fallback_text="Next"
            #     )
            #     if next_button_language_login:
            #         next_button_language_login.click()
            #         test_flow_steps.append({"step": "Click Next on language screen", "status": "Success"})
            #     else:
            #         raise Exception("Next button in language selection not found")
            
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
                test_flow_steps.append({"step": "Enter valid phone number", "status": "Success", "value": "7660852538"})
            
            with allure.step("7. Tap next button"):
                if not smart_click(driver, "Next (login)", next_button_login_xpath, "Next"):
                    pytest.fail("Could not find or click the 'Next' button after entering phone number.")
                test_flow_steps.append({"step": "Click Next after entering phone number", "status": "Success"})
            
            with allure.step("8. Wait for OTP and verify"):
                time.sleep(20)
                if not smart_click(driver, "Verify (login)", verify_button_login_xpath, "Verify"):
                    pytest.fail("Could not find or click the 'Verify' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

            with allure.step("9. Verify Dashboard"):
               print("[INFO] Waiting for dashboard screen...")
               dashboard = None
               timeout = 15  # seconds
               poll_interval = 2
               start_time = time.time()
               ocr_dashboard_found = False
               
               while time.time() - start_time < timeout:
                   # FIX: Use text that ACTUALLY appears on the dashboard (from your logs)
                   found_element, used_ocr = smart_find_element(
                       driver,
                       name="dashboard_title",
                       xpath=dashboard_title_xpath, 
                       fallback_text="Pramod" 
                   )
                   
                   if found_element or used_ocr:
                       print(f"[INFO] Dashboard found via {'OCR' if used_ocr else 'XPath'}.")
                       dashboard = found_element
                       ocr_dashboard_found = used_ocr 
                       break
                   
                   # Manual Fallback: Check for robust keywords
                   try:
                       screenshot_path = "screenshots/dashboard_check.png"
                       os.makedirs("screenshots", exist_ok=True)
                       driver.save_screenshot(screenshot_path)
                       ocr_text = extract_text_with_coordinates(screenshot_path)
                       
                       detected_texts = [item.get("text", "").lower() for item in ocr_text]
                       
                       # FIX: Removed "pramod" and "agent". Only allow distinct dashboard elements.
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

            # with allure.step("10. add farm"):
            #     # time.sleep(20)
            #     if not find_and_click(driver, AppiumBy.XPATH, add_farm_button_xpath, "Add farm"):
            #         pytest.fail("Could not find or click the 'Verify' button.")
            #     test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
            # with allure.step("11. draw on map button"):
            #     time.sleep(3)
            #     if not find_and_click(driver, AppiumBy.XPATH, draw_on_map_button_xpath, "Verify"):
            #         pytest.fail("Could not find or click the 'Verify' button.")
            #     test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

            # with allure.step("12. submit button in add farm"):
            #     time.sleep(3)
            #     if not find_and_click(driver, AppiumBy.XPATH, submit_button_xpath, "Verify"):
            #         pytest.fail("Could not find or click the 'Verify' button.")
            #     test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})


            
                
            # with allure.step("2. Allow picture"):
            #     allow_picture_button, used_ocr = smart_find_element(
            #         driver, name="allow_picture_button", xpath=allow_picture_button_xpath, fallback_text="While using the app"
            #     )
            #     if allow_picture_button:
            #         allow_picture_button.click()
            #         test_flow_steps.append({"step": "Allow picture permission", "status": "Success"})
            #     else:
            #         raise Exception("Allow picture button not found")

            # with allure.step("3. Allow location"):
            #     allow_location_button, used_ocr = smart_find_element(
            #         driver, name="allow_location_button", xpath=allow_location_button_xpath, fallback_text="While using"
            #     )
            #     if allow_location_button:
            #         allow_location_button.click()
            #         test_flow_steps.append({"step": "Allow location permission", "status": "Success"})
            #     else:
            #         raise Exception("Allow Location button not found")
            
            # with allure.step("4. Allow audio"):
            #     allow_audio_button, used_ocr = smart_find_element(
            #         driver, name="allow_audio_button", xpath=allow_audio_button_xpath, fallback_text="While using the app"
            #     )
            #     if allow_audio_button:
            #         allow_audio_button.click()
            #         test_flow_steps.append({"step": "Allow audio permission", "status": "Success"})
            #     else:
            #         raise Exception("Allow audio button not found")

            # with allure.step("5. Allow notifications"):
            #     allow_notifications_button, used_ocr = smart_find_element(
            #         driver, name="allow_notifications_button", xpath=allow_notifications_button_xpath, fallback_text="Allow"
            #     )
            #     if allow_notifications_button:
            #         allow_notifications_button.click()
            #         test_flow_steps.append({"step": "Allow notifications permission", "status": "Success"})
            #     else:
            #         raise Exception("Allow Notifications button not found")

            # with allure.step("6. Enter phone number"):
            #     phone_input, used_ocr = smart_find_element(
            #         driver, name="phone_number_input", xpath=phone_number_input_xpath, fallback_text="Phone"
            #     )
            #     if phone_input:
            #         phone_input.clear()
            #         phone_input.send_keys("9896000099")
            #         test_flow_steps.append({"step": "Enter valid phone number", "status": "Success", "value": "9896000099"})
            #     else:
            #         raise Exception("Phone input field not found")

            # with allure.step("7. Tap next button"):
            #     next_button, used_ocr = smart_find_element(
            #         driver, name="next_button_login", xpath=next_button_login_xpath, fallback_text="Next"
            #     )
            #     if next_button:
            #         next_button.click()
            #         test_flow_steps.append({"step": "Click Next after entering phone number", "status": "Success"})
            #     else:
            #         raise Exception("Next button not found")

            # with allure.step("8. Wait for OTP and verify"):
            #     time.sleep(3)  # Waiting for OTP
            #     verify_button, used_ocr = smart_find_element(
            #         driver, name="verify_button_login", xpath=verify_button_login_xpath, fallback_text="Verify"
            #     )
            #     if verify_button:
            #         verify_button.click()
            #         test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            #     else:
            #         raise Exception("Verify button not found")
                
            # with allure.step("9. click on the 'Add Farm' button"):
            #     time.sleep(10)
            #     add_farm_button, used_ocr = smart_find_element(
            #         driver, name="add_farm_button", xpath=add_farm_button_xpath, fallback_text="Add Farm"
            #     )
            #     if add_farm_button:
            #         add_farm_button.click()
            #         test_flow_steps.append({"step": "Click Add Farm button", "status": "Success"})

            #     else:
            #         raise Exception("Add Farm button not found")
                
            # with allure.step("10. Click Draw on Map button"):
            #     draw_on_map_button, used_ocr = smart_find_element(
            #         driver, name="draw_on_map_button", xpath=draw_on_map_button_xpath, fallback_text="Draw on Map"
            #     )
            #     if draw_on_map_button:
            #         draw_on_map_button.click()
            #         test_flow_steps.append({"step": "Click Draw on Map button", "status": "Success"})
            #         # allure.attach("Onboarding successful", name="Result", attachment_type=allure.attachment_type.TEXT)
            #     else:
            #         raise Exception("Draw on Map button not found")
            
            # with allure.step("11. Submit Farm Details"):
            #     submit_button, used_ocr = smart_find_element(
            #         driver, name="submit_button", xpath=submit_button_xpath, fallback_text="Submit"
            #     )
            #     if submit_button:
            #         submit_button.click()
            #         test_flow_steps.append({"step": "Click Submit Farm Details", "status": "Success"})
            #     else:
            #         raise Exception("Submit button not found")
            
            # with allure.step("12. Skip Add Crop Screen"):
            #     skip_button, used_ocr = smart_find_element(
            #         driver, name="skip_button", xpath=skip_button_xpath, fallback_text="Skip"
            #     )
            #     if skip_button:
            #         skip_button.click()
            #         test_flow_steps.append({"step": "Click Skip Add Crop Screen", "status": "Success"})
            #         allure.attach("Login & Add Farm Done", name="Result", attachment_type=allure.attachment_type.TEXT)

            #     else:
            #         raise Exception("Skip button not found")
            
            # with allure.step("13. Skip the Boundary (Android Back)"):
            #     try:
            #         driver.back()  # Simulate Android back button
            #         test_flow_steps.append({"step": "Android Back Button Pressed", "status": "Success"})
            #     except WebDriverException as e:
            #         allure.attach(driver.page_source, name="Page Source", attachment_type=allure.attachment_type.XML)
            #         allure.attach(driver.get_screenshot_as_png(), name="Screenshot", attachment_type=allure.attachment_type.PNG)
            #         raise Exception(f"Android back action failed: {str(e)}")
                
            # with allure.step("13. Skip the Boundary"):
            #     back_arrow_icon, used_ocr = smart_find_element(
            #         driver, name="back_arrow_icon", xpath=back_arrow_icon_xpath, fallback_text="Back"
            #     )
            #     if back_arrow_icon:
            #         back_arrow_icon.click()
            #         test_flow_steps.append({"step": "Click Back Arrow Icon", "status": "Success"})
            #     else:
            #         raise Exception("Back Arrow Icon not found")
            # with allure.step("9. Verify dashboard appears"):
            #     time.sleep(10)
            #     dashboard, used_ocr = smart_find_element(
            #         driver, name="dashboard_title", xpath=dashboard_title_xpath, fallback_text="Dashboard"
            #     )
            #     assert dashboard is not None or used_ocr, "Dashboard not found after login"
            #     test_flow_steps.append({"step": "Verify dashboard is displayed", "status": "Success"})
            #     allure.attach("Login successful", name="Result", attachment_type=allure.attachment_type.TEXT)

        finally:
            # Save the captured flow to a file
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/login_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)
