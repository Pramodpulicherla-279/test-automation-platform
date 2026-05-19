# pages/regular_farmer_app/diagnosis_updates_page.py

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

# ─────────────────────────────────────────────────────────────
# Load Locators
# ─────────────────────────────────────────────────────────────

def load_locators_once(self, request):

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    locators_path = os.path.join(project_root, "locators", "state_farmer.json")

    with open(locators_path, "r", encoding="utf-8") as f:
        xpaths = json.load(f)

    diagnosis_xpaths = xpaths.get("Diagnosis_updates", {})

    request.cls.click_active_farms_xpath = diagnosis_xpaths.get("active_farms")
    # request.cls.hamburger_menu_xpath = diagnosis_xpaths.get("hamburger_menu")
    # request.cls.historical_farms_xpath = diagnosis_xpaths.get("historical_farms")
    request.cls.click_diagnosis_xpath = diagnosis_xpaths.get("diagnosis_tab")
    request.cls.click_first_ok_button_xpath = diagnosis_xpaths.get("click_first_ok_button")
    request.cls.click_symptom_ok_button_xpath = diagnosis_xpaths.get("click_Symptom_ok_button")
    request.cls.click_secondary_symptom_ok_button_xpath = diagnosis_xpaths.get("click_secondary_sysmptom_ok_button")
    request.cls.click_disease_confirm_button_xpath = diagnosis_xpaths.get("click_Disease_confirm_button")
    request.cls.click_curative_ok_button_xpath = diagnosis_xpaths.get("click_curative_ok_button")

    request.cls.image_desc_audio_input_xpath = diagnosis_xpaths.get("main_audio_start")
    request.cls.image_desc_audio_stop_xpath = diagnosis_xpaths.get("main_audio_stop")
    request.cls.camera_icon_xpath = diagnosis_xpaths.get("camera_icon")
    request.cls.image_desc_video_start_xpath = diagnosis_xpaths.get("video_start")
    request.cls.image_desc_video_stop_xpath = diagnosis_xpaths.get("video_stop")

    request.cls.image_desc_photo_capture_xpath = diagnosis_xpaths.get("image_capture_icon")
    request.cls.image_desc_photo_capture_comment_xpath = diagnosis_xpaths.get("image_comment_input")
    request.cls.image_desc_photo_capture_save_xpath = diagnosis_xpaths.get("image_save_button")

    request.cls.image_desc_general_remarks_xpath = diagnosis_xpaths.get("general_remarks_commentbox")

    request.cls.image_desc_submit_button_xpath = diagnosis_xpaths.get("submit_button")

    request.cls.profile_icon_xpath = diagnosis_xpaths.get("profile_icon")
    request.cls.profile_button_xpath = diagnosis_xpaths.get("profile_button")

    request.cls.profile_diagnosis_tab_xpath = diagnosis_xpaths.get("profile_diagnosis_tab")
    request.cls.profile_diagnosis_dropdown_xpath = diagnosis_xpaths.get("profile_diagnosis_dropdown")


# ─────────────────────────────────────────────────────────────
# Active Farms
# ─────────────────────────────────────────────────────────────

# def click_humburger_menu(driver, obj, test_flow_steps):

#     with allure.step("Click Hamburger Menu"):

#         time.sleep(2)

#         if not smart_click(driver, "Hamburger Menu", obj.hamburger_menu_xpath):
#             pytest.fail("Could not click Hamburger Menu")

#         time.sleep(2)

#         test_flow_steps.append({"step": "Click Hamburger Menu", "status": "Success"})

# def click_historical_farms(driver, obj, test_flow_steps):

#     with allure.step("Click Historical Farms"):

#         time.sleep(2)

#         if not smart_click(driver, "Historical Farms", obj.historical_farms_xpath):
#             pytest.fail("Could not click Historical Farms")

#         time.sleep(2)

#         test_flow_steps.append({"step": "Click Historical Farms", "status": "Success"})


def click_active_farms(driver, obj, test_flow_steps):

    with allure.step("Click Active Farms"):

        time.sleep(2)

        if not smart_click(driver, "Active Farms", obj.click_active_farms_xpath):
            pytest.fail("Could not click Active Farms")

        time.sleep(2)

        test_flow_steps.append({"step": "Click Active Farms", "status": "Success"})


# ─────────────────────────────────────────────────────────────
# Diagnosis Button
# ─────────────────────────────────────────────────────────────

def click_diagnosis_button(driver, obj, test_flow_steps):

    with allure.step("Click Diagnosis Button"):

        time.sleep(2)

        if not smart_click(driver, "Diagnosis Button", obj.click_diagnosis_xpath):
            pytest.fail("Could not click Diagnosis Button")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Diagnosis Button",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# First OK Button
# ─────────────────────────────────────────────────────────────

def click_first_ok_button(driver, obj, test_flow_steps):

    with allure.step("Click First OK Button"):

        time.sleep(2)

        if not smart_click(driver, "First OK Button", obj.click_first_ok_button_xpath):
            pytest.fail("Could not click First OK Button")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click First OK Button",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Symptom OK Button
# ─────────────────────────────────────────────────────────────

def click_symptom_ok_button(driver, obj, test_flow_steps):

    with allure.step("Click Symptom OK Button"):

        time.sleep(2)

        if not smart_click(driver, "Symptom OK Button", obj.click_symptom_ok_button_xpath):
            pytest.fail("Could not click Symptom OK Button")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Symptom OK Button",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Secondary Symptom OK Button
# ─────────────────────────────────────────────────────────────

def click_secondary_symptom_ok_button(driver, obj, test_flow_steps):

    with allure.step("Click Secondary Symptom OK Button"):

        time.sleep(2)

        if not smart_click(driver, "Secondary Symptom OK Button", obj.click_secondary_symptom_ok_button_xpath):
            pytest.fail("Could not click Secondary Symptom OK Button")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Secondary Symptom OK Button",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Disease Confirm Button
# ─────────────────────────────────────────────────────────────

def click_disease_confirm_button(driver, obj, test_flow_steps):

    with allure.step("Click Disease Confirm Button"):

        time.sleep(2)

        if not smart_click(driver, "Disease Confirm Button", obj.click_disease_confirm_button_xpath):
            pytest.fail("Could not click Disease Confirm Button")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Disease Confirm Button",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Curative OK Button
# ─────────────────────────────────────────────────────────────

def click_curative_ok_button(driver, obj, test_flow_steps):

    with allure.step("Click Curative OK Button"):

        time.sleep(2)

        if not smart_click(driver, "Curative OK Button", obj.click_curative_ok_button_xpath):
            pytest.fail("Could not click Curative OK Button")

        time.sleep(5)

        test_flow_steps.append({
            "step": "Click Curative OK Button",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Start Audio Recording
# ─────────────────────────────────────────────────────────────

def start_audio_recording(driver, obj, test_flow_steps):

    with allure.step("Start Audio Recording"):

        if not smart_click(driver, "Audio Start", obj.image_desc_audio_input_xpath):
            pytest.fail("Could not start audio recording")

        time.sleep(3)

        test_flow_steps.append({
            "step": "Start Audio Recording",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Stop Audio Recording
# ─────────────────────────────────────────────────────────────

def stop_audio_recording(driver, obj, test_flow_steps):

    with allure.step("Stop Audio Recording"):

        time.sleep(2)

        if not smart_click(driver, "Audio Stop", obj.image_desc_audio_stop_xpath):
            pytest.fail("Could not stop audio recording")

        time.sleep(3)

        test_flow_steps.append({
            "step": "Stop Audio Recording",
            "status": "Success"
        })

def click_camera_icon(driver, obj, test_flow_steps):

    with allure.step("Click Camera Icon"):

        time.sleep(2)

        if not smart_click(driver, "Camera Icon", obj.camera_icon_xpath):
            pytest.fail("Could not click Camera Icon")

        time.sleep(3)

        test_flow_steps.append({
            "step": "Click Camera Icon",
            "status": "Success"
        })



# ─────────────────────────────────────────────────────────────
# Start Video Recording
# ─────────────────────────────────────────────────────────────
def start_video_recording(driver, obj, test_flow_steps):

    with allure.step("Start Video Recording"):

        time.sleep(5)

        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, obj.image_desc_video_start_xpath)
            )
        )

        element.click()

        time.sleep(10)

        test_flow_steps.append({
            "step": "Start Video Recording",
            "status": "Success"
        })

# ─────────────────────────────────────────────────────────────
# Stop Video Recording
# ─────────────────────────────────────────────────────────────

def stop_video_recording(driver, obj, test_flow_steps):

    with allure.step("Stop Video Recording"):

        time.sleep(2)

        if not smart_click(driver, "Video Stop", obj.image_desc_video_stop_xpath):
            pytest.fail("Could not stop video recording")

        time.sleep(3)

        test_flow_steps.append({
            "step": "Stop Video Recording",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Photo Capture With Comment
# ─────────────────────────────────────────────────────────────
def image_capture_icon(driver, obj, test_flow_steps):

    with allure.step("Click Image Capture Icon"):

        time.sleep(2)

        if not smart_click(driver, "Image Capture Icon", obj.image_desc_photo_capture_xpath):
            pytest.fail("Could not click Image Capture Icon")

        time.sleep(3)

        test_flow_steps.append({
            "step": "Click Image Capture Icon",
            "status": "Success"
        })
def photo_capture_with_comment(driver, obj, test_flow_steps):

    with allure.step("Photo Capture With Comment"):

        time.sleep(2)

        comment_box = driver.find_element(
            AppiumBy.XPATH,
            obj.image_desc_photo_capture_comment_xpath
        )

        comment_box.send_keys("Diagnosis Photo Comment")

        if not smart_click(driver, "Save Photo", obj.image_desc_photo_capture_save_xpath):
            pytest.fail("Could not save photo")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Photo Capture With Comment",
            "status": "Success"
        })



# ─────────────────────────────────────────────────────────────
# General Remarks
# ─────────────────────────────────────────────────────────────

def enter_general_remarks(driver, obj, test_flow_steps):

    with allure.step("Enter General Remarks"):

        time.sleep(2)

        remarks_box = driver.find_element(
            AppiumBy.XPATH,
            obj.image_desc_general_remarks_xpath
        )

        remarks_box.send_keys("Diagnosis General Remarks")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Enter General Remarks",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Submit Button
# ─────────────────────────────────────────────────────────────

def click_submit_button(driver, obj, test_flow_steps):

    with allure.step("Click Submit Button"):

        time.sleep(2)

        if not smart_click(driver, "Submit Button", obj.image_desc_submit_button_xpath):
            pytest.fail("Could not click Submit Button")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Submit Button",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Profile Icon
# ─────────────────────────────────────────────────────────────

def click_profile_icon(driver, obj, test_flow_steps):

    with allure.step("Click Profile Icon"):

        time.sleep(2)

        if not smart_click(driver, "Profile Icon", obj.profile_icon_xpath):
            pytest.fail("Could not click Profile Icon")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Profile Icon",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Profile Button
# ─────────────────────────────────────────────────────────────

def click_profile_button(driver, obj, test_flow_steps):

    with allure.step("Click Profile Button"):

        time.sleep(2)

        if not smart_click(driver, "Profile Button", obj.profile_button_xpath):
            pytest.fail("Could not click Profile Button")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Profile Button",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Diagnosis Tab
# ─────────────────────────────────────────────────────────────

def click_diagnosis_tab(driver, obj, test_flow_steps):

    with allure.step("Click Diagnosis Tab"):

        time.sleep(2)

        if not smart_click(driver, "Diagnosis Tab", obj.profile_diagnosis_tab_xpath):
            pytest.fail("Could not click Diagnosis Tab")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Diagnosis Tab",
            "status": "Success"
        })


# ─────────────────────────────────────────────────────────────
# Diagnosis Dropdown
# ─────────────────────────────────────────────────────────────

def click_diagnosis_dropdown(driver, obj, test_flow_steps):

    with allure.step("Click Diagnosis Dropdown"):

        time.sleep(2)

        if not smart_click(driver, "Diagnosis Dropdown", obj.profile_diagnosis_dropdown_xpath):
            pytest.fail("Could not click Diagnosis Dropdown")

        time.sleep(2)

        test_flow_steps.append({
            "step": "Click Diagnosis Dropdown",
            "status": "Success"
        })

def select_audio_from_dropdown(driver, obj, test_flow_steps):

    with allure.step("Scroll and select Audio"):

        time.sleep(2)

        if not smart_click(
            driver,
            "Audio Option",
            obj.stop_audio,
            "Audio",
            screenshot_path="screenshots/audio_option.png",
            force_ocr=False,
            ocr_attempts=3
        ):
            pytest.fail("Could not click Audio option")

        test_flow_steps.append({
            "step": "Select Audio from dropdown",
            "status": "Success"
        })
# ─────────────────────────────────────────────────────────────
# Android Back
# ─────────────────────────────────────────────────────────────

def android_back(driver, obj, test_flow_steps):

    with allure.step("Android Back"):

        if not android_back_func(driver):
            pytest.fail("Failed Android Back")

        test_flow_steps.append({
            "step": "Android Back",
            "status": "Success"
        })