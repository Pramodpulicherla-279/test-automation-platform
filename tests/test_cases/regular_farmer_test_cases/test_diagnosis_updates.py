# tests/test_diagnosis_updates.py
from socket import timeout
import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
import sys
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import find_and_click, smart_click
import sys
from pages.regular_farmer_app.diagnosis_updates_page import (

    click_camera_icon,
    load_locators_once,
    click_active_farms,
    click_diagnosis_button,
    click_first_ok_button,
    click_symptom_ok_button,
    click_secondary_symptom_ok_button,
    click_disease_confirm_button,
    click_curative_ok_button,
    start_audio_recording,
    start_general_remarks_audio,
    stop_audio_recording,
    start_video_recording,
    stop_general_remarks_audio,
    stop_video_recording,
    image_capture_icon,
    photo_capture_with_comment,
    enter_general_remarks,
    click_submit_button,
    click_profile_icon,
    click_profile_button,
    # click_diagnosis_tab,
    click_diagnosis_dropdown,
    select_first_media_item,

    android_back,
    photo_capture
)
from pages.regular_farmer_app.farmer_update_page import (
    crop_info_icon,
    cross_icon,
    download_icon,
    play_audio_icon,
    pause_audio_icon,
    start_video,
    stop_video,
    tab_on_video_play,
)

sys.dont_write_bytecode = True


@allure.epic("Diagnosis Updates Flow")
@allure.feature("Authentication")
class TestDiagnosisUpdates:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        load_locators_once(self, request)

    # @allure.story("Successful Diagnosis Updates")
    # @allure.title("TC_001 -- Diagnosis Updates with image, audio, and video")
    # def test_tc_001(self, driver):
    #     test_flow_steps = []
    #     try:
    #         # click_humburger_menu(driver, self, test_flow_steps)
    #         # click_historical_farms(driver, self, test_flow_steps)
    #         click_active_farms(driver, self, test_flow_steps)
    #         click_diagnosis_button(driver, self, test_flow_steps)
    #         click_first_ok_button(driver, self, test_flow_steps)
    #         click_symptom_ok_button(driver, self, test_flow_steps)
    #         click_secondary_symptom_ok_button(driver, self, test_flow_steps)
    #         click_disease_confirm_button(driver, self, test_flow_steps)
    #         click_curative_ok_button(driver, self, test_flow_steps)
    #         start_audio_recording(driver, self, test_flow_steps)
    #         stop_audio_recording(driver, self, test_flow_steps)
    #         click_camera_icon(driver, self, test_flow_steps)
    #         start_video_recording(driver, self, test_flow_steps)
    #         stop_video_recording(driver, self, test_flow_steps)
    #         click_camera_icon(driver, self, test_flow_steps)
    #         image_capture_icon(driver, self, test_flow_steps)
    #         photo_capture(driver, self, test_flow_steps)
    #         enter_general_remarks(driver, self, test_flow_steps)
    #         start_general_remarks_audio(driver, self, test_flow_steps)
    #         stop_general_remarks_audio(driver, self, test_flow_steps)
    #         click_submit_button(driver, self, test_flow_steps)
    #         click_profile_icon(driver, self, test_flow_steps)
    #         click_profile_button(driver, self, test_flow_steps)
    #         # click_diagnosis_tab(driver, self, test_flow_steps)
    #         click_diagnosis_dropdown(driver, self, test_flow_steps)
    #         # select_audio_from_dropdown(driver, self, test_flow_steps)
    #         select_first_media_item(driver, self, test_flow_steps)
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
    #         with open("test-flows/diagnosis_updates_flow.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)


    # @allure.title("TC_002 -- Diagnosis Updates with audio ")
    # def test_tc_002(self, driver):
    #     test_flow_steps = []
    #     try:
    #         click_active_farms(driver, self, test_flow_steps)
    #         click_diagnosis_button(driver, self, test_flow_steps)
    #         click_first_ok_button(driver, self, test_flow_steps)
    #         click_symptom_ok_button(driver, self, test_flow_steps)
    #         click_secondary_symptom_ok_button(driver, self, test_flow_steps)
    #         click_disease_confirm_button(driver, self, test_flow_steps)
    #         click_curative_ok_button(driver, self, test_flow_steps)
    #         start_audio_recording(driver, self, test_flow_steps)
    #         stop_audio_recording(driver, self, test_flow_steps)
    #         click_submit_button(driver, self, test_flow_steps)
    #         click_profile_icon(driver, self, test_flow_steps)
    #         click_profile_button(driver, self, test_flow_steps)
    #         # click_diagnosis_tab(driver, self, test_flow_steps)
    #         click_diagnosis_dropdown(driver, self, test_flow_steps)
    #         select_first_media_item(driver, self, test_flow_steps)
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
    #         with open("test-flows/diagnosis_updates_flow.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)

    # @allure.title("TC_003 -- Diagnosis Updates with video ")
    # def test_tc_003(self, driver):
    #     test_flow_steps = []
    #     try:
    #         click_active_farms(driver, self, test_flow_steps)
    #         click_diagnosis_button(driver, self, test_flow_steps)
    #         click_first_ok_button(driver, self, test_flow_steps)
    #         click_symptom_ok_button(driver, self, test_flow_steps)
    #         click_secondary_symptom_ok_button(driver, self, test_flow_steps)
    #         click_disease_confirm_button(driver, self, test_flow_steps)
    #         click_curative_ok_button(driver, self, test_flow_steps)
    #         click_camera_icon(driver, self, test_flow_steps)
    #         start_video_recording(driver, self, test_flow_steps)
    #         stop_video_recording(driver, self, test_flow_steps)
    #         click_submit_button(driver, self, test_flow_steps)
    #         click_profile_icon(driver, self, test_flow_steps)
    #         click_profile_button(driver, self, test_flow_steps)
    #         click_diagnosis_dropdown(driver, self, test_flow_steps)
    #         select_first_media_item(driver, self, test_flow_steps)
    #         crop_info_icon(driver, self, test_flow_steps)
    #         cross_icon(driver, self, test_flow_steps)
    #         download_icon(driver, self, test_flow_steps)
    #         start_video(driver, self, test_flow_steps)
    #         # tab_on_video_play(driver, self, test_flow_steps)
    #         # stop_video(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #         android_back(driver, self, test_flow_steps)
    #     finally:
    #         os.makedirs("test-flows", exist_ok=True)
    #         with open("test-flows/diagnosis_updates_flow.json", "w") as f:
    #             json.dump(test_flow_steps, f, indent=4)

    @allure.title("TC_004 -- Diagnosis Updates with image with comment ")
    def test_tc_004(self, driver):
        test_flow_steps = []
        try:
            click_active_farms(driver, self, test_flow_steps)
            click_diagnosis_button(driver, self, test_flow_steps)
            click_first_ok_button(driver, self, test_flow_steps)
            click_symptom_ok_button(driver, self, test_flow_steps)
            click_secondary_symptom_ok_button(driver, self, test_flow_steps)
            click_disease_confirm_button(driver, self, test_flow_steps)
            click_curative_ok_button(driver, self, test_flow_steps)
            click_camera_icon(driver, self, test_flow_steps)
            image_capture_icon(driver, self, test_flow_steps)
            photo_capture_with_comment(driver, self, test_flow_steps)
            click_submit_button(driver, self, test_flow_steps)
            click_profile_icon(driver, self, test_flow_steps)
            click_profile_button(driver, self, test_flow_steps)
            click_diagnosis_dropdown(driver, self, test_flow_steps)
            select_first_media_item(driver, self, test_flow_steps)
            crop_info_icon(driver, self, test_flow_steps)
            cross_icon(driver, self, test_flow_steps)
            download_icon(driver, self, test_flow_steps)
    
        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/diagnosis_updates_flow.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)

    @allure.title("TC_007 -- Diagnosis Updates with audio & video ")
    def test_tc_007(self, driver):
        test_flow_steps = []
        try:
            click_diagnosis_button(driver, self, test_flow_steps)
            click_first_ok_button(driver, self, test_flow_steps)
            click_symptom_ok_button(driver, self, test_flow_steps)
            click_secondary_symptom_ok_button(driver, self, test_flow_steps)
            click_disease_confirm_button(driver, self, test_flow_steps)
            click_curative_ok_button(driver, self, test_flow_steps)
            start_audio_recording(driver, self, test_flow_steps)
            stop_audio_recording(driver, self, test_flow_steps)
            click_camera_icon(driver, self, test_flow_steps)  
            start_video_recording(driver, self, test_flow_steps)
            stop_video_recording(driver, self, test_flow_steps)
            click_submit_button(driver, self, test_flow_steps)
            click_profile_icon(driver, self, test_flow_steps)
            click_profile_button(driver, self, test_flow_steps)
            click_diagnosis_dropdown(driver, self, test_flow_steps)
            select_first_media_item(driver, self, test_flow_steps)
            crop_info_icon(driver, self, test_flow_steps)
            cross_icon(driver, self, test_flow_steps)
            download_icon(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
    
        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/diagnosis_updates_flow.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)     


    @allure.title("TC_006 -- Diagnosis Updates without general remarks ")
    def test_tc_006(self, driver):
        test_flow_steps = []
        try:
            click_diagnosis_button(driver, self, test_flow_steps)
            click_first_ok_button(driver, self, test_flow_steps)
            click_symptom_ok_button(driver, self, test_flow_steps)
            click_secondary_symptom_ok_button(driver, self, test_flow_steps)
            click_disease_confirm_button(driver, self, test_flow_steps)
            click_curative_ok_button(driver, self, test_flow_steps)
            start_audio_recording(driver, self, test_flow_steps)
            stop_audio_recording(driver, self, test_flow_steps)
            click_camera_icon(driver, self, test_flow_steps)
            start_video_recording(driver, self, test_flow_steps)
            stop_video_recording(driver, self, test_flow_steps)
            click_camera_icon(driver, self, test_flow_steps)
            image_capture_icon(driver, self, test_flow_steps)
            photo_capture_with_comment(driver, self, test_flow_steps)       
            click_submit_button(driver, self, test_flow_steps)
            click_profile_icon(driver, self, test_flow_steps)
            click_profile_button(driver, self, test_flow_steps)
            click_diagnosis_dropdown(driver, self, test_flow_steps)
            select_first_media_item(driver, self, test_flow_steps)
            crop_info_icon(driver, self, test_flow_steps)
            cross_icon(driver, self, test_flow_steps)
            download_icon(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
    
        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/diagnosis_updates_flow.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)  


    @allure.title("TC_007 -- Diagnosis Updates with image & video ")
    def test_tc_007(self, driver):
        test_flow_steps = []
        try:
            click_diagnosis_button(driver, self, test_flow_steps)
            click_first_ok_button(driver, self, test_flow_steps)
            click_symptom_ok_button(driver, self, test_flow_steps)
            click_secondary_symptom_ok_button(driver, self, test_flow_steps)
            click_disease_confirm_button(driver, self, test_flow_steps)
            click_curative_ok_button(driver, self, test_flow_steps)
            click_camera_icon(driver, self, test_flow_steps)
            start_video_recording(driver, self, test_flow_steps)
            stop_video_recording(driver, self, test_flow_steps)
            click_camera_icon(driver, self, test_flow_steps)
            image_capture_icon(driver, self, test_flow_steps)
            click_submit_button(driver, self, test_flow_steps)
            click_profile_icon(driver, self, test_flow_steps)
            click_profile_button(driver, self, test_flow_steps)
            click_diagnosis_dropdown(driver, self, test_flow_steps)
            select_first_media_item(driver, self, test_flow_steps)
            crop_info_icon(driver, self, test_flow_steps)
            cross_icon(driver, self, test_flow_steps)
            download_icon(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
    
        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/diagnosis_updates_flow.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)


    @allure.title("TC_008 -- Diagnosis Updates with image & audio")
    def test_tc_008(self, driver):
        test_flow_steps = []
        try:
            click_diagnosis_button(driver, self, test_flow_steps)
            click_first_ok_button(driver, self, test_flow_steps)
            click_symptom_ok_button(driver, self, test_flow_steps)
            click_secondary_symptom_ok_button(driver, self, test_flow_steps)
            click_disease_confirm_button(driver, self, test_flow_steps)
            click_curative_ok_button(driver, self, test_flow_steps)
            start_audio_recording(driver, self, test_flow_steps)
            stop_audio_recording(driver, self, test_flow_steps)
            click_camera_icon(driver, self, test_flow_steps)
            image_capture_icon(driver, self, test_flow_steps)
            photo_capture_with_comment(driver, self, test_flow_steps)       
            click_submit_button(driver, self, test_flow_steps)
            click_profile_icon(driver, self, test_flow_steps)
            click_profile_button(driver, self, test_flow_steps)
            click_diagnosis_dropdown(driver, self, test_flow_steps)
            select_first_media_item(driver, self, test_flow_steps)
            crop_info_icon(driver, self, test_flow_steps)
            cross_icon(driver, self, test_flow_steps)
            download_icon(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
    
        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/diagnosis_updates_flow.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)
