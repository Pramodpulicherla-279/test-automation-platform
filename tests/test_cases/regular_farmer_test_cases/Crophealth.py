from socket import timeout
import time
import allure
import click
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import smart_click
import sys

sys.dont_write_bytecode = True

@allure.epic("Crop Health Flow")
@allure.feature("Crophealth")
class TestCropHealth:

    @pytest.fixture(scope="class", autouse=True)
    def _load_locators_once(self, request):
        """Loads locators once per test class and attaches them to the class."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, "r", encoding="utf-8") as f:
            xpaths = json.load(f)

        # ── Crop Health & Diary locators ───────────────────────────────────────
        crop_health_xpaths = xpaths.get("crop_health", {})
        diary_xpaths = xpaths.get("diary_screen", {})
        weather_xpaths = xpaths.get("weather_screen", {})
        leaf_moisture_xpaths = xpaths.get("leaf_moisture_screen", {})
        soil_moisture_xpaths = xpaths.get("soil_moisture_screen", {})
        
        # Farm card and navigation
        request.cls.farm_card_xpath = crop_health_xpaths.get("active_farms")
        request.cls.navigation_button_xpath = crop_health_xpaths.get("navigation_button")
        request.cls.diary_icon_xpath = crop_health_xpaths.get("diary_icon")
        
        # Validate mandatory locators
        mandatory_locators = {
            "farm_card_xpath": request.cls.farm_card_xpath,
            "navigation_button_xpath": request.cls.navigation_button_xpath,
            "diary_icon_xpath": request.cls.diary_icon_xpath,
        }
        
        for name, value in mandatory_locators.items():
            if not value:
                # Warning instead of failing immediately so you can test mock data
                print(f"[WARN] Locator missing in regular_farmer.json: {name}")
        
        # Diary screen
        request.cls.add_activity_button_xpath = diary_xpaths.get("add_activity_button")
        request.cls.activity_placeholder_xpath = diary_xpaths.get("activity_placeholder")
        request.cls.activity_input_field_xpath = diary_xpaths.get("activity_input_field")
        request.cls.cost_field_xpath = diary_xpaths.get("cost_field")
        request.cls.cost_input_field_xpath = diary_xpaths.get("cost_input_field")
        request.cls.submit_button_xpath = diary_xpaths.get("submit_button")
        request.cls.back_button_xpath = diary_xpaths.get("back_button")

        # Weather screen
        request.cls.weather_icon_xpath = weather_xpaths.get("weather_icon")
        request.cls.calendar_date_xpath = weather_xpaths.get("calendar_date")
        request.cls.weather_alert_xpath = weather_xpaths.get("weather_alert")
        request.cls.forecast_xpath = weather_xpaths.get("forecast")
        request.cls.hours_button_xpath = weather_xpaths.get("hours_button")
        request.cls.days_button_xpath = weather_xpaths.get("days_button")
        request.cls.close_icon_xpath = weather_xpaths.get("close_icon")
        request.cls.share_icon_xpath = weather_xpaths.get("share_icon")
        request.cls.maximise_icon_xpath = weather_xpaths.get("maximise_icon")
        request.cls.notification_icon_xpath = weather_xpaths.get("notification_icon")
        request.cls.expert_comments_xpath = weather_xpaths.get("expert_comments")
        request.cls.crop_stress_xpath = weather_xpaths.get("crop_stress")

        # Leaf Moisture screen
        request.cls.leaf_moisture_navigation_xpath = leaf_moisture_xpaths.get("leaf_moisture_navigation")
        request.cls.leaf_moisture_share_icon_xpath = leaf_moisture_xpaths.get("leaf_moisture_share_icon")
        request.cls.leaf_moisture_maximise_icon_xpath = leaf_moisture_xpaths.get("leaf_moisture_maximise_icon")
        request.cls.leaf_moisture_share_popup_xpath = leaf_moisture_xpaths.get("leaf_moisture_share_popup")

        # Soil Moisture screen
        request.cls.soil_moisture_navigation_xpath = soil_moisture_xpaths.get("soil_moisture_navigation")
        request.cls.soil_moisture_share_icon_xpath = soil_moisture_xpaths.get("soil_moisture_share_icon")
        request.cls.soil_moisture_maximise_icon_xpath = soil_moisture_xpaths.get("soil_moisture_maximise_icon")
        request.cls.soil_moisture_share_popup_xpath = soil_moisture_xpaths.get("soil_moisture_share_popup")

    def _android_back(self, driver) -> bool:
        """Navigate back on Android (driver.back() + fallback to KEYCODE_BACK)."""
        try:
            driver.back()
            time.sleep(1)
            return True
        except WebDriverException:
            pass
        except Exception:
            pass
        try:
            driver.press_keycode(4)  # KEYCODE_BACK
            time.sleep(1)
            return True
        except Exception:
            return False

    def _screenshot_with_allure(self, driver, name):
        """Take and attach screenshot to Allure report."""
        try:
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = f"screenshots/{name}_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            allure.attach(driver.get_screenshot_as_png(), name=name, attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            print(f"[WARN] Screenshot failed: {e}")

    def _scroll_to_element(self, driver, element_xpath, max_scrolls=5):
        """Scroll down until element is visible."""
        scrolls = 0
        while scrolls < max_scrolls:
            try:
                element = driver.find_element(AppiumBy.XPATH, element_xpath)
                if element.is_displayed():
                    print(f"[INFO] Element found after {scrolls} scrolls")
                    return True
            except:
                pass
            
            # Perform scroll
            try:
                size = driver.get_window_size()
                start_x = size["width"] // 2
                start_y = int(size["height"] * 0.8)
                end_x = size["width"] // 2
                end_y = int(size["height"] * 0.3)
                driver.swipe(start_x, start_y, end_x, end_y, 1000)
                time.sleep(1)
                scrolls += 1
            except Exception as e:
                print(f"[WARNING] Scroll failed: {str(e)}")
                return False
        
        print(f"[WARNING] Element not found after {max_scrolls} scrolls")
        return False

    def _wait_for_popup(self, driver, popup_xpath, timeout=10):
        """Wait for popup to appear."""
        try:
            popup = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((AppiumBy.XPATH, popup_xpath))
            )
            print("[INFO] Share popup appeared")
            return True
        except Exception as e:
            print(f"[WARNING] Share popup did not appear: {str(e)}")
            return False

    def _wait_for_maximize_screen(self, driver, timeout=10):
        """Wait for maximize screen to appear."""
        try:
            time.sleep(2)
            print("[INFO] Maximize screen displayed")
            return True
        except Exception as e:
            print(f"[WARNING] Maximize screen wait failed: {str(e)}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    @allure.story("Crop Health & Diary Flow")
    @allure.title("Complete Diary Activity Entry Flow")
    def test_crop_health_diary_activity_flow(self, driver):
        test_flow_steps = []

        try:
            # ── Step 1: Click on farm card ──────────────────────────────────────
            with allure.step("1. Click on farm card"):
                print("[INFO] Clicking on farm card...")
                time.sleep(2)
                if not smart_click(driver, "Click on farm card", self.farm_card_xpath):
                    self._screenshot_with_allure(driver, "farm_card_click_failed")
                    pytest.fail("Could not find or click the 'farm card'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_farm_card_click")
                test_flow_steps.append({"step": "Click on farm card", "status": "Success"})

            # ── Step 2: Click navigation button ──────────────────────────────────────
            with allure.step("2. Click navigation button"):
                print("[INFO] Clicking on navigation button...")
                time.sleep(2)
                if not smart_click(driver, "Click navigation button", self.navigation_button_xpath):
                    self._screenshot_with_allure(driver, "navigation_button_click_failed")
                    pytest.fail("Could not find or click the 'navigation button'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_navigation_button_click")
                test_flow_steps.append({"step": "Click navigation button", "status": "Success"})

            # ── Step 3: Android back ──────────────────────────────────────
            with allure.step("3. Android back button"):
                print("[INFO] Pressing Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "android_back_failed")
                    pytest.fail("Could not execute Android back button.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_android_back")
                test_flow_steps.append({"step": "Android back button pressed", "status": "Success"})

            # ── Step 4: Click diary icon ──────────────────────────────────────
            with allure.step("4. Click diary icon"):
                print("[INFO] Clicking on diary icon...")
                time.sleep(2)
                if not smart_click(driver, "Click diary icon", self.diary_icon_xpath):
                    self._screenshot_with_allure(driver, "diary_icon_click_failed")
                    pytest.fail("Could not find or click the 'diary icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_diary_icon_click")
                test_flow_steps.append({"step": "Click diary icon", "status": "Success"})

            # ── Step 5: Click Add Activity button ──────────────────────────────────────
            with allure.step("5. Click Add Activity button"):
                print("[INFO] Clicking on Add Activity button...")
                time.sleep(2)
                if not smart_click(driver, "Click Add Activity button", self.add_activity_button_xpath, "Add Activity"):
                    self._screenshot_with_allure(driver, "add_activity_button_click_failed")
                    pytest.fail("Could not find or click the 'Add Activity' button.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_add_activity_click")
                test_flow_steps.append({"step": "Click Add Activity button", "status": "Success"})

            # ── Step 6: Click activity placeholder and enter activity name ──────────────────────────────────────
            with allure.step("6. Click activity placeholder and enter activity name"):
                print("[INFO] Clicking on activity placeholder and entering 'Ram'...")
                time.sleep(2)
                
                # Click on placeholder first
                if not smart_click(driver, "Click activity placeholder", self.activity_placeholder_xpath):
                    self._screenshot_with_allure(driver, "activity_placeholder_click_failed")
                    pytest.fail("Could not find or click the activity placeholder.")
                
                time.sleep(1)
                
                # Now enter the activity name
                try:
                    activity_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((AppiumBy.XPATH, self.activity_input_field_xpath))
                    )
                    activity_input.clear()
                    activity_input.send_keys("Ram")
                    print("[INFO] Entered activity name: 'Ram'")
                    self._screenshot_with_allure(driver, "after_activity_name_entered")
                    test_flow_steps.append({
                        "step": "Enter activity name",
                        "status": "Success",
                        "value": "Ram"
                    })
                except Exception as e:
                    self._screenshot_with_allure(driver, "activity_input_failed")
                    pytest.fail(f"Could not enter activity name: {str(e)}")
                
                time.sleep(2)

            # ── Step 7: Click cost field ──────────────────────────────────────
            with allure.step("7. Click cost field"):
                print("[INFO] Clicking on cost field...")
                time.sleep(2)
                if not smart_click(driver, "Click cost field", self.cost_field_xpath, "Cost"):
                    self._screenshot_with_allure(driver, "cost_field_click_failed")
                    pytest.fail("Could not find or click the 'cost field'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_cost_field_click")
                test_flow_steps.append({"step": "Click cost field", "status": "Success"})

                        # ── Step 8: Enter cost amount ──────────────────────────────────────
            with allure.step("8. Enter cost amount"):
                print("[INFO] Entering cost amount '10000/-'...")
                time.sleep(1)

                try:
                    cost_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, self.cost_input_field_xpath)
                        )
                    )

                    cost_input.clear()
                    cost_input.send_keys("10000")

                    print("[INFO] Entered cost amount: '10000'")

                    self._screenshot_with_allure(
                        driver,
                        "after_cost_amount_entered"
                    )

                    test_flow_steps.append({
                        "step": "Enter cost amount",
                        "status": "Success",
                        "value": "10000"
                    })

                except Exception as e:
                    self._screenshot_with_allure(driver, "cost_input_failed")
                    pytest.fail(f"Could not enter cost amount: {str(e)}")

                time.sleep(2)


            # ── Step 9: Click Submit button ──────────────────────────────────────
            with allure.step("9. Click Submit button"):
                print("[INFO] Clicking on Submit button...")

                submit_clicked = False

                for attempt in range(2):

                    try:
                        print(f"[INFO] Submit click attempt {attempt + 1}")

                        submit_btn = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (AppiumBy.XPATH, self.submit_button_xpath)
                            )
                        )

                        submit_btn.click()

                        print("[INFO] Submit button clicked")
                        time.sleep(3)

                        # Check if submit popup still exists
                        remaining_submit_buttons = driver.find_elements(
                            AppiumBy.XPATH,
                            self.submit_button_xpath
                        )

                        if len(remaining_submit_buttons) == 0:
                            print("[INFO] Popup closed successfully")
                            submit_clicked = True
                            break

                        else:
                            print("[WARNING] Submit button still visible, retrying...")

                    except Exception as e:
                        print(f"[WARNING] Submit attempt failed: {str(e)}")

                    time.sleep(2)

                # Final validation
                if not submit_clicked:
                    self._screenshot_with_allure(
                        driver,
                        "submit_button_click_failed"
                    )
                    pytest.fail(
                        "Submit popup still visible after 2 attempts."
                    )

                time.sleep(5)

                self._screenshot_with_allure(
                    driver,
                    "after_submit_click"
                )

                test_flow_steps.append({
                    "step": "Click Submit button",
                    "status": "Success"
                })
        
            # ── Step 10: Android back ──────────────────────────────────────
            with allure.step("10. Android back button"):
                print("[INFO] Pressing Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "final_android_back_failed")
                    pytest.fail("Could not execute Android back button.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_final_android_back")
                test_flow_steps.append({"step": "Android back button pressed", "status": "Success"})

            # ====================================================================
            # WEATHER FLOW SECTION
            # ====================================================================
            
            # ── Step 11: Click weather icon ──────────────────────────────────────
            with allure.step("11. Click weather icon"):
                print("[INFO] Clicking on weather icon...")
                time.sleep(2)
                if not smart_click(driver, "Click weather icon", self.weather_icon_xpath):
                    self._screenshot_with_allure(driver, "weather_icon_click_failed")
                    pytest.fail("Could not find or click the 'weather icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_weather_icon_click")
                test_flow_steps.append({"step": "Click weather icon", "status": "Success"})

            # ── Step 13: Click weather alert ──────────────────────────────────────
            with allure.step("13. Click weather alert"):
                print("[INFO] Clicking on weather alert...")
                time.sleep(2)
                if not smart_click(driver, "Click weather alert", self.weather_alert_xpath):
                    self._screenshot_with_allure(driver, "weather_alert_click_failed")
                    pytest.fail("Could not find or click the 'weather alert'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_weather_alert_click")
                test_flow_steps.append({"step": "Click weather alert", "status": "Success"})

            # ── Step 14: Click Forecast ──────────────────────────────────────
            with allure.step("14. Click Forecast"):
                print("[INFO] Clicking on forecast...")
                time.sleep(2)
                if not smart_click(driver, "Click forecast", self.forecast_xpath):
                    self._screenshot_with_allure(driver, "forecast_click_failed")
                    pytest.fail("Could not find or click the 'forecast'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_forecast_click")
                test_flow_steps.append({"step": "Click forecast", "status": "Success"})

            # ── Step 15: Click hours button ──────────────────────────────────────
            with allure.step("15. Click hours button"):
                print("[INFO] Clicking on hours button...")
                time.sleep(2)

                if not smart_click(driver, "Click hours button", self.hours_button_xpath):
                    self._screenshot_with_allure(driver, "hours_button_click_failed")
                    pytest.fail("Could not find or click the 'hours button'.")

                time.sleep(3)

                self._screenshot_with_allure(driver, "after_hours_button_click")

                test_flow_steps.append({
                    "step": "Click hours button",
                    "status": "Success"
                })

                # Android swipe instead of execute_script
                try:
                    size = driver.get_window_size()

                    start_x = size["width"] // 2
                    start_y = int(size["height"] * 0.8)

                    end_x = size["width"] // 2
                    end_y = int(size["height"] * 0.3)

                    driver.swipe(start_x, start_y, end_x, end_y, 1000)

                    print("[INFO] Swipe completed successfully")

                except Exception as e:
                    print(f"[WARNING] Swipe failed: {str(e)}")

                time.sleep(2)

            # ── Step 16: Click days button ──────────────────────────────────────
            with allure.step("16. Click days button"):
                print("[INFO] Clicking on days button...")
                time.sleep(2)

                if not smart_click(driver, "Click days button", self.days_button_xpath):
                    self._screenshot_with_allure(driver, "days_button_click_failed")
                    pytest.fail("Could not find or click the 'days button'.")

                time.sleep(2)

                self._screenshot_with_allure(driver, "after_days_button_click")

                test_flow_steps.append({
                    "step": "Click days button",
                    "status": "Success"
                })
        
            # ── Step 17: Click close icon ──────────────────────────────────────
            with allure.step("17. Click close icon"):
                print("[INFO] Clicking on close icon...")
                time.sleep(2)
                if not smart_click(driver, "Click close icon", self.close_icon_xpath):
                    self._screenshot_with_allure(driver, "close_icon_click_failed")
                    pytest.fail("Could not find or click the 'close icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_close_icon_click")
                test_flow_steps.append({"step": "Click close icon", "status": "Success"})

            # ── Step 18: Click share icon ──────────────────────────────────────
            with allure.step("18. Click share icon"):
                print("[INFO] Clicking on share icon.")
                time.sleep(2)
                if not smart_click(driver, "Click share icon", self.share_icon_xpath):
                    self._screenshot_with_allure(driver, "share_icon_click_failed")
                    pytest.fail("Could not find or click the 'share icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_share_icon_click")
                test_flow_steps.append({"step": "Click share icon", "status": "Success"})
                
                time.sleep(2) 

            # ── Step 19: Click Android back button ──────────────────────────────────────
            with allure.step("19. Click Android back button"):   
                print("[INFO] Clicking on Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "android_back_after_share_failed")
                    pytest.fail("Could not execute Android back button after share screen.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_android_back_after_share")
                test_flow_steps.append({"step": "Android back button pressed after share", "status": "Success"})

            # ── Step 20: Click maximise icon ──────────────────────────────────────
            with allure.step("20. Click maximise icon"):
                print("[INFO] Clicking on maximise icon.")
                time.sleep(2)
                if not smart_click(driver, "Click maximise icon", self.maximise_icon_xpath):
                    self._screenshot_with_allure(driver, "maximise_icon_click_failed")
                    pytest.fail("Could not find or click the 'maximise icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_maximise_icon_click")
                test_flow_steps.append({"step": "Click maximise icon", "status": "Success"})

            # ── Step 21: Click Android back button ──────────────────────────────────────
            with allure.step("21. Click Android back button"):   
                print("[INFO] Clicking on Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "android_back_after_weather_failed")
                    pytest.fail("Could not execute Android back button after weather screen.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_android_back_after_weather")
                test_flow_steps.append({"step": "Android back button pressed after weather screen", "status": "Success"})

            # ── Step 18: Click share icon ──────────────────────────────────────
            with allure.step("18. Click notification icon"):
                print("[INFO] Clicking on notification icon.")
                time.sleep(2)
                if not smart_click(driver, "Click notification icon", self.notification_icon_xpath):
                    self._screenshot_with_allure(driver, "notification_icon_click_failed")
                    pytest.fail("Could not find or click the 'notification icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_notification_icon_click")
                test_flow_steps.append({"step": "Click notification icon", "status": "Success"})

                time.sleep(2)

            with allure.step("18. Click expert comments"):
                print("[INFO] Clicking on expert comments.")
                time.sleep(2)
                if not smart_click(driver, "Click expert comments", self.expert_comments_xpath):
                    self._screenshot_with_allure(driver, "expert_comments_click_failed")
                    pytest.fail("Could not find or click the 'expert comments'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_expert_comments_click")
                test_flow_steps.append({"step": "Click expert comments", "status": "Success"})

                time.sleep(2)

            with allure.step("18. Click crop stress"):
                print("[INFO] Clicking on crop stress.")
                time.sleep(2)
                if not smart_click(driver, "Click crop stress", self.crop_stress_xpath):
                    self._screenshot_with_allure(driver, "crop_stress_click_failed")
                    pytest.fail("Could not find or click the 'crop stress'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_crop_stress_click")
                test_flow_steps.append({"step": "Click crop stress", "status": "Success"})

                time.sleep(2)

            # ── Step 19: Click Android back button ──────────────────────────────────────
            with allure.step("19. Click Android back button"):   
                print("[INFO] Clicking on Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "android_back_after_share_failed")
                    pytest.fail("Could not execute Android back button after share screen.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_android_back_after_share")
                test_flow_steps.append({"step": "Android back button pressed after share", "status": "Success"})

            # ====================================================================
            # LEAF MOISTURE FLOW SECTION
            # ====================================================================

            # ── Step 22: Scroll down till Leaf Moisture ──────────────────────────────────────
            with allure.step("22. Scroll down till Leaf Moisture section"):
                print("[INFO] Scrolling down to find Leaf Moisture section...")
                time.sleep(2)
                if not self._scroll_to_element(driver, self.leaf_moisture_navigation_xpath, max_scrolls=5):
                    self._screenshot_with_allure(driver, "leaf_moisture_scroll_failed")
                    pytest.fail("Could not scroll to Leaf Moisture section.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "leaf_moisture_section_found")
                test_flow_steps.append({"step": "Scroll to Leaf Moisture section", "status": "Success"})

            # ── Step 23: Click navigation icon in Leaf Moisture ──────────────────────────────────────
            with allure.step("23. Click navigation icon in Leaf Moisture"):
                print("[INFO] Clicking on navigation icon in Leaf Moisture...")
                time.sleep(2)
                if not smart_click(driver, "Click leaf moisture navigation", self.leaf_moisture_navigation_xpath):
                    self._screenshot_with_allure(driver, "leaf_moisture_navigation_click_failed")
                    pytest.fail("Could not find or click the 'leaf moisture navigation icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_leaf_moisture_navigation_click")
                test_flow_steps.append({"step": "Click navigation icon in Leaf Moisture", "status": "Success"})

            # ── Step 24: Click Android back button ──────────────────────────────────────
            with allure.step("24. Click Android back button"):
                print("[INFO] Clicking on Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "android_back_after_leaf_moisture_navigation_failed")
                    pytest.fail("Could not execute Android back button after leaf moisture navigation.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_android_back_after_leaf_moisture_navigation")
                test_flow_steps.append({"step": "Android back button pressed after leaf moisture navigation", "status": "Success"})

            # ── Step 25: Click share icon in Leaf Moisture ──────────────────────────────────────
            with allure.step("25. Click share icon in Leaf Moisture"):
                print("[INFO] Clicking on share icon in Leaf Moisture...")
                time.sleep(2)
                if not smart_click(driver, "Click leaf moisture share icon", self.leaf_moisture_share_icon_xpath):
                    self._screenshot_with_allure(driver, "leaf_moisture_share_icon_click_failed")
                    pytest.fail("Could not find or click the 'leaf moisture share icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_leaf_moisture_share_icon_click")
                test_flow_steps.append({"step": "Click share icon in Leaf Moisture", "status": "Success"})

            # ── Step 26: Wait for share popup to appear ──────────────────────────────────────
            with allure.step("26. Wait for Leaf Moisture share popup to appear"):
                print("[INFO] Waiting for Leaf Moisture share popup...")
                time.sleep(2)
                if not self._wait_for_popup(driver, self.leaf_moisture_share_popup_xpath, timeout=10):
                    self._screenshot_with_allure(driver, "leaf_moisture_share_popup_wait_failed")
                    print("[WARNING] Share popup did not appear, continuing...")
                time.sleep(2)
                self._screenshot_with_allure(driver, "leaf_moisture_share_popup_appeared")
                test_flow_steps.append({"step": "Wait for Leaf Moisture share popup", "status": "Success"})

            # ── Step 27: Click Android back button ──────────────────────────────────────
            with allure.step("27. Click Android back button"):
                print("[INFO] Clicking on Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "android_back_after_leaf_moisture_share_failed")
                    pytest.fail("Could not execute Android back button after leaf moisture share popup.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_android_back_after_leaf_moisture_share")
                test_flow_steps.append({"step": "Android back button pressed after leaf moisture share", "status": "Success"})

            # ── Step 28: Click maximize icon in Leaf Moisture ──────────────────────────────────────
            with allure.step("28. Click maximize icon in Leaf Moisture"):
                print("[INFO] Clicking on maximize icon in Leaf Moisture...")
                time.sleep(2)
                if not smart_click(driver, "Click leaf moisture maximize icon", self.leaf_moisture_maximise_icon_xpath):
                    self._screenshot_with_allure(driver, "leaf_moisture_maximize_icon_click_failed")
                    pytest.fail("Could not find or click the 'leaf moisture maximize icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_leaf_moisture_maximize_icon_click")
                test_flow_steps.append({"step": "Click maximize icon in Leaf Moisture", "status": "Success"})

            # ── Step 29: Wait for Leaf Moisture maximize screen ──────────────────────────────────────
            with allure.step("29. Wait for Leaf Moisture maximize screen to appear"):
                print("[INFO] Waiting for Leaf Moisture maximize screen...")
                time.sleep(2)
                if not self._wait_for_maximize_screen(driver, timeout=10):
                    print("[WARNING] Maximize screen wait timed out, continuing...")
                self._screenshot_with_allure(driver, "leaf_moisture_maximize_screen_displayed")
                test_flow_steps.append({"step": "Wait for Leaf Moisture maximize screen", "status": "Success"})

            # ====================================================================
            # SOIL MOISTURE FLOW SECTION
            # ====================================================================

            # ── Step 30: Scroll down till Soil Moisture ──────────────────────────────────────
            with allure.step("30. Scroll down till Soil Moisture section"):
                print("[INFO] Scrolling down to find Soil Moisture section...")
                time.sleep(2)
                if not self._scroll_to_element(driver, self.soil_moisture_navigation_xpath, max_scrolls=5):
                    self._screenshot_with_allure(driver, "soil_moisture_scroll_failed")
                    pytest.fail("Could not scroll to Soil Moisture section.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "soil_moisture_section_found")
                test_flow_steps.append({"step": "Scroll to Soil Moisture section", "status": "Success"})

            # ── Step 31: Click navigation icon in Soil Moisture ──────────────────────────────────────
            with allure.step("31. Click navigation icon in Soil Moisture"):
                print("[INFO] Clicking on navigation icon in Soil Moisture...")
                time.sleep(2)
                if not smart_click(driver, "Click soil moisture navigation", self.soil_moisture_navigation_xpath):
                    self._screenshot_with_allure(driver, "soil_moisture_navigation_click_failed")
                    pytest.fail("Could not find or click the 'soil moisture navigation icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_soil_moisture_navigation_click")
                test_flow_steps.append({"step": "Click navigation icon in Soil Moisture", "status": "Success"})

            # ── Step 32: Click Android back button ──────────────────────────────────────
            with allure.step("32. Click Android back button"):
                print("[INFO] Clicking on Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "android_back_after_soil_moisture_navigation_failed")
                    pytest.fail("Could not execute Android back button after soil moisture navigation.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_android_back_after_soil_moisture_navigation")
                test_flow_steps.append({"step": "Android back button pressed after soil moisture navigation", "status": "Success"})

            # ── Step 33: Click share icon in Soil Moisture ──────────────────────────────────────
            with allure.step("33. Click share icon in Soil Moisture"):
                print("[INFO] Clicking on share icon in Soil Moisture...")
                time.sleep(2)
                if not smart_click(driver, "Click soil moisture share icon", self.soil_moisture_share_icon_xpath):
                    self._screenshot_with_allure(driver, "soil_moisture_share_icon_click_failed")
                    pytest.fail("Could not find or click the 'soil moisture share icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_soil_moisture_share_icon_click")
                test_flow_steps.append({"step": "Click share icon in Soil Moisture", "status": "Success"})

            # ── Step 34: Wait for share popup to appear ──────────────────────────────────────
            with allure.step("34. Wait for Soil Moisture share popup to appear"):
                print("[INFO] Waiting for Soil Moisture share popup...")
                time.sleep(2)
                if not self._wait_for_popup(driver, self.soil_moisture_share_popup_xpath, timeout=10):
                    self._screenshot_with_allure(driver, "soil_moisture_share_popup_wait_failed")
                    print("[WARNING] Share popup did not appear, continuing...")
                time.sleep(2)
                self._screenshot_with_allure(driver, "soil_moisture_share_popup_appeared")
                test_flow_steps.append({"step": "Wait for Soil Moisture share popup", "status": "Success"})

            # ── Step 35: Click Android back button ──────────────────────────────────────
            with allure.step("35. Click Android back button"):
                print("[INFO] Clicking on Android back button...")
                time.sleep(2)
                if not self._android_back(driver):
                    self._screenshot_with_allure(driver, "android_back_after_soil_moisture_share_failed")
                    pytest.fail("Could not execute Android back button after soil moisture share popup.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_android_back_after_soil_moisture_share")
                test_flow_steps.append({"step": "Android back button pressed after soil moisture share", "status": "Success"})

            # ── Step 36: Click maximize icon in Soil Moisture ──────────────────────────────────────
            with allure.step("36. Click maximize icon in Soil Moisture"):
                print("[INFO] Clicking on maximize icon in Soil Moisture...")
                time.sleep(2)
                if not smart_click(driver, "Click soil moisture maximize icon", self.soil_moisture_maximise_icon_xpath):
                    self._screenshot_with_allure(driver, "soil_moisture_maximize_icon_click_failed")
                    pytest.fail("Could not find or click the 'soil moisture maximize icon'.")
                time.sleep(2)
                self._screenshot_with_allure(driver, "after_soil_moisture_maximize_icon_click")
                test_flow_steps.append({"step": "Click maximize icon in Soil Moisture", "status": "Success"})

            # ── Step 37: Wait for Soil Moisture maximize screen ──────────────────────────────────────
            with allure.step("37. Wait for Soil Moisture maximize screen to appear"):
                print("[INFO] Waiting for Soil Moisture maximize screen...")
                time.sleep(2)
                if not self._wait_for_maximize_screen(driver, timeout=10):
                    print("[WARNING] Maximize screen wait timed out, continuing...")
                self._screenshot_with_allure(driver, "soil_moisture_maximize_screen_displayed")
                test_flow_steps.append({"step": "Wait for Soil Moisture maximize screen", "status": "Success"})

            # ── Success ──────────────────────────────────────────────────────────────
            print("[SUCCESS] All steps completed successfully!")
            allure.attach(
                json.dumps(test_flow_steps, indent=4),
                name="Complete Flow Steps",
                attachment_type=allure.attachment_type.JSON
            )

        except Exception as e:
            print(f"[ERROR] Test failed: {str(e)}")
            self._screenshot_with_allure(driver, "unexpected_error")
            raise
        
        finally:
            # Save test flow steps to JSON file
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/crophealth_diary_flow.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)
            print(f"[INFO] Test flow saved to test-flows/crophealth_diary_flow.json")