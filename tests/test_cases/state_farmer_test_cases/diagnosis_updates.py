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
from pages.state_farmer_app.diagnosis_updates_pages import (

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
    stop_audio_recording,
    start_video_recording,
    stop_video_recording,
    image_capture_icon,
    photo_capture_with_comment,
    enter_general_remarks,
    click_submit_button,
    click_profile_icon,
    click_profile_button,
    click_diagnosis_tab,
    click_diagnosis_dropdown,
    android_back
)

sys.dont_write_bytecode = True


@allure.epic("Diagnosis Updates Flow")
@allure.feature("Authentication")
class TestDiagnosisUpdates:


    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):

        load_locators_once(self, request)


    @allure.story("Successful Diagnosis Updates")
    @allure.title("DC_001 -- Diagnosis Updates Flow")
    def test_diagnosis_updates(self, driver):

        test_flow_steps = []

        try:
            # click_humburger_menu(driver, self, test_flow_steps)
            # click_historical_farms(driver, self, test_flow_steps)
            click_active_farms(driver, self, test_flow_steps)

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

            # image_save_button(driver, self, test_flow_steps)

            

            enter_general_remarks(driver, self, test_flow_steps)

            click_submit_button(driver, self, test_flow_steps)

            click_profile_icon(driver, self, test_flow_steps)

            click_profile_button(driver, self, test_flow_steps)

            click_diagnosis_tab(driver, self, test_flow_steps)

            click_diagnosis_dropdown(driver, self, test_flow_steps)

            android_back(driver, self, test_flow_steps)

            android_back(driver, self, test_flow_steps)


        finally:

            os.makedirs("test-flows", exist_ok=True)

            with open("test-flows/diagnosis_updates_flow.json", "w") as f:

                json.dump(test_flow_steps, f, indent=4)


    @allure.title("DC_002 -- Diagnosis Updates audio recording ")
    def test_audio_recording(self, driver):  

        test_flow_steps = []

        try:
            # click_humburger_menu(driver, self, test_flow_steps)
            # click_historical_farms(driver, self, test_flow_steps)
            click_active_farms(driver, self, test_flow_steps)

            click_diagnosis_button(driver, self, test_flow_steps)

            click_first_ok_button(driver, self, test_flow_steps)

            click_symptom_ok_button(driver, self, test_flow_steps)

            click_secondary_symptom_ok_button(driver, self, test_flow_steps)

            click_disease_confirm_button(driver, self, test_flow_steps)

            click_curative_ok_button(driver, self, test_flow_steps)

            start_audio_recording(driver, self, test_flow_steps)

            stop_audio_recording(driver, self, test_flow_steps)

            # click_camera_icon(driver, self, test_flow_steps)

            # start_video_recording(driver, self, test_flow_steps)

            # stop_video_recording(driver, self, test_flow_steps)

            # click_camera_icon(driver, self, test_flow_steps)


            # image_capture_icon(driver, self, test_flow_steps)
        

            # photo_capture_with_comment(driver, self, test_flow_steps)

            # enter_general_remarks(driver, self, test_flow_steps)

            click_submit_button(driver, self, test_flow_steps)

            click_profile_icon(driver, self, test_flow_steps)

            click_profile_button(driver, self, test_flow_steps)

            click_diagnosis_tab(driver, self, test_flow_steps)

            click_diagnosis_dropdown(driver, self, test_flow_steps)

            android_back(driver, self, test_flow_steps)

            android_back(driver, self, test_flow_steps)


        finally:

            os.makedirs("test-flows", exist_ok=True)

            with open("test-flows/diagnosis_updates_flow.json", "w") as f:

                json.dump(test_flow_steps, f, indent=4)