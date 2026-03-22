import time
import allure
import pytest
import json
import os

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy

from utils.wait_utils import smart_click


@allure.epic("Onboarding Flow")
@allure.feature("Authentication")
class TestOnboarding:

    @pytest.fixture(scope="class", autouse=True)
    def _load_locators_once(self, request):

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "state_client.json")

        with open(locators_path, "r", encoding="utf-8") as f:
            xpaths = json.load(f)

        dashboard_xpaths = xpaths.get("dashboard_screen", {})
        add_farmer_xpaths = xpaths.get("add_farmer_screen", {})
        add_crop_xpaths = xpaths.get("add_crop_screen", {})

        # Dashboard
        request.cls.add_button_dashboard_xpath = dashboard_xpaths.get("add_button_dashboard")
        request.cls.add_new_farmer_option_xpath = dashboard_xpaths.get("add_new_farmer_option")
        request.cls.farm_village_dropdown_xpath = dashboard_xpaths.get("farm_village_dropdown_button")
        request.cls.farm_village_item_xpath = dashboard_xpaths.get("farm_village_item")
        request.cls.download_boundary_button_xpath = dashboard_xpaths.get("download_boundary_button")
        request.cls.submit_button_farm_villages_xpath = dashboard_xpaths.get("submit_button_farm_villages")
        request.cls.search_by_bunds_results_xpath = dashboard_xpaths.get("search_by_bunds_results")

        request.cls.search_by_bunds_lat_long_option_xpath = dashboard_xpaths.get("search_by_bunds_lat_long_option")
        # request.cls.search_by_bunds_input_xpath = dashboard_xpaths.get("search_by_bunds_input")
        request.cls.confirm_bunds_selection_button_xpath = dashboard_xpaths.get("confirm_bunds_selection_button")
        request.cls.map_marker_xpath = dashboard_xpaths.get("map_marker_xpath")

        # Farmer
        request.cls.add_farmer_name_xpath = add_farmer_xpaths.get("add_farmer_name")
        request.cls.add_farmer_phone_xpath = add_farmer_xpaths.get("add_farmer_phone")
        request.cls.submit_button_add_farmer_xpath = add_farmer_xpaths.get("submit_button_add_farmer")

        # Crop
        request.cls.crop_name_dropdown_xpath = add_crop_xpaths.get("crop_name_dropdown")
        request.cls.crop_name_xpath = add_crop_xpaths.get("crop_name")
        request.cls.short_duration_button_xpath = add_crop_xpaths.get("short_duration_button")
        request.cls.medium_duration_button_xpath = add_crop_xpaths.get("medium_duration_button")
        request.cls.long_duration_button_xpath = add_crop_xpaths.get("long_duration_button")
        request.cls.transplanted_date_xpath = add_crop_xpaths.get("transplanted_date")
        request.cls.sowing_date_xpath = add_crop_xpaths.get("sowing_date")
        request.cls.calendar_ok_button_xpath = add_crop_xpaths.get("calendar_ok_button")
        request.cls.submit_button_crop_xpath = add_crop_xpaths.get("submit_crop_button")

    def _android_back(self, driver):
        try:
            driver.back()
        except Exception:
            driver.press_keycode(4)

    @allure.story("Successful Onboarding")
    @allure.title("Dashboard → Add Farmer → Add Farm → Add Crop")
    def test_add_new_farmer_flow(self, driver):

        test_flow_steps = []

        try:

            # # Wait for Dashboard
            # WebDriverWait(driver, 20).until(
            #     EC.visibility_of_element_located((AppiumBy.XPATH, self.add_button_dashboard_xpath))
            # )

            # 1 Click Add Button
            with allure.step("1. Click Add button"):

                if not smart_click(driver, "Dashboard Add Button", self.add_button_dashboard_xpath, "Add"):
                    pytest.fail("Could not click Add button")

                test_flow_steps.append({"step": "Click Add Button", "status": "Success"})

            # 2 Add New Farmer
            with allure.step("2. Click Add New Farmer"):

                if not smart_click(driver, "Add New Farmer", self.add_new_farmer_option_xpath, "Add New Farmer"):
                    pytest.fail("Could not click Add New Farmer")

                test_flow_steps.append({"step": "Click Add New Farmer", "status": "Success"})

            # 3 Select Farm Village
            with allure.step("3. Select Farm Village"):
                # time.sleep(10)  # Wait for dropdown animation
                if not smart_click(driver, "Farm Village Dropdown", self.farm_village_dropdown_xpath, "Farm Village"):
                    pytest.fail("Could not open Farm Village dropdown")
                        
                test_flow_steps.append({"step": "Open Farm Village Dropdown", "status": "Success"})
                time.sleep(3)  # Wait for dropdown to open before selecting item

            with allure.step("4. Select specific Farm Village"):
                 time.sleep(3)  
                 if not smart_click(driver, "Select Farm Village", self.farm_village_item_xpath, "Ankampalem"):
                    pytest.fail("Could not select farm village")
                        
                 test_flow_steps.append({"step": "Select specific Farm Village", "status": "Success"})
                       

            # 4 Download Boundary
            with allure.step("5. Download Boundary"):

                if not smart_click(driver, "Download Boundary", self.download_boundary_button_xpath, "Download"):
                    pytest.fail("Could not download boundary")

                test_flow_steps.append({"step": "Download Boundary", "status": "Success"})

            # 5 Submit Village
            with allure.step("6. Submit Farm Village"):

                if not smart_click(driver, "Submit Village", self.submit_button_farm_villages_xpath, "Submit"):
                    pytest.fail("Could not submit village")

                test_flow_steps.append({"step": "Submit Village", "status": "Success"})

                time.sleep(5)  # Wait for village to be submitted and screen to update before searching bunds

            # 6 Search Bund
            with allure.step("7. Search Bund"):

                if not smart_click(driver, "Search Bund", self.search_by_bunds_lat_long_option_xpath, "Bunds"):
                    pytest.fail("Could not click Bund option")

                test_flow_steps.append({"step": "Search Bund", "status": "Success"})

            with allure.step("8.Enter Bund Number"):

                bund_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, self.search_by_bunds_lat_long_option_xpath))
                )
                bund_input.clear()
                bund_input.send_keys("20")
                time.sleep(2)  # Wait for search results to update

                test_flow_steps.append({"step": "Enter Bund Number", "status": "Success", "value": "20"})

                # if not scroll_and_click_by_text_robust(driver, "20"):
                #     pytest.fail("Bund not found")

            with allure.step("9. Select Bund 20"):

                bund_result = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((AppiumBy.XPATH, self.search_by_bunds_results_xpath))
                )
                bund_result.click()

                test_flow_steps.append({"step": "Select Bund 20", "status": "Success"})

            # with allure.step("9. Verify Bund Selected"):

            #     try:
            #         WebDriverWait(driver, 10).until(
            #             EC.presence_of_element_located((AppiumBy.XPATH, self.search_by_bunds_results_xpath))
            #         )
            #         test_flow_steps.append({"step": "Verify Bund Search Result", "status": "Success"})
            #     except Exception:
            #         pytest.fail("Bund search result not found")

                time.sleep(3)

            # step 10 map marker click to confirm bund selection
            with allure.step("10. Click Map Marker to confirm bund selection"):

                map_marker = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((AppiumBy.XPATH, self.map_marker_xpath))
                )
                map_marker.click()

                test_flow_steps.append({"step": "Click Map Marker to confirm bund selection", "status": "Success"})

            # 7 Confirm Bund
            with allure.step("11. Confirm Bund"):

                confirm_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((AppiumBy.XPATH, self.confirm_bunds_selection_button_xpath))
                )
                confirm_button.click()

                test_flow_steps.append({"step": "Confirm Bund", "status": "Success"})

            # 8 Add Farmer Name
            with allure.step("12. Add Farmer Name"):

                farmer_name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, self.add_farmer_name_xpath))
                )
                farmer_name_input.clear()
                farmer_name_input.send_keys("Tester33")

                test_flow_steps.append({
                    "step": "Enter Farmer Name",
                    "status": "Success",
                    "value": "Tester33"
                })

            # 9 Add Farmer Phone
            with allure.step("13. Add Farmer Phone"):

                farmer_phone_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, self.add_farmer_phone_xpath))
                )
                farmer_phone_input.clear()
                farmer_phone_input.send_keys("4545467328")

                test_flow_steps.append({
                    "step": "Enter Farmer Phone",
                    "status": "Success",
                    "value": "4545467328"
                })

            # 10 Submit Farmer
            with allure.step("14. Submit Farmer"):

                if not smart_click(driver, "Submit Farmer", self.submit_button_add_farmer_xpath, "Submit"):
                    pytest.fail("Could not submit farmer")

                test_flow_steps.append({"step": "Submit Farmer", "status": "Success"})

            # 11 crop name dropdown and selection
            with allure.step("15.crop name dropdown and selection"):

                if not smart_click(driver, "Crop Dropdown", self.crop_name_dropdown_xpath, "Crop"):
                    pytest.fail("Could not open crop dropdown")

                test_flow_steps.append({"step": "Add Crop", "status": "Success"})

            #16 select specific crop
            with allure.step("16. Click on 'Crop Name' list item in dropdown"):
                time.sleep(2)  # small settle time for dropdown animation
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_xpath,   # still tried first (safe), then OCR
                    "Arecanut",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,              # <- key: skip scrolling/DOM, go to OCR
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the crop name via OCR.")
                test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
            # #17 select duration
            # with allure.step("17. Select Duration"):

            #     if not smart_click(driver, "Select Duration", self.short_duration_button_xpath, "Short"):
            #         pytest.fail("Could not select duration")

            #     test_flow_steps.append({"step": "Select Duration", "status": "Success"})


            #18 select transplanted date
            with allure.step("17. Select Transplanted Date"):

                if not smart_click(driver, "Transplanted Date", self.transplanted_date_xpath, "Transplanted"):
                    pytest.fail("Could not open transplanted date calendar")

                test_flow_steps.append({"step": "Select Transplanted Date", "status": "Success"})
                     # select today's date

            with allure.step("19. Calendar OK Button"):

                if not smart_click(driver, "Calendar OK", self.calendar_ok_button_xpath, "OK"):
                    pytest.fail("Could not click calendar OK button")

                    test_flow_steps.append({"step": "Calendar OK Button", "status": "Success"})

            #18 select sowing date
            
            with allure.step("18. Select Sowing Date"):

                if not smart_click(driver, "Sowing Date", self.sowing_date_xpath, "Sowing Date"):
                    pytest.fail("Could not open sowing date calendar")

                test_flow_steps.append({"step": "Select Sowing Date", "status": "Success"})
                     # select today's date
                # today = time.strftime("%-d")  # Get current day without leading zero
                # xpath_for_today = f"//android.view.View[@content-desc='{today}']"

                # if not smart_click(driver, "Select Today's Date", xpath_for_today, today):
                #     pytest.fail("Could not select today's date")

                #     test_flow_steps.append({"step": "Select Today's Date", "status": "Success"})

            #19 calendar ok button
            with allure.step("19. Calendar OK Button"):

                if not smart_click(driver, "Calendar OK", self.calendar_ok_button_xpath, "OK"):
                    pytest.fail("Could not click calendar OK button")

                    test_flow_steps.append({"step": "Calendar OK Button", "status": "Success"})

            #20 submit crop
            with allure.step("20. Submit Crop"):

                if not smart_click(driver, "Submit Crop", self.submit_button_crop_xpath, "Submit"):
                    pytest.fail("Could not submit crop")

                    test_flow_steps.append({"step": "Submit Crop", "status": "Success"})

            # 12 Android Back
            with allure.step("20. Android Back"):

                self._android_back(driver)

                test_flow_steps.append({"step": "Android Back", "status": "Success"})

        finally:

            os.makedirs("test-flows", exist_ok=True)

            with open("test-flows/onboarding_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)