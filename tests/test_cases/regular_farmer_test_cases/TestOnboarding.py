# import time
# import allure
# import pytest
# from appium.webdriver.common.appiumby import AppiumBy
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# # from utils.wait_utils import smart_find_element
# from utils.ocr_utils import extract_text_with_coordinates
# from selenium.common.exceptions import TimeoutException 
# import json
# import os
# # Import our new utility function
# from utils.wait_utils import find_and_click
# from utils.wait_utils import scroll_and_click_by_text_robust
# from utils.touch_utils import tap_at_coordinates

# @allure.epic("Onboarding Flow")
# @allure.feature("Onboarding")
# class TestOnboarding:

#     @allure.story("Successful Onboarding")
#     @allure.title("Verify user can complete onboarding with valid information")
#     def test_onboarding_success(self, driver):
#         test_flow_steps = []

#         project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
#         locators_path = os.path.join(project_root, "tests", "locators", "elements.json")

#         with open(locators_path, 'r') as f:
#             xpaths = json.load(f)

#         # --- Locators ---
#         dashboard_xpaths = xpaths.get("dashboard_screen", {})
#         add_farm_button_xpath = dashboard_xpaths.get("add_farm_button")
#         determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
#         draw_on_map_button_xpath = determine_boundary_modal_xpaths.get("draw_on_map_button")
#         add_farm_xpaths = xpaths.get("add_farm_screen", {})
#         farm_name_input_xpath = add_farm_xpaths.get("farm_name_input")
#         acreage_input_xpath = add_farm_xpaths.get("acreage_input")
#         submit_button_xpath = add_farm_xpaths.get("submit_button")
#         add_crop_xpaths = xpaths.get("add_crop_screen", {})
#         direct_sowing_xpaths = add_crop_xpaths.get("direct_sowing", {})
#         sowing_date_input_xpath = direct_sowing_xpaths.get("sowing_date_input")
#         harvest_date_input_xpath = direct_sowing_xpaths.get("harvest_date_input")
#         transplanted_xpaths = add_crop_xpaths.get("transplanted", {})
#         draw_on_map_xpaths = xpaths.get("draw_on_map_screen", {})
#         add_crop_screen_xpaths = xpaths.get("add_crop_screen", {})
#         crop_name_input_xpath = add_crop_screen_xpaths.get("crop_name_input")
#         crop_name_item_xpath = add_crop_screen_xpaths.get("crop_name_item")
#         ok_button_xpath = add_crop_screen_xpaths.get("ok_button")
#         submit_crop_button_xpath = add_crop_screen_xpaths.get("submit_crop_button")
#         bengal_gram_crop_xpath = add_crop_screen_xpaths.get("bengal_gram_crop")
#         skip_button_xpath = add_crop_screen_xpaths.get("skip_button")
#         determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
#         draw_on_map_button_xpath = determine_boundary_modal_xpaths.get("draw_on_map_button")
#         draw_on_map_screen_xpaths = xpaths.get("draw_on_map_screen", {})
#         save_approve_button_xpath = draw_on_map_screen_xpaths.get("save_approve_button")
#         direct_sowing_button_xpath = add_crop_screen_xpaths.get("direct_sowing_button")


#         try:
#             with allure.step("1. Click on the 'Add Farm' button"):
#                 if not find_and_click(driver, AppiumBy.XPATH, add_farm_button_xpath, "Add Farm"):
#                     pytest.fail("Could not find or click the 'Add Farm' button.")
#                 test_flow_steps.append({"step": "Click Add Farm button", "status": "Success"})

#             with allure.step("2. Click on the 'Draw on Map' button"):
#                 if not find_and_click(driver, AppiumBy.XPATH, draw_on_map_button_xpath, "Draw on Map"):
#                     pytest.fail("Could not find or click the 'Draw on Map' button.")
#                 test_flow_steps.append({"step": "Click Draw on Map button", "status": "Success"})

#             with allure.step("3. Submit Farm Details"):
#                 if not find_and_click(driver, AppiumBy.XPATH, submit_button_xpath, "Submit"):
#                     pytest.fail("Could not find or click the 'Submit' button.")
#                 test_flow_steps.append({"step": "Click Submit Farm Details", "status": "Success"})
            
#             with allure.step("4. Click on 'Crop Name' input field"):
#                 time.sleep(10)
#                 # This opens the dropdown
#                 if not find_and_click(driver, AppiumBy.XPATH, crop_name_input_xpath, "Crop Name"):
#                     pytest.fail("Could not find or click the 'Crop Name' input field.")
#                 test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

#             with allure.step("4. Click on 'Crop Name' list item in dropdown"):
#                 time.sleep(10)
#                 if not find_and_click(driver, AppiumBy.XPATH, crop_name_item_xpath, "Beetroot"):
#                     pytest.fail("Could not find or click the 'Crop Name item' input field.")
#                 test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})

#             # with allure.step("5. Select 'Bengal Gram' from the dropdown using coordinates"):
#             #     # These coordinates are just an example. You must find the correct ones for your app.
#             #     # Let's assume the center of "Bengal Gram" is at x=540, y=850.
#             #     bengal_gram_x = 555
#             #     bengal_gram_y = 1582
            
#             #     if not tap_at_coordinates(driver, bengal_gram_x, bengal_gram_y):
#             #         pytest.fail("Failed to tap at the specified coordinates for 'Bengal Gram'.")
                
#             #     test_flow_steps.append({"step": "Select Crop 'Bengal Gram'", "status": "Success"})
#             with allure.step("4. Click on 'Direct Sowing' list item in dropdown"):
#                 time.sleep(10)
#                 if not find_and_click(driver, AppiumBy.XPATH, direct_sowing_button_xpath, "Direct sowing"):
#                     pytest.fail("Could not find or click the 'Direct sowing Button' input field.")
#                 test_flow_steps.append({"step": "Click Direct sowing Button", "status": "Success"})

#             with allure.step("6. Sowing Date input"):
#                 if not find_and_click(driver, AppiumBy.XPATH, sowing_date_input_xpath, "Sowing Date"):
#                     pytest.fail("Could not find or click the 'Sowing Date' input field.")
#                 test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

#             with allure.step("7. OK button on calendar"):
#                 if not find_and_click(driver, AppiumBy.XPATH, ok_button_xpath, "OK"):
#                     pytest.fail("Could not find or click the 'OK' button.")
#                 test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

#             with allure.step("8. Submit Crop button"):
#                 if not find_and_click(driver, AppiumBy.XPATH, submit_crop_button_xpath, "Submit"):
#                     pytest.fail("Could not find or click the 'Submit' button.")
#                 test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})

#             with allure.step("9. Add Boundary - Draw On Map"):
#                 time.sleep(10)  # Wait for the map to load
#                 coordinates = [
#                     (390, 760),  # Top-left corner
#                     (690, 760),  # Top-right corner
#                     (690, 1160), # Bottom-right corner
#                     (390, 1160), # Bottom-left corner
#                     (390, 760),  # Closing the box
#                     (390, 760)   # Closing the box
#                 ]
#                 for coord in coordinates:
#                     driver.tap([coord], 100)  # duration=100ms per tap
#                 test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})
            
#             with allure.step("10. Save & Approve Boundary"):
#                 if not find_and_click(driver, AppiumBy.XPATH, save_approve_button_xpath, "Save & Approve Boundary"):
#                     pytest.fail("Could not find or click the 'Save & Approve Boundary' button.")
#                 test_flow_steps.append({"step": "Click Save & Approve Boundary", "status": "Success"})

#         finally:
#             os.makedirs("test-flows", exist_ok=True)
#             with open("test-flows/onboarding_flow_success.json", "w") as f:
#                 json.dump(test_flow_steps, f, indent=4)

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
from utils.wait_utils import find_and_click


@allure.epic("Onboarding Flow")
@allure.feature("Authentication")
class TestOnboarding:

    @allure.story("Successful Onboarding")
    @allure.title("Onboarding the farms and crops")
    def test_onboarding_success(self, driver):
        # This list will store the details of each step in the test flow
        test_flow_steps = []

         # Compute project root (…/test-automation-platform)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, 'r') as f:
            xpaths = json.load(f)

        
        # # --- Locators ---
        # login_screen_xpaths = xpaths.get("login_screen", {})
        dashboard_xpaths = xpaths.get("dashboard", {})
        # language_next_xpath = login_screen_xpaths.get("next_button_language_login")
        # allow_picture_button_xpath = login_screen_xpaths.get("allow_picture_button")
        # allow_location_button_xpath = login_screen_xpaths.get("allow_location_button")
        # allow_audio_button_xpath = login_screen_xpaths.get("allow_audio_button")
        # allow_notifications_button_xpath = login_screen_xpaths.get("allow_notifications_button")
        # phone_number_input_xpath = login_screen_xpaths.get("phone_number_input")
        # next_button_login_xpath = login_screen_xpaths.get("next_button_login")
        # verify_button_login_xpath = login_screen_xpaths.get("verify_button_login")
        # dashboard_title_xpath = dashboard_xpaths.get("dashboard_title")   
        dashboard_xpaths = xpaths.get("dashboard_screen", {})
        add_farm_button_xpath = dashboard_xpaths.get("add_farm_button")
        determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
        draw_on_map_button_xpath = determine_boundary_modal_xpaths.get("draw_on_map_button")
        add_farm_screen_xpaths = xpaths.get("add_farm_screen", {})
        submit_button_xpath = add_farm_screen_xpaths.get("submit_button")
        # add_crop_screen_xpaths = xpaths.get("add_crop_screen", {})
        # skip_button_xpath = add_crop_screen_xpaths.get("skip_button")
        # draw_on_map_screen_xpaths = xpaths.get("draw_on_map_screen", {})
        # save_approve_button_xpath = draw_on_map_screen_xpaths.get("save_approve_button")
        # back_arrow_icon_xpath = draw_on_map_screen_xpaths.get("back_arrow_icon")
        

        try:

            with allure.step("1. add farm"):
                # time.sleep(20)
                if not find_and_click(driver, AppiumBy.XPATH, add_farm_button_xpath, "Add farm"):
                    pytest.fail("Could not find or click the 'Verify' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
            with allure.step("2. draw on map button"):
                time.sleep(3)
                if not find_and_click(driver, AppiumBy.XPATH, draw_on_map_button_xpath, "Verify"):
                    pytest.fail("Could not find or click the 'Verify' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

            with allure.step("3. submit button in add farm"):
                time.sleep(3)
                if not find_and_click(driver, AppiumBy.XPATH, submit_button_xpath, "Verify"):
                    pytest.fail("Could not find or click the 'Verify' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
        finally:
            # Save the captured flow to a file
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/onboarding_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

