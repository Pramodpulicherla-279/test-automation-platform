from socket import timeout
import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.conftest import driver
import json
import os
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import find_and_click, smart_click
import sys
sys.dont_write_bytecode = True


@allure.epic("farmer updates Flow")
@allure.feature("Authentication")
class TestFarmer:

    @pytest.fixture(scope="class", autouse=True)
    def _load_locators_once(self, request):
        """Loads locators once per test class and attaches them to the class."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, "r", encoding="utf-8") as f:
            xpaths = json.load(f)

        farmer_updates_xpaths  = xpaths.get("farmer_updates", {})
        # diagnosis_xpaths       = xpaths.get("Diagnosis_updates", {})
        # ── Farmer updates locators ───────────────────────────────────────
        request.cls.active_farms_xpath = farmer_updates_xpaths.get("active_farms")
        request.cls.navigation_button_xpath = farmer_updates_xpaths.get("navigation_button")
        request.cls.start_audio_xpath = farmer_updates_xpaths.get("start_audio")
        request.cls.stop_audio_xpath = farmer_updates_xpaths.get("stop_audio")
        request.cls.start_video_recording_xpath = farmer_updates_xpaths.get("start_video_recording")
        request.cls.stop_video_recording_xpath = farmer_updates_xpaths.get("stop_video_recording")
        request.cls.photo_capture_xpath = farmer_updates_xpaths.get("photo_capture")
        request.cls.photo_capture_comment_xpath = farmer_updates_xpaths.get("photo_capture_comment")
        request.cls.navigation_photo_capture_continue_xpath = farmer_updates_xpaths.get("navigation_photo_capture_continue")
        request.cls.navigation_photo_capture_cancel_xpath = farmer_updates_xpaths.get("navigation_photo_capture_cancel")
        request.cls.navigation_save_button_xpath = farmer_updates_xpaths.get("navigation_save_button")
        request.cls.profile_xpath = farmer_updates_xpaths.get("profile")
        request.cls.profile_button_xpath = farmer_updates_xpaths.get("profile_button")
        request.cls.field_images_xpath = farmer_updates_xpaths.get("field_images")

        # ⚠️ also fixed key spacing issue
        request.cls.field_updates_tab_xpath = farmer_updates_xpaths.get("field_updates_tab")

        request.cls.media_files_xpath = farmer_updates_xpaths.get("media_files")
        request.cls.crop_info_icon_xpath = farmer_updates_xpaths.get("crop_info_icon")
        request.cls.cross_icon_xpath = farmer_updates_xpaths.get("cross_icon")
        request.cls.plus_icon_xpath = farmer_updates_xpaths.get("plus_icon")
        request.cls.minus_icon_xpath = farmer_updates_xpaths.get("minus_icon")
        request.cls.download_icon_xpath = farmer_updates_xpaths.get("download_icon")
        request.cls.play_audio_icon_xpath = farmer_updates_xpaths.get("play_audio_icon")
        request.cls.pause_audio_icon_xpath = farmer_updates_xpaths.get("pause_audio_icon")
        request.cls.start_video_xpath = farmer_updates_xpaths.get("start_video")
        request.cls.stop_video_xpath = farmer_updates_xpaths.get("stop_video")

       

    def _android_back(self, driver) -> bool:
        """Navigate back on Android (driver.back() + fallback to KEYCODE_BACK)."""
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

    # ─────────────────────────────────────────────────────────────────────────
    @allure.story("Successful Farmer Updates")
    @allure.title("crop health > farmer updates flow")
    def test_addfarm(self, driver):
        test_flow_steps = []

        try:
                    # ── Step 1: Click on active farms ──────────────────────────────────
                    with allure.step("1. Click on active farms"):
                        time.sleep(2)
                        if not smart_click(driver, "Click on active farms", self.active_farms_xpath):
                            pytest.fail("Could not find or click the 'active farms' button.")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Click on active farms", "status": "Success"})


                    # ── Step 2: Navigation button ──────────────────────────────────────
                    with allure.step("2. Navigation button"):
                        time.sleep(2)
                        if not smart_click(driver, "Navigation button", self.navigation_button_xpath):
                            pytest.fail("Could not find or click the 'navigation button'.")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Navigation button", "status": "Success"})


                    # ── Step 3: Start audio recording ──────────────────────────────────
                    with allure.step("3. Start audio recording"):
                        time.sleep(2)
                        if not smart_click(driver, "Start audio", self.start_audio_xpath):
                            pytest.fail("Could not click 'start audio'.")
                        time.sleep(3)
                        test_flow_steps.append({"step": "Start Audio Recording", "status": "Success"})


                    # ── Step 4: Stop audio recording ───────────────────────────────────
                    with allure.step("4. Stop audio recording"):
                        time.sleep(2)
                        if not smart_click(driver, "Stop audio", self.stop_audio_xpath):
                            pytest.fail("Could not click 'stop audio'.")
                        time.sleep(3)
                        test_flow_steps.append({"step": "Stop Audio Recording", "status": "Success"})


                    # ── Step 5: Start video recording ──────────────────────────────────
                    with allure.step("5. Start video recording"):
                        time.sleep(2)
                        if not smart_click(driver, "Start video", self.start_video_recording_xpath):
                            pytest.fail("Could not click 'start video'.")
                        time.sleep(3)
                        test_flow_steps.append({"step": "Start Video Recording", "status": "Success"})


                    # ── Step 6: Stop video recording ───────────────────────────────────
                    with allure.step("6. Stop video recording"):
                        time.sleep(2)
                        if not smart_click(driver, "Stop video", self.stop_video_recording_xpath):
                            pytest.fail("Could not click 'stop video'.")
                        time.sleep(3)
                        test_flow_steps.append({"step": "Stop Video Recording", "status": "Success"})


                    # ── Step 7: Photo capture with comment ─────────────────────────────
                    with allure.step("7. Photo capture with comment"):
                        time.sleep(2)
                        if not smart_click(driver, "Photo Capture", self.photo_capture_xpath):
                            pytest.fail("Could not click 'Photo Capture'")

                        time.sleep(2)
                        comment_box = driver.find_element(AppiumBy.XPATH, self.photo_capture_comment_xpath)
                        comment_box.send_keys("Test photo comment")

                        if not smart_click(driver, "Continue", self.navigation_photo_capture_continue_xpath):
                            pytest.fail("Could not click 'Continue'")

                        time.sleep(2)
                        test_flow_steps.append({"step": "Photo Capture with Comment", "status": "Success"})


                    # ── Step 8: Photo capture without comment ──────────────────────────
                    with allure.step("8. Photo capture without comment"):
                        time.sleep(2)
                        if not smart_click(driver, "Photo Capture", self.photo_capture_xpath):
                            pytest.fail("Could not click 'Photo Capture'")

                        if not smart_click(driver, "Continue", self.navigation_photo_capture_continue_xpath):
                            pytest.fail("Could not click 'Continue'")

                        time.sleep(2)
                        test_flow_steps.append({"step": "Photo Capture without Comment", "status": "Success"})


                    # ── Step 9: Save button ────────────────────────────────────────────
                    with allure.step("9. Save button"):
                        time.sleep(2)
                        if not smart_click(driver, "Save", self.navigation_save_button_xpath):
                            pytest.fail("Could not click 'Save'")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Save Button", "status": "Success"})


                    # ── Step 10: Android back ──────────────────────────────────────────
                    with allure.step("10. Android back"):
                        time.sleep(2)
                        if not self._android_back(driver):
                            pytest.fail("Failed Android back")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Android back", "status": "Success"})


                    # ── Step 11: Profile icon ──────────────────────────────────────────
                    with allure.step("11. Profile icon"):
                        time.sleep(2)
                        if not smart_click(driver, "Profile", self.profile_xpath):
                            pytest.fail("Could not click profile icon")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Profile Icon", "status": "Success"})


                    # ── Step 12: Profile button ────────────────────────────────────────
                    with allure.step("12. Profile button"):
                        time.sleep(2)
                        if not smart_click(driver, "Profile button", self.profile_button_xpath):
                            pytest.fail("Could not click profile button")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Profile Button", "status": "Success"})


                    # ── Step 13: Field Images ──────────────────────────────────────────
                    with allure.step("13. Field Images"):
                        time.sleep(2)
                        if not smart_click(driver, "Field Images", self.field_images_xpath):
                            pytest.fail("Could not click Field Images")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Field Images", "status": "Success"})


                    # ── Step 14: Media files / Farmer updates ──────────────────────────
                    with allure.step("14. Media files"):
                        time.sleep(2)
                        if not smart_click(driver, "Media Files", self.media_files_xpath):
                            pytest.fail("Could not click Media Files")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Media Files", "status": "Success"})

                    with allure.step("15. Crop info icon"):
                        time.sleep(2)
                        if not smart_click(driver, "Crop Info", self.crop_info_icon_xpath):
                            pytest.fail("Could not click Crop Info")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Crop Info", "status": "Success"})

                    with allure.step("16. Cross icon"):
                        time.sleep(2)
                        if not smart_click(driver, "Cross icon", self.cross_icon_xpath):
                            pytest.fail("Could not click Cross icon")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Cross Icon", "status": "Success"})

                    # with allure.step("17. Plus icon"):
                    #     time.sleep(2)
                    #     if not smart_click(driver, "Plus icon", self.plus_icon_xpath):
                    #          pytest.fail("Could not click Plus icon")
                    #     time.sleep(2)
                    #     test_flow_steps.append({"step": "Plus Icon", "status": "Success"})

                    # with allure.step("18. Minus icon"):
                    #     time.sleep(2)
                    #     if not smart_click(driver, "Minus icon", self.minus_icon_xpath):
                    #          pytest.fail("Could not click Minus icon")
                    #     time.sleep(2)
                    #     test_flow_steps.append({"step": "Minus Icon", "status": "Success"})
                    
                    with allure.step("17. Download icon"):
                        time.sleep(2)
                        if not smart_click(driver, "Download icon", self.download_icon_xpath):
                             pytest.fail("Could not click Download icon")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Download Icon", "status": "Success"})

                    with allure.step("18. Play audio icon"):
                        time.sleep(2)
                        if not smart_click(driver, "Play audio icon", self.play_audio_icon_xpath):
                             pytest.fail("Could not click Play audio icon")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Play Audio Icon", "status": "Success"})

                    with allure.step("19. Pause audio icon"):
                        time.sleep(2)
                        if not smart_click(driver, "Pause audio icon", self.pause_audio_icon_xpath):
                             pytest.fail("Could not click Pause audio icon")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Pause Audio Icon", "status": "Success"})

                    # with allure.step("22. Start video"):
                    #     time.sleep(2)
                    #     if not smart_click(driver, "Start video", self.start_video_xpath):
                    #          pytest.fail("Could not click Start video")
                    #     time.sleep(2)
                    #     test_flow_steps.append({"step": "Start Video", "status": "Success"})

                    # with allure.step("23. Stop video"):
                    #     time.sleep(2)
                    #     if not smart_click(driver, "Stop video", self.stop_video_xpath):
                    #          pytest.fail("Could not click Stop video")
                    #     time.sleep(2)
                    #     test_flow_steps.append({"step": "Stop Video", "status": "Success"})

                    # ── Step 15: Android back ──────────────────────────────────────────
                    with allure.step("20. Android back"):
                        time.sleep(2)
                        if not self._android_back(driver):
                            pytest.fail("Failed Android back")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Android back", "status": "Success"})
                    
                    with allure.step("21. Android back to crop health screen"):
                        time.sleep(2)
                        if not self._android_back(driver):
                            pytest.fail("Failed Android back to crop health screen")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Android back to crop health screen", "status": "Success"})

                    with allure.step("22.Android back to home screen"):
                        time.sleep(2)
                        if not self._android_back(driver):
                            pytest.fail("Failed Android back to home screen")
                        time.sleep(2)
                        test_flow_steps.append({"step": "Android back to home screen", "status": "Success"})

                    
        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/onboarding_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    # ─────────────────────────────────────────────────────────────────────────

    # @allure.title("crop health > farmer updates > navigation online flow")
    # def test_addfarm(self, driver):
    #     test_flow_steps = []

    #     try:

    #         # ── Step 1: turn off internet Click on crop health ──────────────────────────────────
    #         with allure.step("1. Click on crop health"):
    #             time.sleep(2)
    #             if not smart_click(driver, "Click on crop health", self.click_on_crop_health_xpath, "Click on crop health"):
    #                 pytest.fail("Could not find or click the 'click on crop health' button.")
    #             time.sleep(2)
    #             test_flow_steps.append({"step": "Click on crop health", "status": "Success"})

        
    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/onboarding_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)


   