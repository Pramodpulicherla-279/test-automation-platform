import allure
import pytest
from selenium.webdriver.support import expected_conditions as EC
import json
import os
import sys
from pages.regular_farmer_app.login_page import (
    login_success,
    login_permissions,
    login_permissions_location,
    login_permissions_audio,
    login_permissions_notifications,
    login_enter_phone,
    login_submit_phone,
    login_verify_otp,
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
        test_flow_steps = []

        try:
            login_success(driver, self, test_flow_steps)
            login_permissions(driver, self, test_flow_steps)
            login_permissions_location(driver, self, test_flow_steps)
            login_permissions_audio(driver, self, test_flow_steps)
            login_permissions_notifications(driver, self, test_flow_steps)
            login_enter_phone(driver, self, test_flow_steps)
            login_submit_phone(driver, self, test_flow_steps)
            login_verify_otp(driver, self, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/login_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)