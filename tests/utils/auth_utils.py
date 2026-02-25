import time
import os
import json
import pytest
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.wait_utils import smart_click
from tests.utils.ui_actions import smart_send_keys

def ensure_logged_in(driver):
    print("\n--- CHECKING LOGIN STATUS ---\n")
    test_flow_steps = []
    
    # --- STRICT HARDCODED PATH ---
    # We are removing the dynamic search to guarantee it finds the file.
    locators_path = r"C:\Users\ram\Automation\test-automation-platform\locators\regular_client.json"
    print(f"DEBUG: Enforcing locators at: {locators_path}")

    if not os.path.exists(locators_path):
        # We use pytest.fail so it STOPS the test loudly if the file is missing
        pytest.fail(f"CRITICAL: Locators JSON is completely missing at {locators_path}")

    with open(locators_path, "r", encoding="utf-8") as f:
        xpaths = json.load(f)
        
    login_x = xpaths.get("login_screen", {})
    dash_x = xpaths.get("dashboard_screen", {})
    add_btn_xpath = dash_x.get("add_button_dashboard")

    try:
        # 1. Check if already on the dashboard
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, add_btn_xpath))
            )
            print("   -> Already on Dashboard. Skipping login.")
            test_flow_steps.append({"step": "Dashboard Verification (Already Logged In)", "status": "Success"})
            return
        except:
            print("   -> Not on Dashboard. Starting Login Flow...")

        # 2. Pre-Login Permissions
        with allure.step("1. Language Selection"):
            smart_click(driver, "Language Next", login_x.get("next_button_language_login"), "Next")
            
        with allure.step("2. Allow notifications"):
            smart_click(driver, "Allow Notifications", login_x.get("allow_notifications_button"), "Allow")

        # 3. Enter Credentials
        with allure.step("3a. Select Email Tab"):
            smart_click(driver, "Email Tab", login_x.get("tab_email_login"), "Email")

        with allure.step("3b. Enter Email"):
            smart_click(driver, "Email Field Focus", login_x.get("email_input"), "Email")
            if not smart_send_keys(driver, login_x.get("email_input"), "fa1@yopmail.com", "Email Input"):
                pytest.fail("CRITICAL: Failed to enter email.")

        with allure.step("3c. Enter Password"):
            smart_click(driver, "Password Field Focus", login_x.get("password_input"), "Password")
            if not smart_send_keys(driver, login_x.get("password_input"), "Fa1@2025", "Password Input"):
                pytest.fail("CRITICAL: Failed to enter password.")

        with allure.step("4. Submit Login"):
            if not smart_click(driver, "Submit Login", login_x.get("submit_login_button"), "Login"):
                driver.execute_script("mobile: clickGesture", {"x": 540, "y": 1400})

        # 4. Post-Login Permissions
        with allure.step("5a. Handle Permissions"):
            smart_click(driver, "Allow picture", login_x.get("allow_picture_button"), "Allow")
            smart_click(driver, "Allow location", login_x.get("allow_location_button"), "Allow")
            smart_click(driver, "Allow audio", login_x.get("allow_audio_button"), "Allow")
        
        # 5. VERIFY DASHBOARD LOADED
        print("   -> Login flow finished. Waiting 10s for Dashboard...")
        time.sleep(10)
        
    finally:
        os.makedirs("test-flows", exist_ok=True)
        with open("test-flows/auth_utility_flow.json", "w") as f:
            json.dump(test_flow_steps, f, indent=4)