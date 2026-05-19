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
from utils.ui_actions import android_back_func
import sys
sys.dont_write_bytecode = True

def load_locators_once(self, request):
    """Loads locators once per test class and attaches them to the class."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    locators_path = os.path.join(project_root, "locators", "state_farmer.json")
    with open(locators_path, "r", encoding="utf-8") as f:
        xpaths = json.load(f)
    farmer_updates_xpaths  = xpaths.get("farmer_updates", {})
    # diagnosis_xpaths       = xpaths.get("Diagnosis_updates", {})
    # ── Farmer updates locators ───────────────────────────────────────
    request.cls.active_farms_xpath = farmer_updates_xpaths.get("active_farms")
    # request.cls.humberger_menu_xpath = farmer_updates_xpaths.get("humberger_menu")
    # request.cls.historical_farms_xpath = farmer_updates_xpaths.get("historical_farms")
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
    request.cls.tab_on_video_play_xpath = farmer_updates_xpaths.get("tab_on_video_play")
    request.cls.stop_video_xpath = farmer_updates_xpaths.get("stop_video")


def click_active_farms(driver, obj, test_flow_steps):
    with allure.step("Click on active farms"):
        time.sleep(2)
        if not smart_click(driver, "Click on active farms", obj.active_farms_xpath):
            pytest.fail("Could not find or click the 'active farms' button.")
        test_flow_steps.append({"step": "Click on active farms", "status": "Success"})

def click_navigation_button(driver, obj, test_flow_steps):
    # ── Step 2: Navigation button ──────────────────────────────────────
    with allure.step("2. Navigation button"):
        time.sleep(2)
        if not smart_click(driver, "Navigation button", obj.navigation_button_xpath):
            pytest.fail("Could not find or click the 'navigation button'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Navigation button", "status": "Success"})

def start_audio_recording(driver, obj, test_flow_steps):
    # ── Step 3: Start audio recording ──────────────────────────────────
    with allure.step("3. Start audio recording"):
        time.sleep(2)
        if not smart_click(driver, "Start audio", obj.start_audio_xpath):
            pytest.fail("Could not click 'start audio'.")
        time.sleep(3)
        test_flow_steps.append({"step": "Start Audio Recording", "status": "Success"})

def stop_audio_recording(driver, obj, test_flow_steps):
    # ── Step 4: Stop audio recording ───────────────────────────────────
    with allure.step("4. Stop audio recording"):
        time.sleep(2)
        if not smart_click(driver, "Stop audio", obj.stop_audio_xpath):
            pytest.fail("Could not click 'stop audio'.")
        time.sleep(3)
        test_flow_steps.append({"step": "Stop Audio Recording", "status": "Success"})

def start_video_recording(driver, obj, test_flow_steps):
    # ── Step 5: Start video recording ──────────────────────────────────
    with allure.step("5. Start video recording"):
        time.sleep(2)
        if not smart_click(driver, "Start video", obj.start_video_recording_xpath):
            pytest.fail("Could not click 'start video'.")
        time.sleep(3)
        test_flow_steps.append({"step": "Start Video Recording", "status": "Success"})


def stop_video_recording(driver, obj, test_flow_steps):

    with allure.step("6. Stop video recording"):

        time.sleep(5)

        driver.execute_script("mobile: clickGesture", {
            "x": 904,
            "y": 2005
        })

        time.sleep(5)

        test_flow_steps.append({
            "step": "Stop Video Recording",
            "status": "Success"
        })

def photo_capture_with_comment(driver, obj, test_flow_steps):
    # ── Step 7: Photo capture with comment ─────────────────────────────
    with allure.step("7. Photo capture with comment"):
        time.sleep(2)
        if not smart_click(driver, "Photo Capture", obj.photo_capture_xpath):
            pytest.fail("Could not click 'Photo Capture'")

        time.sleep(2)
        comment_box = driver.find_element(AppiumBy.XPATH, obj.photo_capture_comment_xpath)
        comment_box.send_keys("Test photo comment")

        if not smart_click(driver, "Continue", obj.navigation_photo_capture_continue_xpath):
           pytest.fail("Could not click 'Continue'")

        time.sleep(2)
        test_flow_steps.append({"step": "Photo Capture with Comment", "status": "Success"})

def photo_capture_without_comment(driver, obj, test_flow_steps):
    # ── Step 8: Photo capture without comment ──────────────────────────
    with allure.step("8. Photo capture without comment"):
        time.sleep(2)
        if not smart_click(driver, "Photo Capture", obj.photo_capture_xpath):
            pytest.fail("Could not click 'Photo Capture'")

        if not smart_click(driver, "Continue", obj.navigation_photo_capture_continue_xpath):
            pytest.fail("Could not click 'Continue'")

        time.sleep(2)
        test_flow_steps.append({"step": "Photo Capture without Comment", "status": "Success"})

def save_updates(driver, obj, test_flow_steps):
    # ── Step 9: Save button ────────────────────────────────────────────
    with allure.step("9. Save button"):
        time.sleep(2)
        if not smart_click(driver, "Save", obj.navigation_save_button_xpath):
            pytest.fail("Could not click 'Save'")
        time.sleep(2)
        test_flow_steps.append({"step": "Save Button", "status": "Success"})

def android_back(driver, obj, test_flow_steps):
    # ── Step 10: Android back ──────────────────────────────────────────
    with allure.step("Android back"):
        if not android_back_func(driver):
            pytest.fail("Failed Android back")
    
        test_flow_steps.append({"step": "Android back", "status": "Success"})

def profile_icon(driver, obj, test_flow_steps):
    # ── Step 11: Profile icon ──────────────────────────────────────────
    with allure.step("11. Profile icon"):
        time.sleep(5)
        if not smart_click(driver, "Profile", obj.profile_xpath):
            pytest.fail("Could not click profile icon")
        time.sleep(2)
        test_flow_steps.append({"step": "Profile Icon", "status": "Success"})

def profile_button(driver, obj, test_flow_steps):
    # ── Step 12: Profile button ────────────────────────────────────────
    with allure.step("12. Profile button"):
        time.sleep(2)
        if not smart_click(driver, "Profile button", obj.profile_button_xpath):
            pytest.fail("Could not click profile button")
        time.sleep(2)
        test_flow_steps.append({"step": "Profile Button", "status": "Success"})

def field_images(driver, obj, test_flow_steps):
    # ── Step 13: Field Images ──────────────────────────────────────────
    with allure.step("13. Field Images"):
        time.sleep(2)
        if not smart_click(driver, "Field Images", obj.field_images_xpath):
            pytest.fail("Could not click Field Images")
        time.sleep(2)
        test_flow_steps.append({"step": "Field Images", "status": "Success"})

def media_files(driver, obj, test_flow_steps):
    # ── Step 14: Media files / Farmer updates ──────────────────────────
    with allure.step("14. Media files"):
        time.sleep(2)
        if not smart_click(driver, "Media Files", obj.media_files_xpath):
            pytest.fail("Could not click Media Files")
        time.sleep(2)
        test_flow_steps.append({"step": "Media Files", "status": "Success"})

def crop_info_icon(driver, obj, test_flow_steps):
    # ── Step 15: Crop info icon ────────────────────────────────────────
    with allure.step("15. Crop info icon"):
        time.sleep(2)
        if not smart_click(driver, "Crop Info", obj.crop_info_icon_xpath):
            pytest.fail("Could not click Crop Info")
        time.sleep(2)
        test_flow_steps.append({"step": "Crop Info", "status": "Success"})

def cross_icon(driver, obj, test_flow_steps):
    # ── Step 16: Cross icon ─────────────────────────────────────────────
     with allure.step("16. Cross icon"):
        time.sleep(2)
        if not smart_click(driver, "Cross icon", obj.cross_icon_xpath):
            pytest.fail("Could not click Cross icon")
        time.sleep(2)
        test_flow_steps.append({"step": "Cross Icon", "status": "Success"})

                    # with allure.step("17. Plus icon"):
                    #     time.sleep(2)
                    #     if not smart_click(driver, "Plus icon", obj.plus_icon_xpath):
                    #          pytest.fail("Could not click Plus icon")
                    #     time.sleep(2)
                    #     test_flow_steps.append({"step": "Plus Icon", "status": "Success"})

                    # with allure.step("18. Minus icon"):
                    #     time.sleep(2)
                    #     if not smart_click(driver, "Minus icon", obj.minus_icon_xpath):
                    #          pytest.fail("Could not click Minus icon")
                    #     time.sleep(2)
                    #     test_flow_steps.append({"step": "Minus Icon", "status": "Success"})
                    
def download_icon(driver, obj, test_flow_steps):
    with allure.step("17. Download icon"):
        time.sleep(2)
        if not smart_click(driver, "Download icon", obj.download_icon_xpath):
             pytest.fail("Could not click Download icon")
        time.sleep(2)
        test_flow_steps.append({"step": "Download Icon", "status": "Success"})

def play_audio_icon(driver, obj, test_flow_steps):
    with allure.step("18. Play audio icon"):
        time.sleep(2)
        if not smart_click(driver, "Play audio icon", obj.play_audio_icon_xpath):
             pytest.fail("Could not click Play audio icon")
        time.sleep(2)
        test_flow_steps.append({"step": "Play Audio Icon", "status": "Success"})

def pause_audio_icon(driver, obj, test_flow_steps):
    with allure.step("19. Pause audio icon"):
        time.sleep(2)
        if not smart_click(driver, "Pause audio icon", obj.pause_audio_icon_xpath):
             pytest.fail("Could not click Pause audio icon")
        time.sleep(2)
        test_flow_steps.append({"step": "Pause Audio Icon", "status": "Success"})

def start_video(driver, obj, test_flow_steps):
    with allure.step("22. Start video"):
        time.sleep(2)
        if not smart_click(driver, "Start video", obj.start_video_xpath):
             pytest.fail("Could not click Start video")
        time.sleep(2)
        test_flow_steps.append({"step": "Start Video", "status": "Success"})

def tab_on_video_play(driver, obj, test_flow_steps):
    with allure.step("22.1 Tab on video while playing"):
        time.sleep(2)
        if not smart_click(driver, "Tab on video play", obj.tab_on_video_play_xpath):
             pytest.fail("Could not click on video while playing")
        time.sleep(2)
        test_flow_steps.append({"step": "Tab on Video while Playing", "status": "Success"})


def stop_video(driver, obj, test_flow_steps):
    with allure.step("23. Stop video"):
        time.sleep(2)
        if not smart_click(driver, "Stop video", obj.stop_video_xpath):
             pytest.fail("Could not click Stop video")
        time.sleep(2)
        test_flow_steps.append({"step": "Stop Video", "status": "Success"})





            

                     

                
                   
