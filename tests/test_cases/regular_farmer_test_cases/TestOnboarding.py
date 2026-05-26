import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from utils.wait_utils import smart_find_element
from utils.ocr_utils import extract_text_with_coordinates
from selenium.common.exceptions import TimeoutException 
import json
import os
# Import our new utility function
from utils.wait_utils import find_and_click
from utils.wait_utils import scroll_and_click_by_text_robust
from utils.touch_utils import tap_at_coordinates

@allure.epic("Onboarding Flow")
@allure.feature("Onboarding")
class TestOnboarding:
 
    @allure.story("Successful Onboarding")
    @allure.title("Verify user can complete onboarding with valid information")
    def test_onboarding_success(self, driver):
        test_flow_steps = []

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "tests", "locators", "elements.json")

        with open(locators_path, 'r') as f:
            xpaths = json.load(f)

           

#         # --- Locators ---
        dashboard_xpaths = xpaths.get("dashboard_screen", {})
        # add_farm_button_xpath = dashboard_xpaths.get("add_farm_button")
        # determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
        # draw_on_map_button_xpath = determine_boundary_modal_xpaths.get("draw_on_map_button")
        # add_farm_xpaths = xpaths.get("add_farm_screen", {})
        # farm_name_input_xpath = add_farm_xpaths.get("farm_name_input")
        # acreage_input_xpath = add_farm_xpaths.get("acreage_input")
        # submit_button_xpath = add_farm_xpaths.get("submit_button")
        # add_crop_xpaths = xpaths.get("add_crop_screen", {})
        # direct_sowing_xpaths = add_crop_xpaths.get("direct_sowing", {})
        # sowing_date_input_xpath = direct_sowing_xpaths.get("sowing_date_input")
        # harvest_date_input_xpath = direct_sowing_xpaths.get("harvest_date_input")
        # transplanted_xpaths = add_crop_xpaths.get("transplanted", {})
        # draw_on_map_xpaths = xpaths.get("draw_on_map_screen", {})
        # add_crop_screen_xpaths = xpaths.get("add_crop_screen", {})
        # crop_name_input_xpath = add_crop_screen_xpaths.get("crop_name_input")
        # crop_name_item_xpath = add_crop_screen_xpaths.get("crop_name_item")
        # ok_button_xpath = add_crop_screen_xpaths.get("ok_button")
        # submit_crop_button_xpath = add_crop_screen_xpaths.get("submit_crop_button")
        # bengal_gram_crop_xpath = add_crop_screen_xpaths.get("bengal_gram_crop")
        # skip_button_xpath = add_crop_screen_xpaths.get("skip_button")
        # determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
        # draw_on_map_button_xpath = determine_boundary_modal_xpaths.get("draw_on_map_button")
        # draw_on_map_screen_xpaths = xpaths.get("draw_on_map_screen", {})
        # save_approve_button_xpath = draw_on_map_screen_xpaths.get("save_approve_button")
        # direct_sowing_button_xpath = add_crop_screen_xpaths.get("direct_sowing_button")
        #


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
from utils.wait_utils import smart_find_element
from utils.ocr_utils import extract_text_with_coordinates
import json
import os
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import find_and_click, smart_click
from utils.wait_utils import find_and_click, smart_click
import sys
sys.dont_write_bytecode = True


@allure.epic("Onboarding Flow")
@allure.feature("Authentication")
class TestOnboarding:

    @pytest.fixture(scope="class", autouse=True)
    def _load_locators_once(self, request):
        """Loads locators once per test class and attaches them to the class."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, "r", encoding="utf-8") as f:
            xpaths = json.load(f)

        # Attach commonly used locators to the class
        dashboard_xpaths = xpaths.get("dashboard_screen", {})
        add_crop_screen_xpaths = xpaths.get("add_crop_screen", {})
        determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
        add_farm_screen_xpaths = xpaths.get("add_farm_screen", {})
        determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
        add_farm_screen_xpaths = xpaths.get("add_farm_screen", {})
        add_crop_xpaths = xpaths.get("add_crop_screen", {})
        direct_sowing_xpaths = add_crop_xpaths.get("direct_sowing", {})
        draw_on_map_screen_xpaths = xpaths.get("draw_on_map_screen", {})
        pending_farms_xpaths = xpaths.get("pending_farms", {})
        three_dots_xpaths = xpaths.get("three_dots_xpath", {})
        pending_farms_xpaths = xpaths.get("pending_farms", {})
        three_dots_xpaths = xpaths.get("three_dots_xpath", {})

        draw_on_map_button_xpath = determine_boundary_modal_xpaths.get("draw_on_map_button")
        submit_button_xpath = add_farm_screen_xpaths.get("submit_button")
        crop_name_item_xpath = add_crop_screen_xpaths.get("crop_name_item")
        
        


        request.cls.xpaths = xpaths  # optional: full dict if you need it later
        request.cls.add_farm_button_xpath = dashboard_xpaths.get("add_farm_button")
        request.cls.draw_on_map_button_xpath = determine_boundary_modal_xpaths.get("draw_on_map_button")
        request.cls.submit_button_xpath = add_farm_screen_xpaths.get("submit_button")
        request.cls.crop_name_item_xpath = add_crop_screen_xpaths.get("crop_name_item")
        request.cls.crop_name_input_xpath = add_crop_screen_xpaths.get("crop_name_input")
        request.cls.sowing_date_input_xpath = direct_sowing_xpaths.get("sowing_date_input")
        request.cls.ok_button_xpath = add_crop_screen_xpaths.get("ok_button")
        request.cls.submit_crop_button_xpath = add_crop_screen_xpaths.get("submit_crop_button")
        request.cls.update_crop_button_xpath = direct_sowing_xpaths.get("update_crop_button")
        request.cls.update_crop_button_xpath = direct_sowing_xpaths.get("update_crop_button")
        request.cls.save_approve_button_xpath = draw_on_map_screen_xpaths.get("save_approve_button")
        request.cls.skip_button_xpath = add_crop_screen_xpaths.get("skip_button")
        request.cls.intercrop_name_xpath = direct_sowing_xpaths.get("intercrop_name")
        request.cls.intercrop_sowingdate_xpath = direct_sowing_xpaths.get("intercrop_sowingdate")
        request.cls.three_dots_xpath = dashboard_xpaths.get("three_dots")
        request.cls.hamburger_menu_xpath = dashboard_xpaths.get("hamburger_menu")
        request.cls.pending_farms_tab_xpath = dashboard_xpaths.get("pending_farms_tab")


        request.cls.type_dropdown_xpath = pending_farms_xpaths.get("type_dropdown")
        request.cls.pending_farms_tab_xpath = pending_farms_xpaths.get("pending_farms_tab")
        request.cls.active_dropdown_xpath = pending_farms_xpaths.get("active_dropdown")
        request.cls.historical_xpath = pending_farms_xpaths.get("historical")
        request.cls.cross_button_xpath = pending_farms_xpaths.get("cross_button")
        request.cls.all_dropdown_xpath = pending_farms_xpaths.get("all_dropdown")
        request.cls.only_farms_xpath = pending_farms_xpaths.get("only_farms_xpath")
        request.cls.all_tab_xpath = pending_farms_xpaths.get("all_tab_xpath")
        request.cls.farms_with_no_crops_xpath = pending_farms_xpaths.get("farms_with_no_crops_xpath")
        request.cls.farms_with_no_boundary_xpath = pending_farms_xpaths.get("farms_with_no_boundary_xpath")

        request.cls.Overview_xpath = three_dots_xpaths.get("Overview")
        request.cls.edit_farm_xpath = three_dots_xpaths.get("edit_farm")
        request.cls.delete_farm_xpath = three_dots_xpaths.get("delete_farm")
        request.cls.add_crop_xpath = three_dots_xpaths.get("add_crop")
        request.cls.edit_crop_xpath = three_dots_xpaths.get("edit_crop")
        request.cls.delete_crop_xpath = three_dots_xpaths.get("delete_crop")
        request.cls.add_boundary_xpath = three_dots_xpaths.get("add_boundary")
        request.cls.edit_boundary_xpath = three_dots_xpaths.get("edit_boundary")
        
    
        request.cls.three_dots_xpath = dashboard_xpaths.get("three_dots")
        request.cls.hamburger_menu_xpath = dashboard_xpaths.get("hamburger_menu")
        request.cls.pending_farms_tab_xpath = dashboard_xpaths.get("pending_farms_tab")


        request.cls.type_dropdown_xpath = pending_farms_xpaths.get("type_dropdown")
        request.cls.pending_farms_tab_xpath = pending_farms_xpaths.get("pending_farms_tab")
        request.cls.active_dropdown_xpath = pending_farms_xpaths.get("active_dropdown")
        request.cls.historical_xpath = pending_farms_xpaths.get("historical")
        request.cls.cross_button_xpath = pending_farms_xpaths.get("cross_button")
        request.cls.all_dropdown_xpath = pending_farms_xpaths.get("all_dropdown")
        request.cls.only_farms_xpath = pending_farms_xpaths.get("only_farms_xpath")
        request.cls.all_tab_xpath = pending_farms_xpaths.get("all_tab_xpath")
        request.cls.farms_with_no_crops_xpath = pending_farms_xpaths.get("farms_with_no_crops_xpath")
        request.cls.farms_with_no_boundary_xpath = pending_farms_xpaths.get("farms_with_no_boundary_xpath")

        request.cls.Overview_xpath = three_dots_xpaths.get("Overview")
        request.cls.edit_farm_xpath = three_dots_xpaths.get("edit_farm")
        request.cls.delete_farm_xpath = three_dots_xpaths.get("delete_farm")
        request.cls.add_crop_xpath = three_dots_xpaths.get("add_crop")
        request.cls.edit_crop_xpath = three_dots_xpaths.get("edit_crop")
        request.cls.delete_crop_xpath = three_dots_xpaths.get("delete_crop")
        request.cls.add_boundary_xpath = three_dots_xpaths.get("add_boundary")
        request.cls.edit_boundary_xpath = three_dots_xpaths.get("edit_boundary")
        
    
        


    def _android_back(self, driver) -> bool:
        """Navigate back on Android (driver.back() + fallback to KEYCODE_BACK)."""
        try:
            driver.back()
            return True
        except WebDriverException:
            pass
        except Exception:
            pass    
        # Fallback for Android-specific drivers
        try:
            driver.press_keycode(4)  # KEYCODE_BACK
            return True
        except Exception:
            return False

    @allure.story("Successful Onboarding")
    # @allure.title("add farm")
    # def test_addfarm(self, driver):
    #     # This list will store the details of each step in the test flow
    #     test_flow_steps = []
    # @allure.title("add farm")
    # def test_addfarm(self, driver):
    #     # This list will store the details of each step in the test flow
    #     test_flow_steps = []

    #     try:
    #     try:

    #         with allure.step("1. add farm"):
    #             # time.sleep(20)
    #             if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
    #         with allure.step("1. add farm"):
    #             # time.sleep(20)
    #             if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map button' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map button' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'submit' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'submit' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("4. Android back"):
    #             if not self._android_back(driver):
    #                 pytest.fail("Failed to navigate back on Android.")
    #             test_flow_steps.append({"step": "Android back", "status": "Success"})
    #         with allure.step("4. Android back"):
    #             if not self._android_back(driver):
    #                 pytest.fail("Failed to navigate back on Android.")
    #             test_flow_steps.append({"step": "Android back", "status": "Success"})
            
    #     finally:
    #         # Save the captured flow to a file
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/onboarding_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)
    #     finally:
    #         # Save the captured flow to a file
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/onboarding_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)
                
    # @allure.title("Onboarding the farms and crops")
    # def test_addfarm_addcrop_success(self, driver):
    #     test_flow_steps = []
    # @allure.title("Onboarding the farms and crops")
    # def test_addfarm_addcrop_success(self, driver):
    #     test_flow_steps = []

    #     try:
    #     try:

    #         with allure.step("1. add farm"):
    #             # time.sleep(20)
    #             if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
    #         with allure.step("1. add farm"):
    #             # time.sleep(20)
    #             if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
    #         with allure.step("4. Click on 'Crop Name' input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
    #                 pytest.fail("Could not find or click the 'Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})
    #         with allure.step("4. Click on 'Crop Name' input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
    #                 pytest.fail("Could not find or click the 'Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

    #         with allure.step("5. Click on 'Crop Name' list item in dropdown"):
    #             time.sleep(2)  # small settle time for dropdown animation
    #             if not smart_click(
    #                 driver,
    #                 "select crop from dropdown (OCR)",
    #                 self.crop_name_item_xpath,   # still tried first (safe), then OCR
    #                 "Apple",
    #                 screenshot_path="screenshots/crop_dropdown.png",
    #                 force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
    #                 ocr_attempts=3,
    #             ):
    #                 pytest.fail("Could not select the crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
    #         with allure.step("5. Click on 'Crop Name' list item in dropdown"):
    #             time.sleep(2)  # small settle time for dropdown animation
    #             if not smart_click(
    #                 driver,
    #                 "select crop from dropdown (OCR)",
    #                 self.crop_name_item_xpath,   # still tried first (safe), then OCR
    #                 "Apple",
    #                 screenshot_path="screenshots/crop_dropdown.png",
    #                 force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
    #                 ocr_attempts=3,
    #             ):
    #                 pytest.fail("Could not select the crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
            
    #         with allure.step("6. Click on Inter Crop Name' input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Crop Name input", self.intercrop_name_xpath, "Inter-Crop Name"):
    #                 pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})
    #         with allure.step("6. Click on Inter Crop Name' input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Crop Name input", self.intercrop_name_xpath, "Inter-Crop Name"):
    #                 pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})

    #         with allure.step("7. Click on 'Crop Name' list item in intercrop dropdown"):
    #             time.sleep(2)  # small settle time for dropdown animation
    #             if not smart_click(
    #                 driver,
    #                 "select crop from dropdown (OCR)",
    #                 self.crop_name_item_xpath,   # still tried first (safe), then OCR
    #                 "Beetroot",
    #                 screenshot_path="screenshots/crop_dropdown.png",
    #                 force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
    #                 ocr_attempts=3,
    #             ):
    #                 pytest.fail("Could not select the inter crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})
    #         with allure.step("7. Click on 'Crop Name' list item in intercrop dropdown"):
    #             time.sleep(2)  # small settle time for dropdown animation
    #             if not smart_click(
    #                 driver,
    #                 "select crop from dropdown (OCR)",
    #                 self.crop_name_item_xpath,   # still tried first (safe), then OCR
    #                 "Beetroot",
    #                 screenshot_path="screenshots/crop_dropdown.png",
    #                 force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
    #                 ocr_attempts=3,
    #             ):
    #                 pytest.fail("Could not select the inter crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

    #         with allure.step("8. Intercrop Sowing Date input"):
    #             if not smart_click(driver,  "sowing date input", self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
    #                 pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})
    #         with allure.step("8. Intercrop Sowing Date input"):
    #             if not smart_click(driver,  "sowing date input", self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
    #                 pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

    #         with allure.step("9. OK button on calendar"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not find or click the 'OK' button.")
    #             test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})
    #         with allure.step("9. OK button on calendar"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not find or click the 'OK' button.")
    #             test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

    #         with allure.step("10. Sowing Date input"):
    #             if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
    #                 pytest.fail("Could not find or click the 'Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})
    #         with allure.step("10. Sowing Date input"):
    #             if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
    #                 pytest.fail("Could not find or click the 'Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

    #         with allure.step("11. OK button on calendar"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not find or click the 'OK' button.")
    #             test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})
    #         with allure.step("11. OK button on calendar"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not find or click the 'OK' button.")
    #             test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

    #         with allure.step("12. Submit Crop button"):
    #             if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})
    #         with allure.step("12. Submit Crop button"):
    #             if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})
         
    #         with allure.step("4. Android back"):
    #            if not self._android_back(driver):
    #                pytest.fail("Failed to navigate back on Android.")
    #            test_flow_steps.append({"step": "Android back", "status": "Success"})
    #         with allure.step("4. Android back"):
    #            if not self._android_back(driver):
    #                pytest.fail("Failed to navigate back on Android.")
    #            test_flow_steps.append({"step": "Android back", "status": "Success"})
            
    #     finally:
    #         # Save the captured flow to a file
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/onboarding_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)
    #     finally:
    #         # Save the captured flow to a file
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/onboarding_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)

    # @allure.title("add farm > add crop > add boundary")
    # def test_addfarm_addcrop_addboundary_success(self, driver):
    #     test_flow_steps = []
    #     try:
    #         with allure.step("1. add farm"):
    #             # time.sleep(20)
    #             if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("4. Click on 'Crop Name' input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
    #                 pytest.fail("Could not find or click the 'Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

    #         with allure.step("5. Click on 'Crop Name' list item in dropdown"):
    #             time.sleep(2)  # small settle time for dropdown animation
    #             if not smart_click(
    #                 driver,
    #                 "select crop from dropdown (OCR)",
    #                 self.crop_name_item_xpath,   # still tried first (safe), then OCR
    #                 "Areca",
    #                 screenshot_path="screenshots/crop_dropdown.png",
    #                 force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
    #                 ocr_attempts=3,
    #             ):
    #                 pytest.fail("Could not select the crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
            
    #         with allure.step("6. Click on Inter Crop Name' input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Crop Name input", self.intercrop_name_xpath, "Inter-Crop Name"):
    #                 pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})

    #         with allure.step("7. Click on 'Crop Name' list item in intercrop dropdown"):
    #             time.sleep(2)  # small settle time for dropdown animation
    #             if not smart_click(
    #                 driver,
    #                 "select crop from dropdown (OCR)",
    #                 self.crop_name_item_xpath,   # still tried first (safe), then OCR
    #                 "Beetroot",
    #                 screenshot_path="screenshots/crop_dropdown.png",
    #                 force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
    #                 ocr_attempts=3,
    #             ):
    #                 pytest.fail("Could not select the inter crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

    #         with allure.step("8. Intercrop Sowing Date input"):
    #             if not smart_click(driver,  "sowing date input", self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
    #                 pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

    #         with allure.step("9. OK button on calendar"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not find or click the 'OK' button.")
    #             test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

    #         with allure.step("10. Sowing Date input"):
    #             if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
    #                 pytest.fail("Could not find or click the 'Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

    #         with allure.step("11. OK button on calendar"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not find or click the 'OK' button.")
    #             test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

    #         with allure.step("12. Submit Crop button"):
    #             if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})

    #         with allure.step("13. Add Boundary - Draw On Map"):
    #             time.sleep(10)  # Wait for the map to load
    #             coordinates = [
    #                 (390, 760),  # Top-left corner
    #                 (690, 760),  # Top-right corner
    #                 (690, 1160), # Bottom-right corner
    #                 (390, 1160), # Bottom-left corner
    #                 (390, 760),  # Closing the box
    #                 (390, 760)   # Closing the box
    #             ]
    #             for coord in coordinates:
    #                 driver.tap([coord], 100)  # duration=100ms per tap
    #             test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})
            
    #         with allure.step("14. Save & Approve Boundary"):
    #             if not smart_click(driver, "Save & Approve Boundary", self.save_approve_button_xpath, "Save & Approve Boundary"):
    #                 pytest.fail("Could not find or click the 'Save & Approve Boundary' button.")
    #             test_flow_steps.append({"step": "Click Save & Approve Boundary", "status": "Success"})
            
    #         with allure.step("15. Android back"):
    #            if not self._android_back(driver):
    #                pytest.fail("Failed to navigate back on Android.")
    #            test_flow_steps.append({"step": "Android back", "status": "Success"})
   
    #     finally:
    #        # Save the captured flow to a file
    #        os.makedirs("test-flows", exist_ok=True)
    #        with open("test-flows/onboarding_flow_success.json", "w") as f:
    #            json.dump(test_flow_steps, f, indent=4)

    # @allure.title("add farm > skip crop > add boundary")
    # def test_addfarm_skipcrop_addboundary_success(self, driver):
    #     test_flow_steps = []
    #     try:
    #         with allure.step("1. add farm"):
    #             # time.sleep(20)
    #             if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
    #         with allure.step("4. skip in add crop"):
    #             time.sleep(3)
    #             if not smart_click(driver, "skip (button in add crop)", self.skip_button_xpath, "Skip"):
    #                 pytest.fail("Could not find or click the 'Skip' button.")
    #             test_flow_steps.append({"step": "Click Skip Button", "status": "Success"})

    #         with allure.step("9. Add Boundary - Draw On Map"):
    #             time.sleep(10)  # Wait for the map to load
    #             coordinates = [
    #                 (390, 760),  # Top-left corner
    #                 (690, 760),  # Top-right corner
    #                 (690, 1160), # Bottom-right corner
    #                 (390, 1160), # Bottom-left corner
    #                 (390, 760),  # Closing the box
    #                 (390, 760)   # Closing the box
    #             ]
    #             for coord in coordinates:
    #                 driver.tap([coord], 100)  # duration=100ms per tap
    #             test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})
            
    #         with allure.step("10. Save & Approve Boundary"):
    #             if not smart_click(driver, "Save & Approve Boundary", self.save_approve_button_xpath, "Save & Approve Boundary"):
    #                 pytest.fail("Could not find or click the 'Save & Approve Boundary' button.")
    #             test_flow_steps.append({"step": "Click Save & Approve Boundary", "status": "Success"})
    #     finally:
    #        # Save the captured flow to a file
    #        os.makedirs("test-flows", exist_ok=True)
    #        with open("test-flows/onboarding_flow_success.json", "w") as f:
    #            json.dump(test_flow_steps, f, indent=4)
    
    # @allure.title("add farm > pending farms > add crop > add boundary")
    # def test_addfarm_pendingfarms_addcrop_addboundary_success(self, driver):
    #     test_flow_steps = []
    #     try:
    #         with allure.step("1. add farm"):
    #             # time.sleep(20)
    #             if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
    #         # hamburger menu
    #         # pending farms
    #         # 3 dots
    #         with allure.step("4. Click on 'Crop Name' input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
    #                 pytest.fail("Could not find or click the 'Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

    #         with allure.step("5. Click on 'Crop Name' list item in dropdown"):
    #             time.sleep(2)  # small settle time for dropdown animation
    #             if not smart_click(
    #                 driver,
    #                 "select crop from dropdown (OCR)",
    #                 self.crop_name_item_xpath,   # still tried first (safe), then OCR
    #                 "Areca",
    #                 screenshot_path="screenshots/crop_dropdown.png",
    #                 force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
    #                 ocr_attempts=3,
    #             ):
    #                 pytest.fail("Could not select the crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})

    #         with allure.step("6. Sowing Date input"):
    #             if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
    #                 pytest.fail("Could not find or click the 'Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

    #         with allure.step("7. OK button on calendar"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not find or click the 'OK' button.")
    #             test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

    #         with allure.step("8. Submit Crop button"):
    #             if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})
    #         # add boundary
            
    #     finally:
    #        # Save the captured flow to a file
    #        os.makedirs("test-flows", exist_ok=True)
    #        with open("test-flows/onboarding_flow_success.json", "w") as f:
    #            json.dump(test_flow_steps, f, indent=4)
        
    # @allure.title("add farm > add crop > pending farms > add boundary")
    # def test_addcrop_addfarm_pendingfarms_addboundary_success(self, driver):
    #     test_flow_steps = []
    #     try:
    #         with allure.step("1. add farm"):
    #             # time.sleep(20)
    #             if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
        
    #     finally:
    #        # Save the captured flow to a file
    #        os.makedirs("test-flows", exist_ok=True)
    #        with open("test-flows/onboarding_flow_success.json", "w") as f:
    #            json.dump(test_flow_steps, f, indent=4)




    # add farm > add crop > pending farms > add boundary
    @allure.title("add farm > add crop > pending farms > add boundary")

    def test_addfarm_addcrop_pendingfarms_addboundary_success(self, driver):
        test_flow_steps = []
        try:
            with allure.step("1. add farm"):
                time.sleep(20)
                if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
                    pytest.fail("Could not find or click the 'add farm' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
            with allure.step("2. draw on map button"):
                time.sleep(3)
                if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
                    pytest.fail("Could not find or click the 'draw on map' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

            with allure.step("3. submit button in add farm"):
                time.sleep(3)
                if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
                    pytest.fail("Could not find or click the 'Submit' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
            with allure.step("2. Click on 'Crop Name' input field"):
                time.sleep(10)
                if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
                    pytest.fail("Could not find or click the 'Crop Name' input field.")
                test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

            with allure.step("3. Click on 'Crop Name' list item in dropdown"):
                time.sleep(2)  # small settle time for dropdown animation
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_item_xpath,   # still tried first (safe), then OCR
                    "Areca",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the crop name via OCR.")
                test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
            
            with allure.step("4. Click on Inter Crop Name' input field"):
                time.sleep(10)
                if not smart_click(driver, "Crop Name input", self.intercrop_name_xpath, "Inter-Crop Name"):
                    pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
                test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})

            with allure.step("5. Click on 'Crop Name' list item in intercrop dropdown"):
                time.sleep(2)  # small settle time for dropdown animation
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_item_xpath,   # still tried first (safe), then OCR
                    "Beetroot",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the inter crop name via OCR.")
                test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

            with allure.step("6. Intercrop Sowing Date input"):
                if not smart_click(driver,  "sowing date input", self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
                    pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
                test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

            with allure.step("7. OK button on calendar"):
                if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                    pytest.fail("Could not find or click the 'OK' button.")
                test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

            with allure.step("8. Sowing Date input"):
                if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
                    pytest.fail("Could not find or click the 'Sowing Date' input field.")
                test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

            with allure.step("9. OK button on calendar"):
                if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                    pytest.fail("Could not find or click the 'OK' button.")
                test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

            with allure.step("10. Submit Crop button"):
                if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
                    pytest.fail("Could not find or click the 'Submit' button.")
                test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})

            with allure.step("11. android back"):
                if not self._android_back(driver):
                    pytest.fail("Failed to navigate back on Android.")

                test_flow_steps.append({"step": "Android back", "status": "Success"})

            with allure.step("12.three dots in pending farms"):
                time.sleep(10)
                if not smart_click(driver, "three dots in pending farms", self.three_dots_xpath, "Three Dots in Pending Farms"):
                    pytest.fail("Could not find or click the three dots in pending farms.")
                test_flow_steps.append({"step": "Click three dots in pending farms", "status": "Success"})

            with allure.step("13. Add Boundary - Draw On Map"):
                time.sleep(10)  # Wait for the map to load
                coordinates = [
                    (390, 760),  # Top-left corner
                    (690, 760),  # Top-right corner
                    (690, 1160), # Bottom-right corner
                    (390, 1160), # Bottom-left corner
                    (390, 760),  # Closing the box
                    (390, 760)   # Closing the box
                ]
                for coord in coordinates:
                    driver.tap([coord], 100)  # duration=100ms per tap
                test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})

            with allure.step("14. Save & Approve Boundary"):
                if not smart_click(driver, "Save & Approve Boundary", self.save_approve_button_xpath, "Save & Approve Boundary"):
                    pytest.fail("Could not find or click the 'Save & Approve Boundary' button.")
                test_flow_steps.append({"step": "Click Save & Approve Boundary", "status": "Success"})

            

        
        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/onboarding_flow_success.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)



    @allure.title("add farm > add crop > pending farms > add boundary")

    def test_addfarm_addcrop_pendingfarms_addboundary_success(self, driver):
        test_flow_steps = []
        try:
            with allure.step("1. add farm"):
                time.sleep(20)
                if not smart_click(driver,"Add farm (button in active farms)", self.add_farm_button_xpath, "Add farm"):
                    pytest.fail("Could not find or click the 'add farm' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
            with allure.step("2. draw on map button"):
                time.sleep(3)
                if not smart_click(driver, "Draw on map (button in determine boundary)", self.draw_on_map_button_xpath, "Draw on map"):
                    pytest.fail("Could not find or click the 'draw on map' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

            with allure.step("3. submit button in add farm"):
                time.sleep(3)
                if not smart_click(driver, "Submit (button in add farm)", self.submit_button_xpath, "Submit"):
                    pytest.fail("Could not find or click the 'Submit' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
            with allure.step("2. Click on 'Crop Name' input field"):
                time.sleep(10)
                if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
                    pytest.fail("Could not find or click the 'Crop Name' input field.")
                test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

            with allure.step("3. Click on 'Crop Name' list item in dropdown"):
                time.sleep(2)  # small settle time for dropdown animation
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_item_xpath,   # still tried first (safe), then OCR
                    "Areca",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the crop name via OCR.")
                test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
            
            with allure.step("4. Click on Inter Crop Name' input field"):
                time.sleep(10)
                if not smart_click(driver, "Crop Name input", self.intercrop_name_xpath, "Inter-Crop Name"):
                    pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
                test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})

            with allure.step("5. Click on 'Crop Name' list item in intercrop dropdown"):
                time.sleep(2)  # small settle time for dropdown animation
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_item_xpath,   # still tried first (safe), then OCR
                    "Beetroot",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the inter crop name via OCR.")
                test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

            with allure.step("6. Intercrop Sowing Date input"):
                if not smart_click(driver,  "sowing date input", self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
                    pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
                test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

            with allure.step("7. OK button on calendar"):
                if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                    pytest.fail("Could not find or click the 'OK' button.")
                test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

            with allure.step("8. Sowing Date input"):
                if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
                    pytest.fail("Could not find or click the 'Sowing Date' input field.")
                test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

            with allure.step("9. OK button on calendar"):
                if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                    pytest.fail("Could not find or click the 'OK' button.")
                test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

            with allure.step("10. Submit Crop button"):
                if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
                    pytest.fail("Could not find or click the 'Submit' button.")
                test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})

            with allure.step("11. android back"):
                if not self._android_back(driver):
                    pytest.fail("Failed to navigate back on Android.")

                test_flow_steps.append({"step": "Android back", "status": "Success"})

            with allure.step("12.three dots in pending farms"):
                time.sleep(10)
                if not smart_click(driver, "three dots in pending farms", self.three_dots_xpath, "Three Dots in Pending Farms"):
                    pytest.fail("Could not find or click the three dots in pending farms.")
                test_flow_steps.append({"step": "Click three dots in pending farms", "status": "Success"})

            with allure.step("13. Add Boundary - Draw On Map"):
                time.sleep(10)  # Wait for the map to load
                coordinates = [
                    (390, 760),  # Top-left corner
                    (690, 760),  # Top-right corner
                    (690, 1160), # Bottom-right corner
                    (390, 1160), # Bottom-left corner
                    (390, 760),  # Closing the box
                    (390, 760)   # Closing the box
                ]
                for coord in coordinates:
                    driver.tap([coord], 100)  # duration=100ms per tap
                test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})

            with allure.step("14. Save & Approve Boundary"):
                if not smart_click(driver, "Save & Approve Boundary", self.save_approve_button_xpath, "Save & Approve Boundary"):
                    pytest.fail("Could not find or click the 'Save & Approve Boundary' button.")
                test_flow_steps.append({"step": "Click Save & Approve Boundary", "status": "Success"})

            

        
        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/onboarding_flow_success.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)



    # active farms > edit crop
    @allure.title("active farms > edit crop")
    def test_activefarms_editcrop(self, driver):
        test_flow_steps = []
        try:
             #click on three dots 
             with allure.step("1. Click on existing farm three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in active farms", self.three_dots_xpath, "Three Dots in Active Farms"):
                    pytest.fail("Could not find or click the three dots in active farms.")
                test_flow_steps.append({"step": "Click three dots in active farms", "status": "Success"})

             with allure.step("2. Click on 'Crop Name' input field"):
                time.sleep(10)
                if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
                    pytest.fail("Could not find or click the 'Crop Name' input field.")
                test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

             with allure.step("3. Click on 'Crop Name' list item in dropdown"):
                time.sleep(2)  # small settle time for dropdown animation
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_item_xpath,   # still tried first (safe), then OCR
                    "Areca",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the crop name via OCR.")
                test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
            
                with allure.step("4. Click on Inter Crop Name' input field"):
                    time.sleep(10)
                    if not smart_click(driver, "Crop Name input", self.intercrop_name_xpath, "Inter-Crop Name"):
                        pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
                    test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})

                with allure.step("5. Click on 'Crop Name' list item in intercrop dropdown"):
                    time.sleep(2)  # small settle time for dropdown animation
                    if not smart_click(
                        driver,
                        "select crop from dropdown (OCR)",
                        self.crop_name_item_xpath,   # still tried first (safe), then OCR
                        "Beetroot",
                        screenshot_path="screenshots/crop_dropdown.png",
                        force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                        ocr_attempts=3,
                    ):
                        pytest.fail("Could not select the inter crop name via OCR.")
                    test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

                with allure.step("6. Intercrop Sowing Date input"):
                    if not smart_click(driver,  "sowing date input", self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
                        pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
                    test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

                with allure.step("7. OK button on calendar"):
                    if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                        pytest.fail("Could not find or click the 'OK' button.")
                    test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

                with allure.step("8. Sowing Date input"):
                    if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
                        pytest.fail("Could not find or click the 'Sowing Date' input field.")
                    test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

                with allure.step("9. OK button on calendar"):
                    if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                        pytest.fail("Could not find or click the 'OK' button.")
                    test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

                with allure.step("10. Submit Crop button"):
                    if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
                        pytest.fail("Could not find or click the 'Submit' button.")
                    test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})



            
        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/onboarding_flow_success.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)

    @allure.title("active farms > edit crop")
    def test_activefarms_editcrop(self, driver):
        test_flow_steps = []
        try:
             #click on three dots 
             with allure.step("1. Click on existing farm three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in active farms", self.three_dots_xpath, "Three Dots in Active Farms"):
                    pytest.fail("Could not find or click the three dots in active farms.")
                test_flow_steps.append({"step": "Click three dots in active farms", "status": "Success"})

             with allure.step("2. Click on 'Crop Name' input field"):
                time.sleep(10)
                if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
                    pytest.fail("Could not find or click the 'Crop Name' input field.")
                test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

             with allure.step("3. Click on 'Crop Name' list item in dropdown"):
                time.sleep(2)  # small settle time for dropdown animation
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_item_xpath,   # still tried first (safe), then OCR
                    "Areca",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the crop name via OCR.")
                test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
            
                with allure.step("4. Click on Inter Crop Name' input field"):
                    time.sleep(10)
                    if not smart_click(driver, "Crop Name input", self.intercrop_name_xpath, "Inter-Crop Name"):
                        pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
                    test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})

                with allure.step("5. Click on 'Crop Name' list item in intercrop dropdown"):
                    time.sleep(2)  # small settle time for dropdown animation
                    if not smart_click(
                        driver,
                        "select crop from dropdown (OCR)",
                        self.crop_name_item_xpath,   # still tried first (safe), then OCR
                        "Beetroot",
                        screenshot_path="screenshots/crop_dropdown.png",
                        force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                        ocr_attempts=3,
                    ):
                        pytest.fail("Could not select the inter crop name via OCR.")
                    test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

                with allure.step("6. Intercrop Sowing Date input"):
                    if not smart_click(driver,  "sowing date input", self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
                        pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
                    test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

                with allure.step("7. OK button on calendar"):
                    if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                        pytest.fail("Could not find or click the 'OK' button.")
                    test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

                with allure.step("8. Sowing Date input"):
                    if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
                        pytest.fail("Could not find or click the 'Sowing Date' input field.")
                    test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

                with allure.step("9. OK button on calendar"):
                    if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                        pytest.fail("Could not find or click the 'OK' button.")
                    test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

                with allure.step("10. Submit Crop button"):
                    if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
                        pytest.fail("Could not find or click the 'Submit' button.")
                    test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})



            
        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/onboarding_flow_success.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)

    # pending farms > edit crop
    
    @allure.title("pending farms > edit crop")
    def test_pendingfarms_editcrop(self, driver):
        test_flow_steps = []

        try:
             #click on three dots 
             with allure.step("1.humburger menu dashboard"):
                time.sleep(10)
                if not smart_click(driver, "hamburger menu in dashboard", self.hamburger_menu_xpath, "Hamburger Menu in dashboard"):
                    pytest.fail("Could not find or click the hamburger menu in pending farms.")
                test_flow_steps.append({"step": "Click hamburger menu in pending farms", "status": "Success"})

             with allure.step("2. Click on pending farms tab"):
                time.sleep(10)
                if not smart_click(driver, "pending farms tab in dashboard", self.pending_farms_tab_xpath, "Pending Farms Tab in dashboard"):
                    pytest.fail("Could not find or click the pending farms tab in dashboard.")
                test_flow_steps.append({"step": "Click pending farms tab in dashboard", "status": "Success"})

             with allure.step("3. Type dropdown"):
                time.sleep(10)
                if not smart_click(driver, "search box in pending farms", self.type_dropdown_xpath, "Search Box in Pending Farms"):
                    pytest.fail("Could not find or click the search box in pending farms.")

                    test_flow_steps.append({"step": "Click search box in pending farms", "status": "Success"})

             with allure.step("4. select type farms with no boundary"):
                time.sleep(10)
                if not smart_click(driver, "select farms with no boundary from dropdown in pending farms", self.farms_with_no_boundary_xpath, "Select Farms with No Boundary from Dropdown in Pending Farms"):
                    pytest.fail("Could not find or click the option to select farms with no boundary in pending farms.")
                test_flow_steps.append({"step": "Select Farms with No Boundary from Dropdown in Pending Farms", "status": "Success"})

             with allure.step("5. Click on existing farm three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in pending farms", self.three_dots_xpath, "Three Dots in Pending Farms"):
                    pytest.fail("Could not find or click the three dots in pending farms.")
                test_flow_steps.append({"step": "Click existing farm three dots", "status": "Success"})

             with allure.step("6. edit crop from three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in pending farms", self.edit_crop_xpath, "Three Dots in Pending Farms"):
                    pytest.fail("Could not find or click the three dots in pending farms.")
                test_flow_steps.append({"step": "Click three dots in pending farms", "status": "Success"})

                    

                with allure.step("4. Click on 'Crop Name' input field"):
                        time.sleep(10)
                        if not smart_click(driver, "crop name input in pending farms", self.crop_name_input_xpath, "Crop Name Input in Pending Farms"):
                            pytest.fail("Could not find or click the 'Crop Name' input field.")
                        test_flow_steps.append({"step": "Click Crop Name input field", "status": "Success"})
                        
                with allure.step("5. Click on 'Crop Name' list item in dropdown"):
                        time.sleep(2)  # small settle time for dropdown animation
                        if not smart_click(
                            driver,
                            "select crop from dropdown (OCR)",
                            self.crop_name_item_xpath,   # still tried first (safe), then OCR
                            "Areca",
                            screenshot_path="screenshots/crop_dropdown.png",
                            force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                            ocr_attempts=3,
                        ):
                            pytest.fail("Could not select the crop name via OCR.")
                        test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})

                with allure.step("6. Click on 'Inter Crop Name' input field"):
                    time.sleep(10)
                    if not smart_click(driver, "Inter Crop Name input in pending farms", self.intercrop_name_xpath, "Inter Crop Name Input in Pending Farms"):
                        pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
                    test_flow_steps.append({"step": "Click Inter Crop Name input field", "status": "Success"})

                with allure.step("7. Click on 'Crop Name' list item in intercrop dropdown"):
                    time.sleep(2)  # small settle time for dropdown animation
                    if not smart_click(
                        driver,
                        "select crop from dropdown (OCR)",
                        self.crop_name_item_xpath,   # still tried first (safe), then OCR
                        "Beetroot",
                        screenshot_path="screenshots/crop_dropdown.png",
                        force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                        ocr_attempts=3,
                    ):
                        pytest.fail("Could not select the inter crop name via OCR.")
                    test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

                with allure.step("8. Intercrop Sowing Date input"):
                    if not smart_click(driver,  "sowing date input in pending farms", self.intercrop_sowingdate_xpath, "Intercrop Sowing Date Input in Pending Farms"):
                        pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
                    test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

                with allure.step("9. OK button on calendar"):
                    if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                        pytest.fail("Could not find or click the 'OK' button.")
                    test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

                with allure.step("10. Sowing Date input"):
                    if not smart_click(driver,  "sowing date input in pending farms", self.sowing_date_input_xpath, "Sowing Date Input in Pending Farms"):
                        pytest.fail("Could not find or click the 'Sowing Date' input field.")
                    test_flow_steps.append({"step": "Click Srowing Date input field", "status": "Success"})

                with allure.step("11. OK button on calendar"):
                    if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                        pytest.fail("Could not find or click the 'OK' button.")
                    test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

                with allure.step("12. update Crop button"):
                    if not smart_click(driver, "submit in pending farms", self.update_button_xpath, "Update Button in Pending Farms"):
                        pytest.fail("Could not find or click the 'Update' button.")
                    test_flow_steps.append({"step": "Click Update button in pending farms", "status": "Success"})

        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/onboarding_flow_success.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)

    
    @allure.title("pending farms > edit crop")
    def test_pendingfarms_editcrop(self, driver):
        test_flow_steps = []

        try:
             #click on three dots 
             with allure.step("1.humburger menu dashboard"):
                time.sleep(10)
                if not smart_click(driver, "hamburger menu in dashboard", self.hamburger_menu_xpath, "Hamburger Menu in dashboard"):
                    pytest.fail("Could not find or click the hamburger menu in pending farms.")
                test_flow_steps.append({"step": "Click hamburger menu in pending farms", "status": "Success"})

             with allure.step("2. Click on pending farms tab"):
                time.sleep(10)
                if not smart_click(driver, "pending farms tab in dashboard", self.pending_farms_tab_xpath, "Pending Farms Tab in dashboard"):
                    pytest.fail("Could not find or click the pending farms tab in dashboard.")
                test_flow_steps.append({"step": "Click pending farms tab in dashboard", "status": "Success"})

             with allure.step("3. Type dropdown"):
                time.sleep(10)
                if not smart_click(driver, "search box in pending farms", self.type_dropdown_xpath, "Search Box in Pending Farms"):
                    pytest.fail("Could not find or click the search box in pending farms.")

                    test_flow_steps.append({"step": "Click search box in pending farms", "status": "Success"})

             with allure.step("4. select type farms with no boundary"):
                time.sleep(10)
                if not smart_click(driver, "select farms with no boundary from dropdown in pending farms", self.farms_with_no_boundary_xpath, "Select Farms with No Boundary from Dropdown in Pending Farms"):
                    pytest.fail("Could not find or click the option to select farms with no boundary in pending farms.")
                test_flow_steps.append({"step": "Select Farms with No Boundary from Dropdown in Pending Farms", "status": "Success"})

             with allure.step("5. Click on existing farm three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in pending farms", self.three_dots_xpath, "Three Dots in Pending Farms"):
                    pytest.fail("Could not find or click the three dots in pending farms.")
                test_flow_steps.append({"step": "Click existing farm three dots", "status": "Success"})

             with allure.step("6. edit crop from three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in pending farms", self.edit_crop_xpath, "Three Dots in Pending Farms"):
                    pytest.fail("Could not find or click the three dots in pending farms.")
                test_flow_steps.append({"step": "Click three dots in pending farms", "status": "Success"})

                    

                with allure.step("4. Click on 'Crop Name' input field"):
                        time.sleep(10)
                        if not smart_click(driver, "crop name input in pending farms", self.crop_name_input_xpath, "Crop Name Input in Pending Farms"):
                            pytest.fail("Could not find or click the 'Crop Name' input field.")
                        test_flow_steps.append({"step": "Click Crop Name input field", "status": "Success"})
                        
                with allure.step("5. Click on 'Crop Name' list item in dropdown"):
                        time.sleep(2)  # small settle time for dropdown animation
                        if not smart_click(
                            driver,
                            "select crop from dropdown (OCR)",
                            self.crop_name_item_xpath,   # still tried first (safe), then OCR
                            "Areca",
                            screenshot_path="screenshots/crop_dropdown.png",
                            force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                            ocr_attempts=3,
                        ):
                            pytest.fail("Could not select the crop name via OCR.")
                        test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})

                with allure.step("6. Click on 'Inter Crop Name' input field"):
                    time.sleep(10)
                    if not smart_click(driver, "Inter Crop Name input in pending farms", self.intercrop_name_xpath, "Inter Crop Name Input in Pending Farms"):
                        pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
                    test_flow_steps.append({"step": "Click Inter Crop Name input field", "status": "Success"})

                with allure.step("7. Click on 'Crop Name' list item in intercrop dropdown"):
                    time.sleep(2)  # small settle time for dropdown animation
                    if not smart_click(
                        driver,
                        "select crop from dropdown (OCR)",
                        self.crop_name_item_xpath,   # still tried first (safe), then OCR
                        "Beetroot",
                        screenshot_path="screenshots/crop_dropdown.png",
                        force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                        ocr_attempts=3,
                    ):
                        pytest.fail("Could not select the inter crop name via OCR.")
                    test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

                with allure.step("8. Intercrop Sowing Date input"):
                    if not smart_click(driver,  "sowing date input in pending farms", self.intercrop_sowingdate_xpath, "Intercrop Sowing Date Input in Pending Farms"):
                        pytest.fail("Could not find or click the 'Intercrop Sowing Date' input field.")
                    test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

                with allure.step("9. OK button on calendar"):
                    if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                        pytest.fail("Could not find or click the 'OK' button.")
                    test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

                with allure.step("10. Sowing Date input"):
                    if not smart_click(driver,  "sowing date input in pending farms", self.sowing_date_input_xpath, "Sowing Date Input in Pending Farms"):
                        pytest.fail("Could not find or click the 'Sowing Date' input field.")
                    test_flow_steps.append({"step": "Click Srowing Date input field", "status": "Success"})

                with allure.step("11. OK button on calendar"):
                    if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                        pytest.fail("Could not find or click the 'OK' button.")
                    test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

                with allure.step("12. update Crop button"):
                    if not smart_click(driver, "submit in pending farms", self.update_button_xpath, "Update Button in Pending Farms"):
                        pytest.fail("Could not find or click the 'Update' button.")
                    test_flow_steps.append({"step": "Click Update button in pending farms", "status": "Success"})

        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/onboarding_flow_success.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)

    # active farms > edit boundary
    @allure.title("active farms > edit boundary")
    def test_activefarms_editboundary(self, driver):
        test_flow_steps = []
        try:
             #click on three dots 
             with allure.step("1. Click on existing farm three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in active farms", self.three_dots_xpath, "Three Dots in Active Farms"):
                    pytest.fail("Could not find or click the three dots in active farms.")
                test_flow_steps.append({"step": "Click three dots in active farms", "status": "Success"})

             with allure.step("2. Edit Boundary from three dots"):
                time.sleep(10)
                if not smart_click(driver, "edit boundary from three dots in active farms", self.edit_boundary_xpath, "Edit Boundary from Three Dots in Active Farms"):
                    pytest.fail("Could not find or click the edit boundary option from three dots in active farms.")
                test_flow_steps.append({"step": "Click Edit Boundary from three dots in active farms", "status": "Success"})

             with allure.step("3. Draw On Map to edit boundary"):
                time.sleep(10)  # Wait for the map to load
                coordinates = [
                    (390, 760),  # Top-left corner
                    (690, 760),  # Top-right corner
                    (690, 1160), # Bottom-right corner
                    (390, 1160), # Bottom-left corner
                    (390, 760),  # Closing the box
                    (390, 760)   # Closing the box
                ]
                for coord in coordinates:
                    driver.tap([coord], 100)  # duration=100ms per tap
                test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})
            
             with allure.step("4. Save & Approve Boundary"):
                if not smart_click(driver, "Save & Approve Boundary", self.save_approve_button_xpath, "Save & Approve Boundary"):
                    pytest.fail("Could not find or click the 'Save & Approve Boundary' button.")
                test_flow_steps.append({"step": "Click Save & Approve Boundary", "status": "Success"})

        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/onboarding_flow_success.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)

    @allure.title("active farms > edit boundary")
    def test_activefarms_editboundary(self, driver):
        test_flow_steps = []
        try:
             #click on three dots 
             with allure.step("1. Click on existing farm three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in active farms", self.three_dots_xpath, "Three Dots in Active Farms"):
                    pytest.fail("Could not find or click the three dots in active farms.")
                test_flow_steps.append({"step": "Click three dots in active farms", "status": "Success"})

             with allure.step("2. Edit Boundary from three dots"):
                time.sleep(10)
                if not smart_click(driver, "edit boundary from three dots in active farms", self.edit_boundary_xpath, "Edit Boundary from Three Dots in Active Farms"):
                    pytest.fail("Could not find or click the edit boundary option from three dots in active farms.")
                test_flow_steps.append({"step": "Click Edit Boundary from three dots in active farms", "status": "Success"})

             with allure.step("3. Draw On Map to edit boundary"):
                time.sleep(10)  # Wait for the map to load
                coordinates = [
                    (390, 760),  # Top-left corner
                    (690, 760),  # Top-right corner
                    (690, 1160), # Bottom-right corner
                    (390, 1160), # Bottom-left corner
                    (390, 760),  # Closing the box
                    (390, 760)   # Closing the box
                ]
                for coord in coordinates:
                    driver.tap([coord], 100)  # duration=100ms per tap
                test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})
            
             with allure.step("4. Save & Approve Boundary"):
                if not smart_click(driver, "Save & Approve Boundary", self.save_approve_button_xpath, "Save & Approve Boundary"):
                    pytest.fail("Could not find or click the 'Save & Approve Boundary' button.")
                test_flow_steps.append({"step": "Click Save & Approve Boundary", "status": "Success"})

        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/onboarding_flow_success.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)

    # pending farms > edit boundary
    @allure.title("pending farms > edit boundary")
    def test_pendingfarms_editboundary(self, driver):
        test_flow_steps = []
        try:
             #click on three dots 
             with allure.step("1.humburger menu dashboard"):
                time.sleep(10)
                if not smart_click(driver, "hamburger menu in dashboard", self.hamburger_menu_xpath, "Hamburger Menu in dashboard"):
                    pytest.fail("Could not find or click the hamburger menu in pending farms.")
                test_flow_steps.append({"step": "Click hamburger menu in pending farms", "status": "Success"})

             with allure.step("2. Click on pending farms tab"):
                time.sleep(10)
                if not smart_click(driver, "pending farms tab in dashboard", self.pending_farms_tab_xpath, "Pending Farms Tab in dashboard"):
                    pytest.fail("Could not find or click the pending farms tab in dashboard.")
                test_flow_steps.append({"step": "Click pending farms tab in dashboard", "status": "Success"})

             with allure.step("3. Type dropdown"):
                time.sleep(10)
                if not smart_click(driver, "search box in pending farms", self.type_dropdown_xpath, "Search Box in Pending Farms"):
                    pytest.fail("Could not find or click the search box in pending farms.")

                    test_flow_steps.append({"step": "Click search box in pending farms", "status": "Success"})

             with allure.step("4. select type farms with no boundary"):
                time.sleep(10)
                if not smart_click(driver, "select farms with no boundary from dropdown in pending farms", self.farms_with_no_boundary_xpath, "Select Farms with No Boundary from Dropdown in Pending Farms"):
                    pytest.fail("Could not find or click the option to select farms with no boundary in pending farms.")
                test_flow_steps.append({"step": "Select Farms with No Boundary from Dropdown in Pending Farms", "status": "Success"})

             with allure.step("5. Click on existing farm three dots"):
                time.sleep(10)
                if not smart_click(driver, "three dots in pending farms", self.three_dots_xpath, "Three Dots in Pending Farms"):
                    pytest.fail("Could not find or click the three dots in pending farms.")
                test_flow_steps.append({"step": "Click existing farm three dots", "status": "Success"})

             with allure.step("6. edit boundary from three dots"):
                time.sleep(10)
                if not smart_click(driver, "edit boundary from three dots in pending farms", self.edit_boundary_xpath, "Edit Boundary from Three Dots in Pending Farms"):
                    pytest.fail("Could not find or click the 'Edit Boundary' option from the three dots in pending farms.")
                test_flow_steps.append({"step": "Click Edit Boundary from Three Dots in Pending Farms", "status": "Success"})

        finally:
           # Save the captured flow to a file
           os.makedirs("test-flows", exist_ok=True)
           with open("test-flows/pendingfarms_editboundary_flow.json", "w") as f:
               json.dump(test_flow_steps, f, indent=4)