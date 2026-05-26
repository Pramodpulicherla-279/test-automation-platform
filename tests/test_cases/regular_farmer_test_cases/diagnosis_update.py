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
class TestOnboarding:

    @pytest.fixture(scope="class", autouse=True)
    def _load_locators_once(self, request):
        """Loads locators once per test class and attaches them to the class."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, "r", encoding="utf-8") as f:
            xpaths = json.load(f)

        
        diagnosis_xpaths       = xpaths.get("Diagnosis_updates", {})

                # ── Diagnosis updates locators ─────────────────────────────────────
        request.cls.click_diagnosis_xpath = diagnosis_xpaths.get("click_diagnosis")
        request.cls.click_first_ok_button_xpath = diagnosis_xpaths.get("click_first_ok_button")
        request.cls.click_symptom_ok_button_xpath = diagnosis_xpaths.get("click_Symptom_ok_button")
        request.cls.click_secondary_symptom_ok_button_xpath = diagnosis_xpaths.get("click_secondary_sysmptom_ok_button")
        request.cls.click_disease_confirm_button_xpath = diagnosis_xpaths.get("click_Disease_confirm_button")
        request.cls.click_curative_ok_button_xpath = diagnosis_xpaths.get("click_curative_ok_button")
        request.cls.image_desc_audio_input_xpath = diagnosis_xpaths.get("image_desc_audio_input")
        request.cls.image_desc_audio_stop_xpath = diagnosis_xpaths.get("image_desc_audio_stop")
        request.cls.image_desc_camera_input_xpath = diagnosis_xpaths.get("image_desc_camera_input")
        request.cls.image_desc_photo_capture_xpath = diagnosis_xpaths.get("image_desc_photo_capture")
        request.cls.image_desc_photo_capture_comment_xpath = diagnosis_xpaths.get("image_desc_photo_capture_comment")
        request.cls.image_desc_photo_capture_save_xpath = diagnosis_xpaths.get("image_desc_photo_capture_save_button")
        request.cls.image_desc_video_start_xpath = diagnosis_xpaths.get("image_desc_video_recording_start")
        request.cls.image_desc_video_stop_xpath = diagnosis_xpaths.get("image_desc_video_recording_stop")
        request.cls.image_desc_general_remarks_xpath = diagnosis_xpaths.get("image_desc_general_remarks_commentbox")
        request.cls.image_desc_submit_button_xpath = diagnosis_xpaths.get("image_desc_submit_button")
        request.cls.image_desc_back_button_xpath = diagnosis_xpaths.get("image_desc_back_button")
        request.cls.profile_diagnosis_tab_xpath = diagnosis_xpaths.get("profile_diagnosis_tab")
        request.cls.profile_diagnosis_dropdown_xpath = diagnosis_xpaths.get("profile_diagnosis_dropdown")

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
    @allure.title("Verify farmer can view diagnosis updates")
    def test_diagnosis_updates(self, driver):
        test_flow_steps = []

        try:

            # ── Step 1: Click on crop health ──────────────────────────────────
            # with allure.step("1. Click on crop health"):
            #     time.sleep(2)
            #     if not smart_click(driver, "Click on crop health", self.click_on_crop_health_xpath):
            #         pytest.fail("Could not find or click the 'crop health' button.")
            #     time.sleep(2)
            #     test_flow_steps.append({"step": "Click on crop health", "status": "Success"})

            # # ── Step 2: Crop health navigation ────────────────────────────────
            # with allure.step("2. Crop health navigation"):
            #     time.sleep(2)
            #     if not smart_click(driver, "Crop health navigation", self.crop_health_navigation_xpath):
            #         pytest.fail("Could not find or click the 'crop health navigation' button.")
            #     time.sleep(2)
            #     test_flow_steps.append({"step": "Crop health navigation", "status": "Success"})

            # ── Step 3: Click Diagnosis button ────────────────────────────────
            with allure.step("2. Click Diagnosis button"):
                time.sleep(2)
                if not smart_click(driver, "Click Diagnosis", self.click_diagnosis_xpath):
                    pytest.fail("Could not find or click the 'Diagnosis' button.")
                print("Diagnosis button clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Diagnosis Button", "status": "Success"})

            # ── Step 4: Click first OK button ─────────────────────────────────
            with allure.step("3. Click first OK button"):
                time.sleep(2)
                if not smart_click(driver, "First OK Button", self.click_first_ok_button_xpath):
                    pytest.fail("Could not find or click the first 'OK' button.")
                print("First OK button clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click First OK Button", "status": "Success"})

            # ── Step 5: Click Symptom OK button ───────────────────────────────
            with allure.step("4. Click Symptom OK button"):
                time.sleep(2)
                if not smart_click(driver, "Symptom OK Button", self.click_symptom_ok_button_xpath):
                    pytest.fail("Could not find or click the 'Symptom OK' button.")
                print("Symptom OK button clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Symptom OK Button", "status": "Success"})

            # ── Step 6: Click Secondary Symptom OK button ─────────────────────
            with allure.step("5. Click Secondary Symptom OK button"):
                time.sleep(2)
                if not smart_click(driver, "Secondary Symptom OK Button", self.click_secondary_symptom_ok_button_xpath):
                    pytest.fail("Could not find or click the 'Secondary Symptom OK' button.")
                print("Secondary Symptom OK button clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Secondary Symptom OK Button", "status": "Success"})

            # ── Step 7: Click Disease Confirm button ──────────────────────────
            with allure.step("6. Click Disease Confirm button"):
                time.sleep(2)
                if not smart_click(driver, "Disease Confirm Button", self.click_disease_confirm_button_xpath):
                    pytest.fail("Could not find or click the 'Disease Confirm' button.")
                print("Disease Confirm button clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Disease Confirm Button", "status": "Success"})

            # ── Step 8: Click Curative OK button ──────────────────────────────
            with allure.step("7. Click Curative OK button"):
                time.sleep(2)
                if not smart_click(driver, "Curative OK Button", self.click_curative_ok_button_xpath):
                    pytest.fail("Could not find or click the 'Curative OK' button.")
                print("Curative OK button clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Curative OK Button", "status": "Success"})

            # ── Step 9: Start audio recording ─────────────────────────────────
            with allure.step("8. Start audio recording"):
                time.sleep(2)
                if not smart_click(driver, "Audio Input", self.image_desc_audio_input_xpath):
                    pytest.fail("Could not find or click the audio input button.")
                print("Audio recording started...")
                time.sleep(3)
                test_flow_steps.append({"step": "Start Audio Recording", "status": "Success"})

            # ── Step 10: Stop audio recording ─────────────────────────────────
            with allure.step("9. Stop audio recording"):
                time.sleep(2)
                if not smart_click(driver, "Audio Stop", self.image_desc_audio_stop_xpath):
                    pytest.fail("Could not find or click the audio stop button.")
                print("Audio recording stopped...")
                time.sleep(3)
                test_flow_steps.append({"step": "Stop Audio Recording", "status": "Success"})

            # ── Step 11: Start video recording ────────────────────────────────
            with allure.step("10. Start video recording"):
                time.sleep(2)
                if not smart_click(driver, "Video Start", self.image_desc_video_start_xpath):
                    pytest.fail("Could not find or click the video start button.")
                print("Video recording started...")
                time.sleep(3)
                test_flow_steps.append({"step": "Start Video Recording", "status": "Success"})

            # ── Step 12: Stop video recording ─────────────────────────────────
            with allure.step("11. Stop video recording"):
                time.sleep(2)
                if not smart_click(driver, "Video Stop", self.image_desc_video_stop_xpath):
                    pytest.fail("Could not find or click the video stop button.")
                print("Video recording stopped...")
                time.sleep(3)
                test_flow_steps.append({"step": "Stop Video Recording", "status": "Success"})

            # ── Step 13: Photo capture ─────────────────────────────────────────
            with allure.step("12. Photo capture"):
                time.sleep(2)
                if not smart_click(driver, "Photo Capture", self.image_desc_photo_capture_xpath):
                    pytest.fail("Could not click 'Photo Capture'")
                print("Photo capture screen opened...")
                time.sleep(2)
                try:
                    comment_box = driver.find_element(AppiumBy.XPATH, self.image_desc_photo_capture_comment_xpath)
                    comment_box.send_keys("Diagnosis photo comment")
                    print("Comment added")
                except Exception as e:
                    pytest.fail(f"Could not enter comment: {str(e)}")
                time.sleep(1)
                if not smart_click(driver, "Save Photo", self.image_desc_photo_capture_save_xpath):
                    pytest.fail("Could not click 'Save' after photo capture")
                print("Photo saved...")
                time.sleep(2)
                test_flow_steps.append({"step": "Photo Capture with Comment and Save", "status": "Success"})

            # ── Step 14: Enter general remarks ────────────────────────────────
            with allure.step("13. Enter general remarks"):
                time.sleep(2)
                try:
                    remarks_box = driver.find_element(AppiumBy.XPATH, self.image_desc_general_remarks_xpath)
                    remarks_box.send_keys("General diagnosis remarks")
                    print("General remarks entered...")
                except Exception as e:
                    pytest.fail(f"Could not enter general remarks: {str(e)}")
                time.sleep(2)
                test_flow_steps.append({"step": "Enter General Remarks", "status": "Success"})

            # ── Step 15: Click Submit button ──────────────────────────────────
            with allure.step("14. Click Submit button"):
                time.sleep(2)
                if not smart_click(driver, "Submit Button", self.image_desc_submit_button_xpath):
                    pytest.fail("Could not find or click the 'Submit' button.")
                print("Submit button clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Submit Button", "status": "Success"})
            
            # ── Step 16: Click crop health profile icon ─────────────────────────────────────────
            with allure.step("15. Click crop health profile icon"):
                time.sleep(2)
                if not smart_click(driver, "Crop health profile icon", self.crop_health_profile_xpath):
                    pytest.fail("Could not find or click the crop health profile icon.")
                print("Crop health profile icon clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Crop Health Profile Icon", "status": "Success"})

             # ── Step 17: Click Profile button  ─────────────────────────────────────────
            with allure.step("16. Click Profile button"):
                time.sleep(2)
                if not smart_click(driver, "Profile button", self.profile_button_xpath):
                    pytest.fail("Could not find or click the 'Profile' button.")
                print("Profile button clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Profile Button", "status": "Success"})

            # --- step 18: click on Diagnosis tab in proflie ---
            with allure.step("17. Click Diagnosis tab in profile"):
                time.sleep(2)
                if not smart_click(driver, "Diagnosis Tab", self.profile_diagnosis_tab_xpath):
                    pytest.fail("Could not find or click the 'Diagnosis Tab' in profile.")
                print("Diagnosis tab in profile clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Diagnosis Tab in Profile", "status": "Success"})
            # --- step 10: click on diagnosis updated tab
            with allure.step("18. Click Diagnosis updates dropdown in profile"):
                time.sleep(2)
                if not smart_click(driver, "Diagnosis Updates Dropdown", self.profile_diagnosis_dropdown_xpath):
                    pytest.fail("Could not find or click the 'Diagnosis updates dropdown' in profile.")
                print("Diagnosis updates dropdown in profile clicked...")
                time.sleep(2)
                test_flow_steps.append({"step": "Click Diagnosis Updates Dropdown in Profile", "status": "Success"})
            
            


        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/diagnosis_updates_flow.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)