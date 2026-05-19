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
from pages.state_farmer_app.farmer_updates_pages import  load_locators_once, start_video, stop_video, tab_on_video_play
from pages.state_farmer_app.farmer_updates_pages import (
    
    click_active_farms,
    click_navigation_button,
    start_audio_recording,
    stop_audio_recording,
    start_video_recording,
    stop_video_recording,
    photo_capture_with_comment,
    photo_capture_without_comment,
    save_updates,
    android_back,
    profile_icon,
    profile_button,
    field_images,
    media_files,
    crop_info_icon,
    cross_icon,
    download_icon,
    play_audio_icon,
    pause_audio_icon

)

sys.dont_write_bytecode = True



@allure.epic("farmer updates Flow")
@allure.feature("Authentication")
class TestFarmer:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        load_locators_once(self, request)
    # ─────────────────────────────────────────────────────────────────────────
    @allure.story("Successful Farmer Updates")
    @allure.title("FC_001 -- farmer updates flow -- adding audio, video & image with comment and without comment")
    def test_addfarm(self, driver):
        test_flow_steps = []

        try:
             # step - 1; click on active farm card
            click_active_farms(driver, self, test_flow_steps)
            click_navigation_button(driver, self, test_flow_steps)
            start_audio_recording(driver, self, test_flow_steps)
            stop_audio_recording(driver, self, test_flow_steps)
            start_video_recording(driver, self, test_flow_steps)
            stop_video_recording(driver, self, test_flow_steps)
            photo_capture_with_comment(driver, self, test_flow_steps)
            photo_capture_without_comment(driver, self, test_flow_steps)
            save_updates(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            profile_icon(driver, self, test_flow_steps)
            profile_button(driver, self, test_flow_steps)
            field_images(driver, self, test_flow_steps)
            media_files(driver, self, test_flow_steps)
            crop_info_icon(driver, self, test_flow_steps)
            cross_icon(driver, self, test_flow_steps)
            download_icon(driver, self, test_flow_steps)
            play_audio_icon(driver, self, test_flow_steps)
            pause_audio_icon(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
        
                    
        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/onboarding_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)


    @allure.title("FC_002 -- Farmer Updates Flow -- Adding Audio")
    def test_add_audio(self, driver):
        test_flow_steps = []

        try:
           
            click_active_farms(driver, self, test_flow_steps)
            click_navigation_button(driver, self, test_flow_steps)
            start_audio_recording(driver, self, test_flow_steps)
            stop_audio_recording(driver, self, test_flow_steps)
            save_updates(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            profile_icon(driver, self, test_flow_steps)
            profile_button(driver, self, test_flow_steps)
            field_images(driver, self, test_flow_steps)
            media_files(driver, self, test_flow_steps)
            crop_info_icon(driver, self, test_flow_steps)
            cross_icon(driver, self, test_flow_steps)
            download_icon(driver, self, test_flow_steps)
            play_audio_icon(driver, self, test_flow_steps)
            pause_audio_icon(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/onboarding_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)


    @allure.title("FC_003 -- Farmer Updates Flow -- Adding Video")
    def test_add_video(self, driver):
        test_flow_steps = []

        try:
          
            click_active_farms(driver, self, test_flow_steps)
            click_navigation_button(driver, self, test_flow_steps)
            start_video_recording(driver, self, test_flow_steps)
            stop_video_recording(driver, self, test_flow_steps)
            save_updates(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            profile_icon(driver, self, test_flow_steps)
            profile_button(driver, self, test_flow_steps)
            field_images(driver, self, test_flow_steps)
            media_files(driver, self, test_flow_steps)
            crop_info_icon(driver, self, test_flow_steps)
            cross_icon(driver, self, test_flow_steps)
            download_icon(driver, self, test_flow_steps)
            # play_audio_icon(driver, self, test_flow_steps)
            # pause_audio_icon(driver, self, test_flow_steps)
            start_video(driver, self, test_flow_steps)
            tab_on_video_play(driver, self, test_flow_steps)
            stop_video(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/onboarding_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    # ─────────────────────────────────────────────────────────────────────────

    # @allure.title("crop health > farmer updates flow")
    # def test_addfarm(self, driver):
    #     test_flow_steps = []

    #     try:
    #                 # ── Step 1: Click on active farms ──────────────────────────────────
    #                 with allure.step("1. Click on active farms"):
    #                     time.sleep(2)
    #                     if not smart_click(driver, "Click on active farms", self.active_farms_xpath):
    #                         pytest.fail("Could not find or click the 'active farms' button.")
    #                     time.sleep(2)
    #                     test_flow_steps.append({"step": "Click on active farms", "status": "Success"})


    #                 # ── Step 2: Navigation button ──────────────────────────────────────
    #                 with allure.step("2. Navigation button"):
    #                     time.sleep(2)
    #                     if not smart_click(driver, "Navigation button", self.navigation_button_xpath):
    #                         pytest.fail("Could not find or click the 'navigation button'.")
    #                     time.sleep(2)
    #                     test_flow_steps.append({"step": "Navigation button", "status": "Success"})


    #                 # ── Step 3: Start audio recording ──────────────────────────────────
    #                 with allure.step("3. Start audio recording"):
    #                     time.sleep(2)
    #                     if not smart_click(driver, "Start audio", self.start_audio_xpath):
    #                         pytest.fail("Could not click 'start audio'.")
    #                     time.sleep(3)
    #                     test_flow_steps.append({"step": "Start Audio Recording", "status": "Success"})


    #                 # ── Step 4: Stop audio recording ───────────────────────────────────
    #                 with allure.step("4. Stop audio recording"):
    #                     time.sleep(2)
    #                     if not smart_click(driver, "Stop audio", self.stop_audio_xpath):
    #                         pytest.fail("Could not click 'stop audio'.")
    #                     time.sleep(3)
    #                     test_flow_steps.append({"step": "Stop Audio Recording", "status": "Success"})

    #                 # ── Step 9: Save button ────────────────────────────────────────────
    #                 with allure.step("9. Save button"):
    #                     time.sleep(2)
    #                     if not smart_click(driver, "Save", self.navigation_save_button_xpath):
    #                         pytest.fail("Could not click 'Save'")
    #                     time.sleep(2)
    #                     test_flow_steps.append({"step": "Save Button", "status": "Success"})


    #                 # ── Step 10: Android back ──────────────────────────────────────────
    #                 with allure.step("10. Android back"):
    #                     time.sleep(2)
    #                     if not self._android_back(driver):
    #                         pytest.fail("Failed Android back")
    #                     time.sleep(2)
    #                     test_flow_steps.append({"step": "Android back", "status": "Success"})

    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/onboarding_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)
   