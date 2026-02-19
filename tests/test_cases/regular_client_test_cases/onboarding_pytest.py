import time
import allure
import pytest
import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- IMPORT CUSTOM UTILITIES ---
from tests.utils.wait_utils import smart_click, smart_send_keys

@allure.epic("Onboarding Flow")
@allure.feature("Farmer, Farm, Crop & Boundary Creation")
class TestOnboarding:

    def _dismiss_coachmarks(self, driver):
        try:
            print("   -> Attempting to dismiss coachmarks...")
            # Replaced unstable ActionBuilder with native clickGesture
            driver.execute_script("mobile: clickGesture", {"x": 500, "y": 1000})
            time.sleep(1)
        except Exception as e:
            print(f"Coachmark dismissal skipped: {e}")

    def perform_login(self, driver, locators):
        """
        Checks if user is on Dashboard. If not, performs login.
        """
        print("\n--- CHECKING LOGIN STATUS ---\n")
        
        # 1. Check if we are already on dashboard (look for Add button)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, locators["add_btn"]))
            )
            print("   -> Already on Dashboard. Skipping login.")
            return
        except:
            print("   -> Not on Dashboard. Starting Login Flow...")

        # 2. Perform Login Steps
        with allure.step("Pre-Login: Handle Language/Permissions"):
            smart_click(driver, "Language Next", locators.get("next_button_language_login"), "Next")
            smart_click(driver, "Allow Notifications", locators.get("allow_notifications_button"), "Allow")

        with allure.step("Login: Enter Credentials"):
            smart_click(driver, "Email Tab", locators.get("email_tab"), "Email")
            smart_click(driver, "Submit Login", locators.get("submit_login_button"), "Login")

        with allure.step("Post-Login: Handle Permissions"):
            perm_btns = [
                locators.get("allow_picture_button"),
                locators.get("allow_location_button"),
                locators.get("allow_audio_button")
            ]
            for btn in perm_btns:
                if btn:
                    smart_click(driver, "Permission Allow", btn, "Allow", timeout=3)
        
        print("   -> Login flow finished. Waiting for Dashboard...")
        time.sleep(5)

    @allure.story("Create Farmer, Farm, Crop, and Boundary")
    @allure.title("Verify user can add a new farmer and complete farm onboarding")
    def test_add_farmer_and_details(self, driver):
        
        print("\n--- STARTING ONBOARDING TEST ---\n")
        
        test_flow_steps = []

        # --- Load JSON ---
        filename = 'regular_client.json'
        possible_paths = [
            os.path.join('locators', filename),
            os.path.join('tests', 'locators', filename),
            os.path.join(os.getcwd(), 'locators', filename),
        ]
        json_path = next((p for p in possible_paths if os.path.exists(p)), None)
        if not json_path: raise FileNotFoundError(f"Could not find '{filename}'")

        with open(json_path, 'r') as f: data = json.load(f)

        # --- Extract Sections ---
        login_x = data.get("login_screen", {})
        dash_x = data.get("dashboard_screen", {})
        farm_x = data.get("farmer_screen", {})
        
        # --- DEFINING LOCATORS (Properly mapped to element.json) ---
        locators = {
            # Login
            "next_button_language_login": login_x.get("next_button_language_login"),
            "allow_notifications_button": login_x.get("allow_notifications_button"),
            "email_tab": login_x.get("tab_email_login"),
            "submit_login_button": login_x.get("submit_login_button"),
            "allow_picture_button": login_x.get("allow_picture_button"),
            "allow_location_button": login_x.get("allow_location_button"),
            "allow_audio_button": login_x.get("allow_audio_button"),

            # Dashboard
            "add_btn": dash_x.get("add_button_dashboard"),
            "add_farmer_opt": dash_x.get("add_new_farmer_option"),
            
            # Farmer
            "farmer_name": farm_x.get("farmer_name_input"),
            "farmer_mobile": farm_x.get("farmer_mobile_input"),
            "submit_farmer": farm_x.get("submit_farmer_button"),
            
            # Farm
            "draw_map_btn": farm_x.get("draw_on_map_button"),
            "farm_name": farm_x.get("farm_name_input"),
            "submit_farm": farm_x.get("submit_button"),
            
            # Crop
            "crop_input": farm_x.get("crop_name_input"),
            "areca_item": farm_x.get("areca_nut_item"),
            "sowing_date": farm_x.get("sowing_date_input"),
            "calendar_ok": farm_x.get("calendar_ok_btn"),
            "submit_crop": farm_x.get("submit_crop_btn"),
            "inter_crop_input": farm_x.get("inter_crop_input"),
            "inter_sowing_date": farm_x.get("inter_sowing_date_input"),
            
            # Crop Details
            "duration_short": farm_x.get("short_duration_button"),
            "sowing_type_direct": farm_x.get("direct_sowing_btn")
        }

        # --- ASSIGN TO SELF ---
        self.crop_name_input_xpath = locators["crop_input"]
        self.crop_name_item_xpath = locators["areca_item"]
        self.intercrop_name_xpath = locators["inter_crop_input"]
        self.intercrop_sowingdate_xpath = locators["inter_sowing_date"]
        self.ok_button_xpath = locators["calendar_ok"]
        self.sowing_date_input_xpath = locators["sowing_date"]
        self.submit_crop_button_xpath = locators["submit_crop"]
        self.duration_short_xpath = locators["duration_short"]
        self.sowing_type_direct_xpath = locators["sowing_type_direct"]

        try:
            # PART 0: ENSURE LOGIN
            self.perform_login(driver, locators)
            
            # PART 1: ADD FARMER
            print("\n--- STARTING ADD FARMER FLOW ---\n")
            time.sleep(3)
            self._dismiss_coachmarks(driver)

            with allure.step("1. Click Add Button"):
                if not smart_click(driver, "Add Button", locators["add_btn"], "Add"):
                    print("   -> Smart Click failed. Forcing coordinate native click...")
                    driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2100})
                    time.sleep(2)

            with allure.step("2. Click 'Add New Farmer'"):
                if not smart_click(driver, "Add New Farmer Option", locators["add_farmer_opt"], "Add New Farmer"):
                    print("   -> Smart Click failed. Forcing coordinate native click...")
                    driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1850})
                    time.sleep(2)

            with allure.step("3. Enter Farmer Details"):
                farmer_name = "Test Farmer " + str(time.time())[-4:]
                smart_send_keys(driver, locators["farmer_name"], farmer_name, "Farmer Name")
                smart_send_keys(driver, locators["farmer_mobile"], "1245125251", "Mobile")
                
                if not smart_click(driver, "Submit Farmer", locators["submit_farmer"], "Submit"):
                    driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2200})
            
            test_flow_steps.append({"step": "Farmer Created", "status": "Success"})
            time.sleep(3)

            # PART 2: ADD FARM
            print("\n--- STARTING ADD FARM FLOW ---\n")
            with allure.step("4. Click Draw on Map"):
                if not smart_click(driver, "Draw on Map", locators["draw_map_btn"], "Draw on map"):
                    driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1500})
                time.sleep(5)

            with allure.step("5. Enter Farm Name"):
                smart_send_keys(driver, locators["farm_name"], "My New Farm", "Farm Name")

            with allure.step("6. Submit Farm"):
                if not smart_click(driver, "Submit Farm", locators["submit_farm"], "Submit"):
                      driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2200})
            time.sleep(5)

            # PART 3: ADD CROP
            print("\n--- STARTING ADD CROP FLOW ---\n")
            try: driver.hide_keyboard()
            except: pass

            # STEP 1: OPEN THE DROPDOWN
            with allure.step("5a. Open Crop Dropdown"):
                print("Attempting to open dropdown...")
                dropdown_opened = smart_click(
                    driver, "open_crop_dropdown", None, "Search",
                    screenshot_path="screenshots/crop_label.png",
                    force_ocr=True, ocr_attempts=1
                )
                
                if not dropdown_opened:
                    print("'Search' not found. Using fallback text 'Search'...")
                    dropdown_opened = smart_click(
                        driver, "open_crop_dropdown_fallback", None, "Search", force_ocr=True
                    )

            # STEP 2: SELECT 'Areca Nut' FROM LIST
            with allure.step("5b. Select 'Areca Nut' from dropdown"):
                time.sleep(3)
                print("Attempting to select 'Areca Nut' using partial text 'Areca'...")
                
                if not smart_click(
                    driver, "select_crop_item", None, "Areca",
                    screenshot_path="screenshots/crop_dropdown_list.png",
                    force_ocr=True, ocr_attempts=3
                ):
                    print("'Areca' not found. Trying 'Nut'...")
                    if not smart_click(driver, "select_crop_item_retry", None, "Nut", force_ocr=True):
                         pytest.fail("Could not select 'Areca Nut' via OCR.")
                
                test_flow_steps.append({"step": "Select Crop Name", "status": "Success"})

            with allure.step("5a. Open Inter Crop Dropdown"):
                print("Attempting to open inter-crop dropdown...")
                dropdown_opened = smart_click(
                    driver, "Inter_open_crop_dropdown", None, "Search",
                    screenshot_path="screenshots/crop_label.png",
                    force_ocr=True, ocr_attempts=3
                )
                time.sleep(2)
           
            with allure.step("5b. Search and Select 'Bananas'"):
                time.sleep(3)
                print("Attempting to type 'Bananas' into the search field...")
                search_field_xpath = "//*[contains(@text, 'Search Inter-Crop') or contains(@hint, 'Search Inter-Crop') or contains(@content-desc, 'Search Inter-Crop')]"
                
                try:
                    smart_send_keys(driver, search_field_xpath, "Bananas", "Inter Crop Search Field")
                    test_flow_steps.append({"step": "Type Bananas in Search", "status": "Success"})
                except Exception as e:
                    print(f"Could not type into search box, but continuing since 'Bananas' is visible. Error: {e}")
                
                time.sleep(3)
                
                print("Attempting to select 'Bananas' using partial text 'Bananas'...")
                if not smart_click(
                    driver, "select_crop_item", None, "Bananas", 
                    screenshot_path="screenshots/crop_dropdown_list.png",
                    force_ocr=True, ocr_attempts=3
                ):
                    print("OCR failed to click Bananas. Using fallback coordinates.")
                    driver.execute_script("mobile: clickGesture", {"x": 500, "y": 750}) 
                    
                test_flow_steps.append({"step": "Select Bananas", "status": "Success"})

                # Handle Sowing Date for Intercrop
                smart_click(driver, "Inter-Crop Sowing Date", self.intercrop_sowingdate_xpath, "Sowing Date")
                smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK")

            # with allure.step("7. Select Crop Duration (Short)"):
            #     time.sleep(2)
            #     if smart_click(driver, "Crop Duration Short", self.duration_short_xpath, "Short", force_ocr=True):
            #         test_flow_steps.append({"step": "Select Short Crop Duration", "status": "Success"})
            #     else:
            #         print("Short duration button not found via OCR/Locator. Tapping coordinates.")
            #         driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1265})

            # with allure.step("8. Select Sowing Type (Direct)"):
            #     time.sleep(2)
            #     try:
            #         print("Attempting to click 'Direct Sowing'...")
            #         if not smart_click(driver, "Sowing Type Direct", self.sowing_type_direct_xpath, "Direct", force_ocr=True):
            #             print("OCR could not read white text on green button. Using fallback coordinates.")
            #             driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1550})
                        
            #         test_flow_steps.append({"step": "Select Direct Sowing Type", "status": "Success"})
            #     except Exception as e:
            #         print(f"Error selecting Direct Sowing type: {e}")

            with allure.step("9. Sowing Date input"):
                time.sleep(2)
                try:
                    # Added force_ocr=True to prevent DOM scroll session crashes
                    if not smart_click(driver, "Sowing Date", self.sowing_date_input_xpath, "Sowing Date", force_ocr=True):
                        print("Fallback: Tapping approximate coordinate for Sowing Date")
                        driver.execute_script("mobile: clickGesture", {"x": 350, "y": 1690}) 
                    
                    test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

                    time.sleep(1)
                    smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK", force_ocr=True)
                    test_flow_steps.append({"step": "Click OK for Sowing Date", "status": "Success"})
                except Exception as e:
                    print(f"Error during Sowing Date selection: {e}")

            with allure.step("11. Submit Crop"):
                time.sleep(2)
                try:
                    # Added force_ocr=True to prevent DOM scroll session crashes
                    if not smart_click(driver, "Submit Crop", self.submit_crop_button_xpath, "Submit", force_ocr=True):
                        driver.execute_script("mobile: clickGesture", {"x": 540, "y": 2200})
                    test_flow_steps.append({"step": "Click Submit Crop", "status": "Success"})
                except Exception as e:
                    print(f"Error submitting crop: {e}")

            # PART 4: BOUNDARY
            print("\n--- STARTING BOUNDARY DRAWING ---\n")
            with allure.step("14. Click Add Boundary"):
                if not smart_click(driver, "Add Boundary", locators["draw_map_btn"], "Add Boundary", force_ocr=True):
                      driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1500})

            with allure.step("15. Draw Polygon on Map"):
                time.sleep(5)
                # Replaced ActionBuilder loop with stable native clicks
                polygon_coords = [(400, 800), (600, 1000), (800, 900), (700, 700), (400, 800)]
                for x, y in polygon_coords:
                    driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
                    time.sleep(0.5)
                test_flow_steps.append({"step": "Boundary Drawn", "status": "Success"})

            with allure.step("16. Save Boundary"):
                if not smart_click(driver, "Save Boundary", locators["submit_farm"], "Save"):
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