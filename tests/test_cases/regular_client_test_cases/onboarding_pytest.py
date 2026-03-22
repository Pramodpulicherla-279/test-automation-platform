import time
import allure
import pytest
import json
import os
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.wait_utils import smart_click
from tests.utils.ui_actions import smart_send_keys

@allure.epic("Onboarding Flow")
@allure.feature("Farmer, Farm, Crop & Boundary Creation")
class TestOnboarding:

    @pytest.fixture(scope="class", autouse=True)
    def _load_locators_once(self, request):
        """Loads locators once per test class and attaches them to the class."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_client.json")

        with open(locators_path, "r", encoding="utf-8") as f:
            xpaths = json.load(f)

        dash_x = xpaths.get("dashboard_screen", {})
        farm_x = xpaths.get("farmer_screen", {})

        # Only Onboarding locators remain here
        request.cls.locators = {
            "add_btn": dash_x.get("add_button_dashboard"),
            "add_farmer_opt": dash_x.get("add_new_farmer_option"),
            "farmer_name": farm_x.get("farmer_name_input"),
            "farmer_mobile": farm_x.get("farmer_mobile_input"),
            "submit_farmer": farm_x.get("submit_farmer_button"),
            "draw_map_btn": farm_x.get("draw_on_map_button"),
            "farm_name": farm_x.get("farm_name_input"),
            "submit_farm": farm_x.get("submit_button"),
            "crop_input": farm_x.get("crop_name_input"),
            "areca_item": farm_x.get("areca_nut_item"),
            "sowing_date": farm_x.get("sowing_date_input"),
            "calendar_ok": farm_x.get("calendar_ok_btn"),
            "transplanted_date": farm_x.get("transplanted_date_input"),
            "submit_crop": farm_x.get("submit_crop_btn"),
            "inter_crop_input": farm_x.get("inter_crop_input"),
            "inter_sowing_date": farm_x.get("inter_sowing_date_input"),
        }

    def _dismiss_coachmarks(self, driver):
        try:
            print("   -> Attempting to dismiss coachmarks...")
            driver.execute_script("mobile: clickGesture", {"x": 500, "y": 1000})
            time.sleep(1)
        except Exception as e:
            print(f"Coachmark dismissal skipped: {e}")

    @allure.story("Create Farmer, Farm, Crop, and Boundary")
    @allure.title("Verify user can add a new farmer and complete farm onboarding")
    def test_add_farmer_and_details(self, driver):
        print("\n--- STARTING ONBOARDING TEST ---\n")
        test_flow_steps = []

        try:
            
            # PART 1: ADD FARMER
            print("\n--- STARTING ADD FARMER FLOW ---\n")
            time.sleep(3)
            self._dismiss_coachmarks(driver)

            with allure.step("1. Click Add Button"):
                if not smart_click(driver, "Add Button", self.locators["add_btn"], "Add"):
                    driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2100})
                    time.sleep(2)

            with allure.step("2. Click 'Add New Farmer'"):
                if not smart_click(driver, "Add New Farmer Option", self.locators["add_farmer_opt"], "Add New Farmer"):
                    driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1850})
                    time.sleep(2)

            with allure.step("3. Enter Farmer Name"):
                farmer_name = "Test Farmer " + str(time.time())[-4:]
                
                # Tap to focus the field first
                if not smart_click(driver, "Focus Farmer Name Field", self.locators["farmer_name"], "Farmer Name"):
                    pytest.fail("Could not find or click the 'Farmer Name' field.")
                    
                # Then send the keys
                if not smart_send_keys(driver, self.locators["farmer_name"], farmer_name, "Farmer Name"):
                    pytest.fail("Could not enter text into the 'Farmer Name' field.")
                
                test_flow_steps.append({"step": "Enter Farmer Name", "status": "Success", "value": farmer_name})

            with allure.step("4. Enter Farmer Mobile"):
                # Tap to focus the field first
                if not smart_click(driver, "Focus Mobile Field", self.locators["farmer_mobile"], "Mobile"):
                    pytest.fail("Could not find or click the 'Mobile' field.")
                    
                # Then send the keys
                if not smart_send_keys(driver, self.locators["farmer_mobile"], "4422551234", "Mobile"):
                    pytest.fail("Could not enter text into the 'Mobile' field.")
                
                test_flow_steps.append({"step": "Enter Farmer Mobile", "status": "Success", "value": "4422551234"})
                
            with allure.step("5. Submit Farmer"):
                if not smart_click(driver, "Submit Farmer", self.locators["submit_farmer"], "Submit"):
                    driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2200})
                test_flow_steps.append({"step": "Submit Farmer Clicked", "status": "Success"})
            
            test_flow_steps.append({"step": "Farmer Created", "status": "Success"})
            time.sleep(3)

            # PART 2: ADD FARM
            print("\n--- STARTING ADD FARM FLOW ---\n")
            with allure.step("4. Click Draw on Map"):
                if not smart_click(driver, "Draw on Map", self.locators["draw_map_btn"], "Draw on map"):
                    driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1500})
                time.sleep(5)

            with allure.step("5. Enter Farm Name"):
                smart_send_keys(driver, self.locators["farm_name"], "My New Farm", "Farm Name")

            with allure.step("6. Submit Farm"):
                if not smart_click(driver, "Submit Farm", self.locators["submit_farm"], "Submit"):
                      driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2200})
            time.sleep(5)

            # PART 3: ADD CROP
            print("\n--- STARTING ADD CROP FLOW ---\n")
            try: driver.hide_keyboard()
            except: pass

            with allure.step("7a. Open Crop Dropdown"):
                dropdown_opened = smart_click(
                    driver, "open_crop_dropdown", "//dummy", "Search",  # <-- Fixed None
                    screenshot_path="screenshots/crop_label.png", force_ocr=True, ocr_attempts=1
                )
                if not dropdown_opened:
                    smart_click(driver, "open_crop_dropdown_fallback", "//dummy", "Search", force_ocr=True) # <-- Fixed None

            with allure.step("7b. Select 'Apple Ber' from dropdown"):
                time.sleep(3)
                if not smart_click(
                    driver, "select_crop_item", "//dummy", "Apple", # <-- Fixed None
                    screenshot_path="screenshots/crop_dropdown_list.png", force_ocr=True, ocr_attempts=3
                ):
                    if not smart_click(driver, "select_crop_item_retry", "//dummy", "Nut", force_ocr=True): # <-- Fixed None
                         pytest.fail("Could not select 'Apple Ber' via OCR.")
                test_flow_steps.append({"step": "Select Crop Name", "status": "Success"})

            with allure.step("8a. Open Inter Crop Dropdown"):
                smart_click(
                    driver, "Inter_open_crop_dropdown", "//dummy", "Search", # <-- Fixed None
                    screenshot_path="screenshots/crop_label.png", force_ocr=True, ocr_attempts=3
                )
                time.sleep(2)
           
            with allure.step("8b. Search for 'Bananas'"):
                search_field_xpath = "//*[contains(@text, 'Search Inter-Crop') or contains(@hint, 'Search Inter-Crop')]"
                try:
                    smart_send_keys(driver, search_field_xpath, "Bananas", "Inter Crop Search Field")
                    test_flow_steps.append({"step": "Search Inter-Crop", "status": "Success", "value": "Bananas"})
                except Exception as e:
                    print(f"Failed to type in search field: {e}")
                    pass
                
            with allure.step("8c. Select 'Bananas' from dropdown"):
                time.sleep(3)
                if not smart_click(
                    driver, "select_crop_item", "//dummy", "Bananas", # <-- Fixed None
                    screenshot_path="screenshots/crop_dropdown_list.png", force_ocr=True, ocr_attempts=3
                ):
                    driver.execute_script("mobile: clickGesture", {"x": 500, "y": 750}) 
                
                test_flow_steps.append({"step": "Select Bananas", "status": "Success"})

            with allure.step("8d. Open Inter-Crop Sowing Date Calendar"):
                smart_click(driver, "Inter-Crop Sowing Date", self.locators["inter_sowing_date"], "Sowing Date")
                test_flow_steps.append({"step": "Click Inter-Crop Sowing Date", "status": "Success"})

            with allure.step("8e. Confirm Sowing Date (Click OK)"):
                smart_click(driver, "Ok in calendar", self.locators["calendar_ok"], "OK")
                test_flow_steps.append({"step": "Confirm Calendar OK", "status": "Success"})
    
            # with allure.step("7. Select Crop Duration (Short)"):
            #     time.sleep(2)
            #     if smart_click(driver, "Crop Duration Short", self.locators.get("duration_short"), "Short", force_ocr=True):
            #         test_flow_steps.append({"step": "Select Short Crop Duration", "status": "Success"})
            #     else:
            #         print("Short duration button not found via OCR/Locator. Tapping coordinates.")
            #         driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1265})
            #         test_flow_steps.append({"step": "Select Short Crop Duration (Coordinate Fallback)", "status": "Success"})

            # with allure.step("8. Select Sowing Type (Direct)"):
            #     time.sleep(2)
            #     try:
            #         print("Attempting to click 'Direct Sowing'...")
            #         if not smart_click(driver, "Sowing Type Direct", self.locators.get("sowing_type_direct"), "Direct", force_ocr=True):
            #             print("OCR could not read white text on green button. Using fallback coordinates.")
            #             driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1550})
                        
            #         test_flow_steps.append({"step": "Select Direct Sowing Type", "status": "Success"})
            #     except Exception as e:
            #         print(f"Error selecting Direct Sowing type: {e}")
            #         test_flow_steps.append({"step": "Select Direct Sowing Type", "status": "Failed", "error": str(e)}) 
            
            with allure.step("9c. Open Transplanted Date Calendar"):
                smart_click(driver, "Transplanted Date Input", self.locators["transplanted_date"], "Transplanted Date")
                test_flow_steps.append({"step": "Click Transplanted Date input", "status": "Success"})

            with allure.step("9d. Confirm Transplanted Date (Click OK)"):
                time.sleep(2) # Give calendar time to open
                smart_click(driver, "Calendar OK Button", self.locators["calendar_ok"], "OK")
                test_flow_steps.append({"step": "Click OK for Transplanted Date", "status": "Success"})

            # with allure.step("9a. Open Sowing Date Calendar"):
            #     smart_click(driver, "Sowing Date Input", self.locators["sowing_date"], "Sowing Date")
            #     test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

            # with allure.step("9b. Confirm Sowing Date (Click OK)"):
            #     time.sleep(2) # Give calendar time to open
            #     smart_click(driver, "Calendar OK Button", self.locators["calendar_ok"], "OK")
            #     test_flow_steps.append({"step": "Click OK for Sowing Date", "status": "Success"})   

            with allure.step("10. Submit Crop"):
                try:
                    time.sleep(3) 
                    try: driver.hide_keyboard() 
                    except: pass
                    
                    driver.execute_script("mobile: swipeGesture", {
                        "left": 500, "top": 1500, "width": 100, "height": 1000,
                        "direction": "up", "percent": 0.75
                    })
                    time.sleep(2)
                    
                    if not smart_click(driver, "Submit Crop", self.locators["submit_crop"], "Submit", force_ocr=True):
                        driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2200})
                    
                    test_flow_steps.append({"step": "Click Submit Crop", "status": "Success"})
                except Exception as e:
                    print(f"Error submitting crop: {e}")
                
            # PART 4: BOUNDARY
            print("\n--- STARTING BOUNDARY DRAWING ---\n")
            with allure.step("11. Click Add Boundary"):
                if not smart_click(driver, "Add Boundary", self.locators["draw_map_btn"], "Add Boundary", force_ocr=True):
                      driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1500})

            with allure.step("12. Draw Polygon on Map"):
                time.sleep(5)
                polygon_coords = [(400, 800), (600, 1000), (800, 900), (700, 700), (400, 800)]
                for x, y in polygon_coords:
                    driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
                    time.sleep(0.5)
                test_flow_steps.append({"step": "Boundary Drawn", "status": "Success"})

            with allure.step("13. Save Boundary"):
                if not smart_click(driver, "Save Boundary", self.locators["submit_farm"], "Save"):
                      driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2200})

            allure.attach("Onboarding Complete", name="Final_Result", attachment_type=allure.attachment_type.TEXT)
            test_flow_steps.append({"step": "Farm & Boundary Added", "status": "Success"})
            time.sleep(5)

        except Exception as e:
            try: allure.attach(driver.get_screenshot_as_png(), name="Onboarding_Failure_Screenshot", attachment_type=allure.attachment_type.PNG)
            except: pass
            raise e

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/onboarding_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)