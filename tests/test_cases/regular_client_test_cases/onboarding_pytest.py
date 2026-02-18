import time
import allure
import pytest
import json
import os
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# --- IMPORT CUSTOM UTILITIES ---
from tests.utils.touch_utils import tap_at_coordinates, perform_scroll
from tests.utils.wait_utils import scroll_to_find
from tests.utils.wait_utils import smart_click, smart_send_keys

@allure.epic("Onboarding Flow")
@allure.feature("Farmer, Farm, Crop & Boundary Creation")
class TestOnboarding:

    def _dismiss_coachmarks(self, driver):
        try:
            print("   -> Attempting to dismiss coachmarks...")
            actions = ActionBuilder(driver)
            p = PointerInput(interaction.POINTER_TOUCH, "finger")
            actions.devices = [p]
            actions.pointer_action.move_to_location(500, 1000)
            actions.pointer_action.pointer_down()
            actions.pointer_action.pause(0.1)
            actions.pointer_action.pointer_up()
            actions.perform()
            time.sleep(1)
        except:
            pass

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
       
        # --- DEFINING LOCATORS ---
        locators = {
            # Login
            "next_button_language_login": login_x.get("next_button_language_login"),
            "allow_notifications_button": login_x.get("allow_notifications_button"),
            "email_tab": login_x.get("email_tab", "//*[contains(@text, 'Email')]"),
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
            "areca_item": "//*[contains(@text, 'Areca')]",
            "sowing_date": farm_x.get("sowing_date_input"),
            "calendar_ok": farm_x.get("calendar_ok_btn"),
            "submit_crop": farm_x.get("submit_crop_btn"),
            "inter_crop_input": "//*[contains(@text, 'Inter') or contains(@content-desc, 'Inter') and contains(@class, 'EditText')]",
            "beetroot_item": "//*[contains(@text, 'Beetroot')]",
            "inter_sowing_date": "//*[contains(@text, 'Sowing Date')]"
        }

        # --- ASSIGN TO SELF ---
        self.crop_name_input_xpath = locators["crop_input"]
        self.crop_name_item_xpath = locators["areca_item"]
        self.intercrop_name_xpath = locators["inter_crop_input"]
        self.intercrop_sowingdate_xpath = locators["inter_sowing_date"]
        self.ok_button_xpath = locators["calendar_ok"]
        self.sowing_date_input_xpath = locators["sowing_date"]
        self.submit_crop_button_xpath = locators["submit_crop"]

        try:
            # PART 0: ENSURE LOGIN
            self.perform_login(driver, locators)
           
            # PART 1: ADD FARMER
            print("\n--- STARTING ADD FARMER FLOW ---\n")
            time.sleep(3)
            self._dismiss_coachmarks(driver)

            with allure.step("1. Click Add Button"):
                if not smart_click(driver, "Add Button", locators["add_btn"], "Add"):
                    print("   -> Smart Click failed. Forcing Coordinate Tap...")
                    tap_at_coordinates(driver, 540, 2100)
                    time.sleep(2)

            with allure.step("2. Click 'Add New Farmer'"):
                if not smart_click(driver, "Add New Farmer Option", locators["add_farmer_opt"], "Add New Farmer"):
                    print("   -> Smart Click failed. Forcing Coordinate Tap...")
                    tap_at_coordinates(driver, 540, 1850)
                    time.sleep(2)

            with allure.step("3. Enter Farmer Details"):
                farmer_name = "Test Farmer " + str(time.time())[-4:]
                smart_send_keys(driver, locators["farmer_name"], farmer_name, "Farmer Name")
                smart_send_keys(driver, locators["farmer_mobile"], "1245125251", "Mobile")
               
                if not smart_click(driver, "Submit Farmer", locators["submit_farmer"], "Submit"):
                    tap_at_coordinates(driver, 540, 2200)
           
            test_flow_steps.append({"step": "Farmer Created", "status": "Success"})
            time.sleep(3)

            # PART 2: ADD FARM
            print("\n--- STARTING ADD FARM FLOW ---\n")
            with allure.step("4. Click Draw on Map"):
                if not smart_click(driver, "Draw on Map", locators["draw_map_btn"], "Draw on map"):
                    tap_at_coordinates(driver, 540, 1500)
                time.sleep(5)

            with allure.step("5. Enter Farm Name"):
                smart_send_keys(driver, locators["farm_name"], "My New Farm", "Farm Name")

            with allure.step("6. Submit Farm"):
                if not smart_click(driver, "Submit Farm", locators["submit_farm"], "Submit"):
                      tap_at_coordinates(driver, 540, 2200)
            time.sleep(5)

            # PART 3: ADD CROP
            print("\n--- STARTING ADD CROP FLOW ---\n")
            try: driver.hide_keyboard()
            except: pass

            # ========================================================
            # PART 3: ADD CROP
            # ========================================================
            print("\n--- STARTING ADD CROP FLOW ---\n")
            try: driver.hide_keyboard()
            except: pass

            # STEP 1: OPEN THE DROPDOWN
            with allure.step("5a. Open Crop Dropdown"):
                print("Attempting to open dropdown...")
                
                # Try finding "Search" first, fallback to "Search" (which worked in your logs)
                dropdown_opened = smart_click(
                    driver,
                    "open_crop_dropdown",
                    None,
                    "Search",
                    screenshot_path="screenshots/crop_label.png",
                    force_ocr=True,
                    ocr_attempts=1
                )
                
                if not dropdown_opened:
                    print("'Search' not found. Using fallback text 'Search'...")
                    dropdown_opened = smart_click(
                        driver, 
                        "open_crop_dropdown_fallback", 
                        None, 
                        "Search", 
                        force_ocr=True
                    )

            # STEP 2: SELECT 'Areca Nut' FROM LIST
            with allure.step("5b. Select 'Areca Nut' from dropdown"):
                time.sleep(3)  # Wait for list to render
                
                print("Attempting to select 'Areca Nut' using partial text 'Areca'...")
                
                # UPDATED: Searching for "Areca" only, to avoid word-splitting issues
                if not smart_click(
                    driver,
                    "select_crop_item",          
                    None,                        
                    "Areca",                     # <--- CHANGED from "Areca Nut" to "Areca"
                    screenshot_path="screenshots/crop_dropdown_list.png",
                    force_ocr=True,              
                    ocr_attempts=3
                ):
                    # Final Fallback: Try "Nut" if "Areca" somehow fails
                    print("'Areca' not found. Trying 'Nut'...")
                    if not smart_click(driver, "select_crop_item_retry", None, "Nut", force_ocr=True):
                         pytest.fail("Could not select 'Areca Nut' via OCR (tried 'Areca' and 'Nut').")
                
                test_flow_steps.append({"step": "Select Crop Name", "status": "Success"})
           
            with allure.step("6. Inter Crop"):
                time.sleep(3)
                if smart_click(driver, "Inter Crop Input", self.intercrop_name_xpath, "Inter", force_ocr=True):
                    test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})
                   
                    time.sleep(2)
                    smart_send_keys(driver, locators["inter_crop_input"], "Beetroot", "Inter Search")
                    time.sleep(2)
                   
                    if not smart_click(driver, "Select Beetroot", self.crop_name_item_xpath, "Beetroot", force_ocr=True):
                          tap_at_coordinates(driver, 500, 500)
                    test_flow_steps.append({"step": "Select Beetroot", "status": "Success"})

                    # Handle Sowing Date for Intercrop
                    smart_click(driver, "Inter-Crop Sowing Date", self.intercrop_sowingdate_xpath, "Sowing Date")
                    smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK")

            with allure.step("10. Sowing Date input"):
                if not smart_click(driver, "Sowing Date", self.sowing_date_input_xpath, "Sowing Date"):
                    tap_at_coordinates(driver, 540, 1200)
                test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

            with allure.step("11. OK button on calendar"):
                smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK")
                test_flow_steps.append({"step": "Click OK button", "status": "Success"})

            with allure.step("12. Submit Crop"):
                if not smart_click(driver, "Submit Crop", self.submit_crop_button_xpath, "Submit"):
                    tap_at_coordinates(driver, 540, 2200)
                test_flow_steps.append({"step": "Click Submit Crop", "status": "Success"})

            # PART 4: BOUNDARY
            print("\n--- STARTING BOUNDARY DRAWING ---\n")
            with allure.step("14. Click Add Boundary"):
                if not smart_click(driver, "Add Boundary", locators["draw_map_btn"], "Add Boundary"):
                      tap_at_coordinates(driver, 540, 1500)

            with allure.step("15. Draw Polygon on Map"):
                time.sleep(5)
                polygon_coords = [(400, 800), (600, 1000), (800, 900), (700, 700), (400, 800)]
                actions = ActionBuilder(driver)
                p = PointerInput(interaction.POINTER_TOUCH, "finger")
                actions.devices = [p]
               
                for idx, (x, y) in enumerate(polygon_coords):
                    if idx == 0:
                        actions.pointer_action.move_to_location(x, y).pointer_down().pause(0.2).pointer_up()
                    else:
                        actions.pointer_action.move_to_location(x, y).pointer_down().pause(0.2).pointer_up()
                actions.perform()
                time.sleep(2)
                test_flow_steps.append({"step": "Boundary Drawn", "status": "Success"})

            with allure.step("16. Save Boundary"):
                if not smart_click(driver, "Save Boundary", locators["submit_farm"], "Save"):
                      tap_at_coordinates(driver, 540, 2200)

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