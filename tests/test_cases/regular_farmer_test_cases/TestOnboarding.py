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
import json
import os
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import smart_click, find_and_click
import sys
sys.dont_write_bytecode = True


# ════════════════════════════════════════════════════════════════════════════
#  MODULE-LEVEL HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _try_permission(driver, name: str, xpath: str, fallback_text: str) -> bool:
    """
    Try to click a permission dialog. Returns True if clicked, False if absent.
    Never raises — dialogs are optional.
    KeyboardInterrupt is re-raised so pytest can terminate the session cleanly.
    """
    try:
        time.sleep(1.5)
        result = smart_click(driver, name, xpath, fallback_text)
        if result:
            print(f"[PERM] ✅ {name}")
            time.sleep(1)
        else:
            print(f"[PERM] ⚠️  Not shown: {name}")
        return result
    except KeyboardInterrupt:
        raise  # CRITICAL: never swallow interrupts
    except Exception as e:
        print(f"[PERM] ⚠️  Exception ({name}): {e}")
        return False


def _wait_for_element(driver, xpath: str, fallback_text: str = "",
                      timeout: int = 30) -> bool:
    """
    Poll until xpath element appears on screen or timeout expires.
    Falls back to a broad @text/@content-desc check.
    KeyboardInterrupt is always re-raised.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            elems = driver.find_elements(AppiumBy.XPATH, xpath)
            if elems and elems[0].is_displayed():
                return True
        except KeyboardInterrupt:
            raise
        except Exception:
            pass

        if fallback_text:
            try:
                fb = (
                    f"//*[contains(@text,'{fallback_text}') or "
                    f"contains(@content-desc,'{fallback_text}')]"
                )
                elems = driver.find_elements(AppiumBy.XPATH, fb)
                if elems and elems[0].is_displayed():
                    return True
            except KeyboardInterrupt:
                raise
            except Exception:
                pass

        time.sleep(2)
    return False


def _dismiss_any_permission_dialogs(driver, locators: dict) -> None:
    """
    Sweep through all known permission dialogs and dismiss whatever is visible.
    Safe to call at any point during the test.
    """
    login_screen_xpaths = locators.get("login_screen", {})
    for key, text in [
        ("allow_picture_button",        "While using the app"),
        ("allow_location_button",       "While using"),
        ("allow_audio_button",          "While using the app"),
        ("allow_notifications_button",  "Allow"),
    ]:
        xpath = login_screen_xpaths.get(key, "")
        if xpath:
            _try_permission(driver, key, xpath, text)


# ════════════════════════════════════════════════════════════════════════════
#  TEST CLASS  (single definition — no duplicate)
# ════════════════════════════════════════════════════════════════════════════

@allure.epic("Onboarding Flow")
@allure.feature("Onboarding")
class TestOnboarding:

    # ── Class-scoped fixture: loads locators once for all tests ──────────

    @pytest.fixture(scope="class", autouse=True)
    def _load_locators_once(self, request):
        """Loads locators once per class and attaches them to request.cls."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, "r", encoding="utf-8") as f:
            xpaths = json.load(f)

        dashboard_xpaths                = xpaths.get("dashboard_screen", {})
        add_crop_screen_xpaths          = xpaths.get("add_crop_screen", {})
        determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
        add_farm_screen_xpaths          = xpaths.get("add_farm_screen", {})
        add_crop_xpaths                 = xpaths.get("add_crop_screen", {})
        direct_sowing_xpaths            = add_crop_xpaths.get("direct_sowing", {})
        draw_on_map_screen_xpaths       = xpaths.get("draw_on_map_screen", {})

        request.cls.xpaths                     = xpaths
        request.cls.add_farm_button_xpath      = dashboard_xpaths.get("add_farm_button")
        request.cls.draw_on_map_button_xpath   = determine_boundary_modal_xpaths.get("draw_on_map_button")
        request.cls.submit_button_xpath        = add_farm_screen_xpaths.get("submit_button")
        request.cls.crop_name_item_xpath       = add_crop_screen_xpaths.get("crop_name_item")
        request.cls.crop_name_input_xpath      = add_crop_screen_xpaths.get("crop_name_input")
        request.cls.sowing_date_input_xpath    = direct_sowing_xpaths.get("sowing_date_input")
        request.cls.ok_button_xpath            = add_crop_screen_xpaths.get("ok_button")
        request.cls.submit_crop_button_xpath   = add_crop_screen_xpaths.get("submit_crop_button")
        request.cls.save_approve_button_xpath  = draw_on_map_screen_xpaths.get("save_approve_button")
        request.cls.skip_button_xpath          = add_crop_screen_xpaths.get("skip_button")
        request.cls.intercrop_name_xpath       = direct_sowing_xpaths.get("intercrop_name")
        request.cls.intercrop_sowingdate_xpath = direct_sowing_xpaths.get("intercrop_sowingdate")

    # ── Internal helpers ──────────────────────────────────────────────────

    def _android_back(self, driver) -> bool:
        """Navigate back on Android. Tries driver.back() then KEYCODE_BACK."""
        try:
            driver.back()
            return True
        except WebDriverException:
            pass
        except Exception:
            pass
        try:
            driver.press_keycode(4)  # KEYCODE_BACK
            return True
        except Exception:
            return False

    def _wait_for_dashboard(self, driver, timeout: int = 60) -> bool:
        """
        Waits until the dashboard (Add Farm button) is visible, dismissing any
        permission dialogs that block the way.

        This is the FIX for 'Could not find or click the add farm button':
        the Onboarding tests start immediately after the driver is created but
        the app may still be on the login / OTP / permission screen.

        Returns True when the dashboard is ready, False on timeout.
        """
        print(f"[ONBOARDING] Waiting up to {timeout}s for dashboard...")
        deadline = time.time() + timeout

        while time.time() < deadline:
            # Primary check: add_farm_button via XPATH
            try:
                elems = driver.find_elements(AppiumBy.XPATH, self.add_farm_button_xpath)
                if elems and elems[0].is_displayed():
                    print("[ONBOARDING] ✅ Dashboard visible")
                    return True
            except KeyboardInterrupt:
                raise
            except Exception:
                pass

            # Text fallback
            try:
                fb = (
                    "//*[contains(@text,'Add farm') or "
                    "contains(@text,'Add Farm') or "
                    "contains(@content-desc,'Add farm')]"
                )
                elems = driver.find_elements(AppiumBy.XPATH, fb)
                if elems and elems[0].is_displayed():
                    print("[ONBOARDING] ✅ Dashboard visible (text fallback)")
                    return True
            except KeyboardInterrupt:
                raise
            except Exception:
                pass

            # Dashboard not ready yet — dismiss any blocking permission dialogs
            _dismiss_any_permission_dialogs(driver, self.xpaths)

            time.sleep(3)

        print("[ONBOARDING] ❌ Dashboard did not appear within timeout")
        return False

    def _screenshot_on_timeout(self, driver, filename: str) -> None:
        """Save a screenshot and attach it to the Allure report."""
        try:
            os.makedirs("screenshots", exist_ok=True)
            path = f"screenshots/{filename}"
            driver.save_screenshot(path)
            allure.attach.file(
                path,
                name=f"Timeout Screenshot — {filename}",
                attachment_type=allure.attachment_type.PNG,
            )
        except Exception as exc:
            print(f"[SCREENSHOT] Failed to capture: {exc}")

    # ════════════════════════════════════════════════════════════════════════
    #  TEST: add farm only
    # ════════════════════════════════════════════════════════════════════════

    @allure.story("Successful Onboarding")
    @allure.title("add farm")
    def test_addfarm(self, driver):
        test_flow_steps = []

        try:
            with allure.step("0. Wait for dashboard to be ready"):
                if not self._wait_for_dashboard(driver, timeout=60):
                    self._screenshot_on_timeout(driver, "dashboard_wait_timeout_addfarm.png")
                    pytest.fail(
                        "Dashboard did not appear within 60s. "
                        "The app may still be on the login/permission screen. "
                        "Check the screenshot attachment."
                    )
                test_flow_steps.append({"step": "Wait for dashboard", "status": "Success"})

            with allure.step("1. add farm"):
                if not smart_click(driver, "Add farm (button in active farms)",
                                   self.add_farm_button_xpath, "Add farm"):
                    pytest.fail("Could not find or click the 'add farm' button.")
                test_flow_steps.append({"step": "Click Add Farm button", "status": "Success"})

            with allure.step("2. draw on map button"):
                time.sleep(3)
                if not smart_click(driver, "Draw on map (button in determine boundary)",
                                   self.draw_on_map_button_xpath, "Draw on map"):
                    pytest.fail("Could not find or click the 'draw on map' button.")
                test_flow_steps.append({"step": "Click Draw on Map", "status": "Success"})

            with allure.step("3. submit button in add farm"):
                time.sleep(3)
                if not smart_click(driver, "Submit (button in add farm)",
                                   self.submit_button_xpath, "Submit"):
                    pytest.fail("Could not find or click the 'Submit' button.")
                test_flow_steps.append({"step": "Click Submit Farm", "status": "Success"})

            with allure.step("4. Android back"):
                if not self._android_back(driver):
                    pytest.fail("Failed to navigate back on Android.")
                test_flow_steps.append({"step": "Android back", "status": "Success"})

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/onboarding_addfarm_flow.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    # ════════════════════════════════════════════════════════════════════════
    #  TEST: add farm + add crop
    # ════════════════════════════════════════════════════════════════════════

    @allure.story("Successful Onboarding")
    @allure.title("Onboarding the farms and crops")
    def test_addfarm_addcrop_success(self, driver):
        test_flow_steps = []

        try:
            with allure.step("0. Wait for dashboard to be ready"):
                if not self._wait_for_dashboard(driver, timeout=60):
                    self._screenshot_on_timeout(
                        driver, "dashboard_wait_timeout_addcrop.png"
                    )
                    pytest.fail(
                        "Dashboard did not appear within 60s before "
                        "test_addfarm_addcrop_success. "
                        "Check the screenshot attachment."
                    )
                test_flow_steps.append({"step": "Wait for dashboard", "status": "Success"})

            with allure.step("1. add farm"):
                if not smart_click(driver, "Add farm (button in active farms)",
                                   self.add_farm_button_xpath, "Add farm"):
                    pytest.fail("Could not find or click the 'add farm' button.")
                test_flow_steps.append({"step": "Click Add Farm button", "status": "Success"})

            with allure.step("2. draw on map button"):
                time.sleep(3)
                if not smart_click(driver, "Draw on map (button in determine boundary)",
                                   self.draw_on_map_button_xpath, "Draw on map"):
                    pytest.fail("Could not find or click the 'draw on map' button.")
                test_flow_steps.append({"step": "Click Draw on Map", "status": "Success"})

            with allure.step("3. submit button in add farm"):
                time.sleep(3)
                if not smart_click(driver, "Submit (button in add farm)",
                                   self.submit_button_xpath, "Submit"):
                    pytest.fail("Could not find or click the 'Submit' button.")
                test_flow_steps.append({"step": "Click Submit Farm", "status": "Success"})

            with allure.step("4. Click on 'Crop Name' input field"):
                time.sleep(10)
                if not smart_click(driver, "Crop Name input",
                                   self.crop_name_input_xpath, "Crop Name"):
                    pytest.fail("Could not find or click the 'Crop Name' input field.")
                test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})

            with allure.step("5. Click on 'Crop Name' list item in dropdown"):
                time.sleep(2)
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_item_xpath,
                    "Apple",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the crop name via OCR.")
                test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})

            with allure.step("6. Click on Inter Crop Name input field"):
                time.sleep(10)
                if not smart_click(driver, "Inter Crop Name input",
                                   self.intercrop_name_xpath, "Inter-Crop Name"):
                    pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
                test_flow_steps.append({
                    "step": "Click Inter Crop Name input", "status": "Success"
                })

            with allure.step("7. Click on 'Crop Name' list item in intercrop dropdown"):
                time.sleep(2)
                if not smart_click(
                    driver,
                    "select crop from dropdown (OCR)",
                    self.crop_name_item_xpath,
                    "Beetroot",
                    screenshot_path="screenshots/crop_dropdown.png",
                    force_ocr=True,
                    ocr_attempts=3,
                ):
                    pytest.fail("Could not select the inter crop name via OCR.")
                test_flow_steps.append({
                    "step": "Click Crop Name item in intercrop", "status": "Success"
                })

            with allure.step("8. Intercrop Sowing Date input"):
                if not smart_click(driver, "sowing date input",
                                   self.intercrop_sowingdate_xpath, "Inter-Crop Sowing Date"):
                    pytest.fail(
                        "Could not find or click the 'Intercrop Sowing Date' input field."
                    )
                test_flow_steps.append({
                    "step": "Click Intercrop Sowing Date input", "status": "Success"
                })

            with allure.step("9. OK button on calendar (intercrop)"):
                if not smart_click(driver, "Ok in calendar",
                                   self.ok_button_xpath, "OK"):
                    pytest.fail("Could not find or click the 'OK' button.")
                test_flow_steps.append({
                    "step": "Click OK on calendar (intercrop)", "status": "Success"
                })

            with allure.step("10. Sowing Date input"):
                if not smart_click(driver, "sowing date input",
                                   self.sowing_date_input_xpath, "Sowing Date"):
                    pytest.fail("Could not find or click the 'Sowing Date' input field.")
                test_flow_steps.append({
                    "step": "Click Sowing Date input", "status": "Success"
                })

            with allure.step("11. OK button on calendar (sowing)"):
                if not smart_click(driver, "Ok in calendar",
                                   self.ok_button_xpath, "OK"):
                    pytest.fail("Could not find or click the 'OK' button.")
                test_flow_steps.append({
                    "step": "Click OK on calendar (sowing)", "status": "Success"
                })

            with allure.step("12. Submit Crop button"):
                if not smart_click(driver, "submit in add crop",
                                   self.submit_crop_button_xpath, "Submit"):
                    pytest.fail("Could not find or click the 'Submit' button.")
                test_flow_steps.append({
                    "step": "Click Submit Crop button", "status": "Success"
                })

            with allure.step("13. Android back"):
                if not self._android_back(driver):
                    pytest.fail("Failed to navigate back on Android.")
                test_flow_steps.append({"step": "Android back", "status": "Success"})

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/onboarding_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    # ════════════════════════════════════════════════════════════════════════
    #  TEST: add farm + add crop + add boundary  (currently commented out)
    # ════════════════════════════════════════════════════════════════════════

    # @allure.title("add farm > add crop > add boundary")
    # def test_addfarm_addcrop_addboundary_success(self, driver):
    #     test_flow_steps = []
    #     try:
    #         with allure.step("0. Wait for dashboard to be ready"):
    #             if not self._wait_for_dashboard(driver, timeout=60):
    #                 self._screenshot_on_timeout(driver, "dashboard_wait_addboundary.png")
    #                 pytest.fail("Dashboard did not appear within 60s.")
    #             test_flow_steps.append({"step": "Wait for dashboard", "status": "Success"})
    #
    #         with allure.step("1. add farm"):
    #             if not smart_click(driver, "Add farm", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not find or click the 'add farm' button.")
    #             test_flow_steps.append({"step": "Click Add Farm button", "status": "Success"})
    #
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not find or click the 'draw on map' button.")
    #             test_flow_steps.append({"step": "Click Draw on Map", "status": "Success"})
    #
    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not find or click the 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Submit Farm", "status": "Success"})
    #
    #         with allure.step("4. Click on 'Crop Name' input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Crop Name input", self.crop_name_input_xpath, "Crop Name"):
    #                 pytest.fail("Could not click 'Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Crop Name input", "status": "Success"})
    #
    #         with allure.step("5. Click on 'Crop Name' list item in dropdown"):
    #             time.sleep(2)
    #             if not smart_click(driver, "select crop (OCR)", self.crop_name_item_xpath,
    #                                "Areca", screenshot_path="screenshots/crop_dropdown.png",
    #                                force_ocr=True, ocr_attempts=3):
    #                 pytest.fail("Could not select the crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})
    #
    #         with allure.step("6. Click on Inter Crop Name input field"):
    #             time.sleep(10)
    #             if not smart_click(driver, "Inter Crop Name", self.intercrop_name_xpath, "Inter-Crop Name"):
    #                 pytest.fail("Could not click 'Inter Crop Name' input field.")
    #             test_flow_steps.append({"step": "Click Inter Crop Name input", "status": "Success"})
    #
    #         with allure.step("7. Click on 'Crop Name' list item in intercrop dropdown"):
    #             time.sleep(2)
    #             if not smart_click(driver, "select intercrop (OCR)", self.crop_name_item_xpath,
    #                                "Beetroot", screenshot_path="screenshots/crop_dropdown.png",
    #                                force_ocr=True, ocr_attempts=3):
    #                 pytest.fail("Could not select the inter crop name via OCR.")
    #             test_flow_steps.append({"step": "Click Crop Name item in intercrop", "status": "Success"})
    #
    #         with allure.step("8. Intercrop Sowing Date input"):
    #             if not smart_click(driver, "intercrop sowing date", self.intercrop_sowingdate_xpath,
    #                                "Inter-Crop Sowing Date"):
    #                 pytest.fail("Could not click 'Intercrop Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Intercrop Sowing Date", "status": "Success"})
    #
    #         with allure.step("9. OK button on calendar (intercrop)"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not click 'OK' button.")
    #             test_flow_steps.append({"step": "OK calendar intercrop", "status": "Success"})
    #
    #         with allure.step("10. Sowing Date input"):
    #             if not smart_click(driver, "sowing date", self.sowing_date_input_xpath, "Sowing Date"):
    #                 pytest.fail("Could not click 'Sowing Date' input field.")
    #             test_flow_steps.append({"step": "Click Sowing Date input", "status": "Success"})
    #
    #         with allure.step("11. OK button on calendar (sowing)"):
    #             if not smart_click(driver, "Ok in calendar", self.ok_button_xpath, "OK"):
    #                 pytest.fail("Could not click 'OK' button.")
    #             test_flow_steps.append({"step": "OK calendar sowing", "status": "Success"})
    #
    #         with allure.step("12. Submit Crop button"):
    #             if not smart_click(driver, "submit crop", self.submit_crop_button_xpath, "Submit"):
    #                 pytest.fail("Could not click 'Submit' button.")
    #             test_flow_steps.append({"step": "Click Submit Crop button", "status": "Success"})
    #
    #         with allure.step("13. Add Boundary - Draw On Map"):
    #             time.sleep(10)
    #             coordinates = [
    #                 (390, 760), (690, 760), (690, 1160),
    #                 (390, 1160), (390, 760), (390, 760),
    #             ]
    #             for coord in coordinates:
    #                 driver.tap([coord], 100)
    #             test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})
    #
    #         with allure.step("14. Save & Approve Boundary"):
    #             if not smart_click(driver, "Save & Approve Boundary",
    #                                self.save_approve_button_xpath, "Save & Approve Boundary"):
    #                 pytest.fail("Could not click 'Save & Approve Boundary' button.")
    #             test_flow_steps.append({"step": "Click Save & Approve", "status": "Success"})
    #
    #         with allure.step("15. Android back"):
    #             if not self._android_back(driver):
    #                 pytest.fail("Failed to navigate back on Android.")
    #             test_flow_steps.append({"step": "Android back", "status": "Success"})
    #
    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/onboarding_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)

    # ════════════════════════════════════════════════════════════════════════
    #  TEST: add farm + skip crop + add boundary  (currently commented out)
    # ════════════════════════════════════════════════════════════════════════

    # @allure.title("add farm > skip crop > add boundary")
    # def test_addfarm_skipcrop_addboundary_success(self, driver):
    #     test_flow_steps = []
    #     try:
    #         with allure.step("0. Wait for dashboard"):
    #             if not self._wait_for_dashboard(driver, timeout=60):
    #                 pytest.fail("Dashboard did not appear within 60s.")
    #             test_flow_steps.append({"step": "Wait for dashboard", "status": "Success"})
    #
    #         with allure.step("1. add farm"):
    #             if not smart_click(driver, "Add farm", self.add_farm_button_xpath, "Add farm"):
    #                 pytest.fail("Could not click 'add farm'.")
    #             test_flow_steps.append({"step": "Click Add Farm button", "status": "Success"})
    #
    #         with allure.step("2. draw on map button"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Draw on map", self.draw_on_map_button_xpath, "Draw on map"):
    #                 pytest.fail("Could not click 'draw on map'.")
    #             test_flow_steps.append({"step": "Click Draw on Map", "status": "Success"})
    #
    #         with allure.step("3. submit button in add farm"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Submit", self.submit_button_xpath, "Submit"):
    #                 pytest.fail("Could not click 'Submit'.")
    #             test_flow_steps.append({"step": "Click Submit Farm", "status": "Success"})
    #
    #         with allure.step("4. skip in add crop"):
    #             time.sleep(3)
    #             if not smart_click(driver, "Skip", self.skip_button_xpath, "Skip"):
    #                 pytest.fail("Could not click 'Skip'.")
    #             test_flow_steps.append({"step": "Click Skip Button", "status": "Success"})
    #
    #         with allure.step("5. Add Boundary - Draw On Map"):
    #             time.sleep(10)
    #             coordinates = [
    #                 (390, 760), (690, 760), (690, 1160),
    #                 (390, 1160), (390, 760), (390, 760),
    #             ]
    #             for coord in coordinates:
    #                 driver.tap([coord], 100)
    #             test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})
    #
    #         with allure.step("6. Save & Approve Boundary"):
    #             if not smart_click(driver, "Save & Approve Boundary",
    #                                self.save_approve_button_xpath, "Save & Approve Boundary"):
    #                 pytest.fail("Could not click 'Save & Approve Boundary'.")
    #             test_flow_steps.append({"step": "Click Save & Approve", "status": "Success"})
    #
    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/onboarding_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)

    # ════════════════════════════════════════════════════════════════════════
    #  TEST: add farm > pending farms > add crop > add boundary (commented)
    # ════════════════════════════════════════════════════════════════════════

    # @allure.title("add farm > pending farms > add crop > add boundary")
    # def test_addfarm_pendingfarms_addcrop_addboundary_success(self, driver):
    #     ...  # implement when needed

    # ════════════════════════════════════════════════════════════════════════
    #  TEST: add farm > add crop > pending farms > add boundary (commented)
    # ════════════════════════════════════════════════════════════════════════

    # @allure.title("add farm > add crop > pending farms > add boundary")
    # def test_addcrop_addfarm_pendingfarms_addboundary_success(self, driver):
    #     ...  # implement when needed

    # ── Future test ideas ─────────────────────────────────────────────────
    # active farms > edit crop
    # pending farms > edit crop
    # active farms > edit boundary
    # pending farms > edit boundary