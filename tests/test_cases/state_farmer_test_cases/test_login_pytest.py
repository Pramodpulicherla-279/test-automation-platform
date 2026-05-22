import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_find_element, smart_click
from utils.ocr_utils import extract_text_with_coordinates
import json
import os
from socket import timeout
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import find_and_click
import sys
from pages.state_farmer_app.login_page import (
    language_next,
    permissions,
    permissions_location,
    permissions_audio,
    permissions_notifications,
    enter_phone,
    next_button_login,
    verify_otp,
    load_locators_once,
)

sys.dont_write_bytecode = True

@allure.epic("Login Flow")
@allure.feature("Authentication")
class TestLogin:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        load_locators_once(self, request)

    @allure.story("Successful Login")
    @allure.title("Verify user can login with valid credentials")
    def test_login_success(self, driver):
        # This list will store the details of each step in the test flow
        test_flow_steps = []

        try:
        
            permissions(driver, self, test_flow_steps)
            permissions_location(driver, self, test_flow_steps)
            permissions_audio(driver, self, test_flow_steps)
            permissions_notifications(driver, self, test_flow_steps)
            language_next(driver, self, test_flow_steps)
            enter_phone(driver, self, test_flow_steps)
            next_button_login(driver, self, test_flow_steps)
            verify_otp(driver, self, test_flow_steps)
        finally:

            os.makedirs("test-flows", exist_ok=True)

            with open(
                "test-flows/login_flow_success.json",
                "w"
            ) as f:
                json.dump(test_flow_steps, f, indent=4)