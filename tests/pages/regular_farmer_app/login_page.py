import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_click
import json
import os
import sys
import re
sys.dont_write_bytecode = True

def load_locators_once(self, request):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    locators_path = os.path.join(project_root, "locators", "state_farmer.json")
    with open(locators_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    raw = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', raw)
    xpaths = json.loads(raw)

    # ── Login ───────────────────────────────────────
    login_screen_xpaths = xpaths.get("login_screen", {})

    #login_screen
    request.cls.language_next_xpath = login_screen_xpaths.get("next_button_language_login")
    request.cls.allow_picture_button_xpath = login_screen_xpaths.get("allow_picture_button")
    request.cls.allow_location_button_xpath = login_screen_xpaths.get("allow_location_button")
    request.cls.allow_audio_button_xpath = login_screen_xpaths.get("allow_audio_button")    
    request.cls.allow_notifications_button_xpath = login_screen_xpaths.get("allow_notifications_button")
    request.cls.phone_number_input_xpath = login_screen_xpaths.get("phone_number_input")
    request.cls.next_button_login_xpath = login_screen_xpaths.get("next_button_login")
    request.cls.verify_button_login_xpath = login_screen_xpaths.get("verify_button_login")

####Login flow test cases
def login_success(driver, obj, test_flow_steps):
    with allure.step("1. Next button on language selection screen"):
        # Use smart_click for robust finding (XPath -> DOM Text -> OCR)
        if not smart_click(driver, "Next Button (Language)", obj.language_next_xpath, "Next"):
            pytest.fail("Could not find or click the 'Next button on language selection' button.")
        test_flow_steps.append({"step": "Click Next button on language selection", "status": "Success"})

def login_permissions(driver, obj, test_flow_steps):      
    with allure.step("2. Allow picture"):
        if not smart_click(driver, "While using the app (allow picture)", obj.allow_picture_button_xpath, "While using the app"):
            pytest.fail("Could not find or click the 'Allow picture' button.")
        test_flow_steps.append({"step": "Allow picture permission", "status": "Success"})

def login_permissions_location(driver, obj, test_flow_steps):   
    with allure.step("3. Allow location"):
        if not smart_click(driver, "While using (allow location)", obj.allow_location_button_xpath, "While using"):
            pytest.fail("Could not find or click the 'Allow location' button.")
        test_flow_steps.append({"step": "Allow location permission", "status": "Success"})

def login_permissions_audio(driver, obj, test_flow_steps):
    with allure.step("4. Allow audio"):
        if not smart_click(driver, "While using the app (allow audio)", obj.allow_audio_button_xpath, "While using the app"):
            pytest.fail("Could not find or click the 'Allow audio' button.")
        test_flow_steps.append({"step": "Allow audio permission", "status": "Success"})

def login_permissions_notifications(driver, obj, test_flow_steps):
    with allure.step("5. Allow notifications"):
        if not smart_click(driver, "Allow notifications", obj.allow_notifications_button_xpath, "Allow"):
            pytest.fail("Could not find or click the 'Allow notifications' button.")
        test_flow_steps.append({"step": "Allow notifications permission", "status": "Success"})

def login_enter_phone(driver, obj, test_flow_steps):
    with allure.step("6. Enter phone number"):
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, obj.phone_number_input_xpath))
        )
        phone_input.clear()
        phone_input.send_keys("7660852538")
        test_flow_steps.append({"step": "Enter valid phone number", "status": "Success", "value": "7660852538"})

def login_submit_phone(driver, obj, test_flow_steps):
    with allure.step("7. Tap next button"):
        if not smart_click(driver, "Next (login)", obj.next_button_login_xpath, "Next"):
            pytest.fail("Could not find or click the 'Next' button after entering phone number.")
        test_flow_steps.append({"step": "Click Next after entering phone number", "status": "Success"})
    
def login_verify_otp(driver, obj, test_flow_steps):
    with allure.step("8. Wait for OTP and verify"):
        time.sleep(20)
        if not smart_click(driver, "Verify (login)", obj.verify_button_login_xpath, "Verify"):
            pytest.fail("Could not find or click the 'Verify' button.")
        test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})