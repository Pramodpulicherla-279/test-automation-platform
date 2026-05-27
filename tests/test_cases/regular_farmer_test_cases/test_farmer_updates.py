from socket import timeout
import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import find_and_click, smart_click
import sys
from pages.regular_farmer_app.farmer_update_page import  load_locators_once, start_video, stop_video, tab_on_video_play
from pages.regular_farmer_app.farmer_update_page import (
    # click_humberger_menu,
    # click_historical_farms,
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
    # @allure.title("FC_001 -- farmer updates flow -- adding audio, video & image with comment and without comment")
    # def test_tc_001(self, driver):
    #     test_flow_steps = []

    #     try:
    #          # step - 1; click on active farm card
    #         click_active_farms(driver, self, test_flow_steps)
    #         click_navigation_button(driver, self, test_flow_steps)
    #         start_audio_recording(driver, self, test_flow_steps)
    #         stop_audio_recording(driver, self, test_flow_steps)
    #         start_video_recording(driver, self, test_flow_steps)
    #         stop_video_recording(driver, self, test_flow_steps)
    #         photo_capture_with_comment(driver, self, test_flow_steps)
    #         photo_capture_without_comment(driver, self, test_flow_steps)
    #         save_updates(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         profile_icon(driver, self, test_flow_steps)
    #         profile_button(driver, self, test_flow_steps)
    #         field_images(driver, self, test_flow_steps)
    #         media_files(driver, self, test_flow_steps)
    #         crop_info_icon(driver, self, test_flow_steps)
    #         cross_icon(driver, self, test_flow_steps)
    #         download_icon(driver, self, test_flow_steps)
    #         play_audio_icon(driver, self, test_flow_steps)
    #         pause_audio_icon(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
        
                    
    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/farmer_updates_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)


    # @allure.title("FC_002 -- Farmer Updates Flow -- Adding Audio")
    # def test_add_audio(self, driver):
    #     test_flow_steps = []

    #     try:
    #         # click_humburger_menu(driver, self, test_flow_steps)
    #         # click_historical_farms(driver, self, test_flow_steps)
    #         click_active_farms(driver, self, test_flow_steps)
    #         click_navigation_button(driver, self, test_flow_steps)
    #         start_audio_recording(driver, self, test_flow_steps)
    #         stop_audio_recording(driver, self, test_flow_steps)
    #         save_updates(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         profile_icon(driver, self, test_flow_steps)
    #         profile_button(driver, self, test_flow_steps)
    #         field_images(driver, self, test_flow_steps)
    #         media_files(driver, self, test_flow_steps)
    #         crop_info_icon(driver, self, test_flow_steps)
    #         cross_icon(driver, self, test_flow_steps)
    #         download_icon(driver, self, test_flow_steps)
    #         play_audio_icon(driver, self, test_flow_steps)
    #         pause_audio_icon(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)

    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/farmer_updates_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)


    # @allure.title("FC_003 -- Farmer Updates Flow -- Adding Video")
    # def test_add_video(self, driver):
    #     test_flow_steps = []

    #     try:
    #         # click_humburger_menu(driver, self, test_flow_steps)
    #         # click_historical_farms(driver, self, test_flow_steps)
    #         click_active_farms(driver, self, test_flow_steps)
    #         click_navigation_button(driver, self, test_flow_steps)
    #         start_video_recording(driver, self, test_flow_steps)
    #         stop_video_recording(driver, self, test_flow_steps)
    #         save_updates(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         profile_icon(driver, self, test_flow_steps)
    #         profile_button(driver, self, test_flow_steps)
    #         field_images(driver, self, test_flow_steps)
    #         media_files(driver, self, test_flow_steps)
    #         crop_info_icon(driver, self, test_flow_steps)
    #         cross_icon(driver, self, test_flow_steps)
    #         download_icon(driver, self, test_flow_steps)
    #         # play_audio_icon(driver, self, test_flow_steps)
    #         # pause_audio_icon(driver, self, test_flow_steps)
    #         start_video(driver, self, test_flow_steps)
    #         tab_on_video_play(driver, self, test_flow_steps)
    #         stop_video(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)

    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/farmer_updates_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)

    @allure.title("TC_001 -- add image with comment")
    def test_tc_001(self, driver):
        test_flow_steps = []

        try:
            # click_humburger_menu(driver, self, test_flow_steps)
            # click_historical_farms(driver, self, test_flow_steps)
            click_active_farms(driver, self, test_flow_steps)
            click_navigation_button(driver, self, test_flow_steps)
            photo_capture_with_comment(driver, self, test_flow_steps)
            save_updates(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/farmer_updates_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    @allure.title("TC_002 -- add image without comment")
    def test_tc_002(self, driver):
        test_flow_steps = []

        try:
            # click_humburger_menu(driver, self, test_flow_steps)
            # click_historical_farms(driver, self, test_flow_steps)
            click_active_farms(driver, self, test_flow_steps)
            click_navigation_button(driver, self, test_flow_steps)
            photo_capture_without_comment(driver, self, test_flow_steps)
            save_updates(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/farmer_updates_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    # @allure.title("TC_003 -- add image, video, audio")
    # def test_tc_003(self, driver):
    #     test_flow_steps = []

    #     try:
    #         # click_humburger_menu(driver, self, test_flow_steps)
    #         # click_historical_farms(driver, self, test_flow_steps)
    #         click_active_farms(driver, self, test_flow_steps)
    #         click_navigation_button(driver, self, test_flow_steps)
    #         photo_capture_without_comment(driver, self, test_flow_steps)
    #         save_updates(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)

    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/farmer_updates_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)

    # @allure.title("TC_004 -- add video, audio")
    # def test_tc_004(self, driver):
    #     test_flow_steps = []

    #     try:
    #         # click_humburger_menu(driver, self, test_flow_steps)
    #         # click_historical_farms(driver, self, test_flow_steps)
    #         click_active_farms(driver, self, test_flow_steps)
    #         click_navigation_button(driver, self, test_flow_steps)
    #         photo_capture_without_comment(driver, self, test_flow_steps)
    #         save_updates(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)

    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/farmer_updates_flow_success.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)

    @allure.title("TC_005 -- add audio")
    def test_tc_005(self, driver):
        test_flow_steps = []

        try:
            # click_humburger_menu(driver, self, test_flow_steps)
            # click_historical_farms(driver, self, test_flow_steps)
            click_active_farms(driver, self, test_flow_steps)
            click_navigation_button(driver, self, test_flow_steps)
            start_audio_recording(driver, self, test_flow_steps)
            stop_audio_recording(driver, self, test_flow_steps)
            save_updates(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/farmer_updates_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    @allure.title("TC_006 -- add image, audio")
    def test_tc_006(self, driver):
        test_flow_steps = []

        try:
            # click_humburger_menu(driver, self, test_flow_steps)
            # click_historical_farms(driver, self, test_flow_steps)
            click_active_farms(driver, self, test_flow_steps)
            click_navigation_button(driver, self, test_flow_steps)
            photo_capture_with_comment(driver, self, test_flow_steps)
            start_audio_recording(driver, self, test_flow_steps)
            stop_audio_recording(driver, self, test_flow_steps)
            save_updates(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/farmer_updates_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    # ─────────────────────────────────────────────────────────────────────────

   