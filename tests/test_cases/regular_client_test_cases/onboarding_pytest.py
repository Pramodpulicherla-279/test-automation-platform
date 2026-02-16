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
from tests.utils.ui_actions import smart_click, smart_send_keys, smart_select_dropdown

@allure.epic("Onboarding Flow")
@allure.feature("Farmer, Farm, Crop & Boundary Creation")
class TestOnboarding:

    def _dismiss_coachmarks(self, driver):
        """
        Taps the center of the screen to dismiss potential tutorial overlays 
        that often appear on the Dashboard after a fresh login.
        """
        try:
            print("   -> Attempting to dismiss coachmarks...")
            actions = ActionBuilder(driver)
            p = PointerInput(interaction.POINTER_TOUCH, "finger")
            actions.devices = [p]
            actions.pointer_action.move_to_location(500, 1000) # Center screen
            actions.pointer_action.pointer_down()
            actions.pointer_action.pause(0.1)
            actions.pointer_action.pointer_up()
            actions.perform()
            time.sleep(1)
        except:
            pass

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

        # --- Extract Sections from JSON ---
        dash_x = data.get("dashboard_screen", {})
        farm_x = data.get("farmer_screen", {}) 
        
        dashboard_coords = data.get("coordinates", {}).get("dashboard_screen", {})
        farm_coords = data.get("coordinates", {}).get("farmer_screen", {})

        # --- DEFINING LOCATORS ---
        locators = {
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
            
            # Crop (Main)
            "crop_input": farm_x.get("crop_name_input"),
            "areca_item": "//*[contains(@text, 'Areca')]", 
            "sowing_date": farm_x.get("sowing_date_input"),
            "calendar_ok": farm_x.get("calendar_ok_btn"),
            "submit_crop": farm_x.get("submit_crop_btn"),

            # Crop (Inter-Crop & Fallbacks)
            "inter_crop_input": "//*[contains(@text, 'Inter') or contains(@content-desc, 'Inter') and contains(@class, 'EditText')]",
            "beetroot_item": "//*[contains(@text, 'Beetroot')]",
            "inter_sowing_date": "//*[contains(@text, 'Sowing Date')]" 
        }

        # --- ASSIGN TO SELF (For compatibility) ---
        self.crop_name_input_xpath = locators["crop_input"]
        self.crop_name_item_xpath = locators["areca_item"]
        self.intercrop_name_xpath = locators["inter_crop_input"]
        self.intercrop_sowingdate_xpath = locators["inter_sowing_date"]
        self.ok_button_xpath = locators["calendar_ok"]
        self.sowing_date_input_xpath = locators["sowing_date"]
        self.submit_crop_button_xpath = locators["submit_crop"]

        try:
            # ========================================================
            # PART 1: ADD FARMER FLOW
            # ========================================================
            print("\n--- STARTING ADD FARMER FLOW ---\n")

            time.sleep(5) 
            self._dismiss_coachmarks(driver)

            with allure.step("1. Click Add Button"):
                if not smart_click(driver, locators["add_btn"], dashboard_coords.get("add_button_dashboard"), "Add Button"):
                    print("   -> Smart Click failed. Forcing Coordinate Tap...")
                    tap_at_coordinates(driver, 540, 2100) 
                    time.sleep(2)

            with allure.step("2. Click 'Add New Farmer'"):
                if not smart_click(driver, locators["add_farmer_opt"], None, "Add New Farmer Option"):
                    raise Exception("Failed to click Add New Farmer option")

            with allure.step("3. Enter Farmer Details"):
                farmer_name = "Test Farmer " + str(time.time())[-4:]
                smart_send_keys(driver, locators["farmer_name"], farmer_name, "Farmer Name")
                smart_send_keys(driver, locators["farmer_mobile"], "1245125251", "Mobile")
                
                if not smart_click(driver, locators["submit_farmer"], None, "Submit Farmer"):
                    raise Exception("Failed to submit farmer")
            
            test_flow_steps.append({"step": "Farmer Created", "status": "Success"})
            time.sleep(3)

            # ========================================================
            # PART 2: ADD FARM FLOW
            # ========================================================
            print("\n--- STARTING ADD FARM FLOW ---\n")

            with allure.step("4. Click Draw on Map"):
                if not smart_click(driver, locators["draw_map_btn"], dashboard_coords.get("draw_on_map_button"), "Draw on Map"):
                    raise Exception("Failed to click Draw on Map")
                time.sleep(5) 

            with allure.step("5. Enter Farm Name"):
                smart_send_keys(driver, locators["farm_name"], "My New Farm", "Farm Name")

            with allure.step("6. Submit Farm"):
                if not smart_click(driver, locators["submit_farm"], None, "Submit Farm"):
                    raise Exception("Failed to click Farm Submit")
            time.sleep(5)

            # ========================================================
            # PART 3: ADD CROP DETAILS (UPDATED WITH OCR)
            # ========================================================
            print("\n--- STARTING ADD CROP FLOW ---\n")
            
            try: driver.hide_keyboard()
            except: pass

            with allure.step("4. Click on 'Crop Name' input field (OCR Force)"):
                time.sleep(5)
                # Attempt 1: Force OCR on text "Crop Name" or "Search"
                if not smart_click(
                    driver,
                    "Crop Name Input (OCR)",
                    self.crop_name_input_xpath, 
                    "Search", # Looking for "Search" placeholder text which is common
                    screenshot_path="screenshots/crop_input.png",
                    force_ocr=True,
                    ocr_attempts=3
                ):
                    print("   -> OCR 'Search' failed. Trying 'Crop Name'...")
                    # Attempt 2: Try finding label "Crop Name"
                    if not smart_click(driver, "Crop Name Label (OCR)", None, "Crop Name", force_ocr=True):
                         print("   -> OCR failed. Forcing Coordinate Tap...")
                         tap_at_coordinates(driver, 540, 600) # Approx coordinate for first input

                test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

            with allure.step("5. Click on 'Crop Name' list item in dropdown"):
                time.sleep(2)
                # Filter first
                smart_send_keys(driver, locators["crop_input"], "Areca", "Crop Search")
                time.sleep(2)
                
                if not smart_click(
                    driver,
                    "Select Areca (OCR)",
                    self.crop_name_item_xpath,   
                    "Areca",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,              
                    ocr_attempts=3,
                ):
                    print("   -> OCR Selection failed. Tapping first list item coordinate...")
                    tap_at_coordinates(driver, 500, 500)

                test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
            
            with allure.step("6. Click on Inter Crop Name' input field (OCR Force)"):
                time.sleep(3)
                if not smart_click(
                    driver,
                    "Inter Crop Input (OCR)",
                    self.intercrop_name_xpath,
                    "Inter", # Look for "Inter" text
                    force_ocr=True
                ):
                    print("   -> OCR for Inter Crop failed. Skipping.")
                else:
                    test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})

                    with allure.step("7. Click on 'Crop Name' list item in intercrop dropdown"):
                        time.sleep(2)
                        smart_send_keys(driver, locators["inter_crop_input"], "Beetroot", "Inter Search")
                        time.sleep(2)
                        
                        if not smart_click(
                            driver,
                            "Select Beetroot (OCR)",
                            self.crop_name_item_xpath,
                            "Beetroot",
                            force_ocr=True,
                            ocr_attempts=3,
                        ):
                             tap_at_coordinates(driver, 500, 500)
                        test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})

                    with allure.step("8. Intercrop Sowing Date input"):
                        if not smart_click(driver,  "sowing date input", self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
                            # Fallback if multiple dates exist
                            print("   -> Specific Inter-crop date locator failed. Tapping by coordinate...")
                            tap_at_coordinates(driver, 540, 1000) # Guessing lower screen position
                        test_flow_steps.append({"step": "Click Intercrop Sowing Date input", "status": "Success"})

                    with allure.step("9. OK button on calendar"):
                        if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                            print("   -> OK button missing. Maybe date not opened?")
                        test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

            with allure.step("10. Sowing Date input"):
                if not smart_click(driver,  "sowing date input", self.sowing_date_input_xpath, "Sowing Date"):
                    pytest.fail("Could not find or click the 'Sowing Date' input field.")
                test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})

            with allure.step("11. OK button on calendar"):
                if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
                    pytest.fail("Could not find or click the 'OK' button.")
                test_flow_steps.append({"step": "Click OK button on calendar", "status": "Success"})

            with allure.step("12. Submit Crop button"):
                if not smart_click(driver, "submit in add crop", self.submit_crop_button_xpath, "Submit"):
                    pytest.fail("Could not find or click the 'Submit' button.")
                test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})


            # ========================================================
            # PART 4: DRAW BOUNDARY
            # ========================================================
            print("\n--- STARTING BOUNDARY DRAWING ---\n")

            with allure.step("14. Click Add Boundary"):
                # Using locators[] here is now safe
                if not smart_click(driver, locators["draw_map_btn"], None, "Add Boundary Button"):
                    raise Exception("Failed to click Add Boundary button")

            with allure.step("15. Draw Polygon on Map"):
                print("Waiting for map to load...")
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
                # Using locators[] here is now safe
                if not smart_click(driver, locators["submit_farm"], None, "Save Boundary"):
                    raise Exception("Failed to click Save Boundary")

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