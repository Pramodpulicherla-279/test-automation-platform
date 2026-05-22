from socket import timeout
import time
import allure
import pytest
import json
import os
import sys

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from utils.ui_actions import (scroll_to_element, wait_for_popup, wait_for_maximize_screen)
from tests.pages.regular_farmer_app.crop_health_page import (
    hamburger_menu,
    historical_farms,
    active_farms,
    load_locators_once,
    navigation_button,
    # navigation_back_arrow,
    android_back,
    # diary_icon,
    # add_activity_button,
    # activity_placeholder,
    # activity_input_field,
    # cost_field,
    # cost_input_field,
    # submit_button,
    # weather_icon,
    # # calendar_date,
    # forecast,
    # hours_button,
    # days_button,
    # close_icon,
    # share_icon,
    # maximise_icon,
    # notification_icon,
    # expert_comments,
    # crop_stress,
    # soil_mositure_card,
    # soil_moisture_navigation,
    # soil_moisture_share,
    # soil_moisture_maximise,
    leaf_moisture_card,
    leaf_moisture_navigation,
    leaf_moisture_share_icon,
    leaf_moisture_maximise,
    date_slider,
    plus_icon,
    minus_icon,
)

sys.dont_write_bytecode = True


@allure.epic("Crop Health Flow")
@allure.feature("Weather and Moisture Validation")
class TestCropHealth:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        load_locators_once(self, request)

    @allure.story("Crop Health Complete Flow")
    @allure.title("FC_001 -- Crop Health Diary, Weather & Moisture Flow")
    def test_crop_health_diary_activity_flow(self, driver):
        test_flow_steps = []

        try:

            # ============================================================
            # FARM FLOW
            # ============================================================

            hamburger_menu(driver, self, test_flow_steps)
            historical_farms(driver, self, test_flow_steps)
            active_farms(driver, self, test_flow_steps)
            navigation_button(driver, self, test_flow_steps)
            # navigation_back_arrow(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)

            # # ============================================================
            # # DIARY FLOW
            # # ============================================================

            # diary_icon(driver, self, test_flow_steps)
            # add_activity_button(driver, self, test_flow_steps)
            # activity_placeholder(driver, self, test_flow_steps)
            # activity_input_field(driver, self, test_flow_steps)
            # cost_field(driver, self, test_flow_steps)
            # cost_input_field(driver, self, test_flow_steps)
            # submit_button(driver, self, test_flow_steps)
            # android_back(driver, self, test_flow_steps)

            # # ============================================================
            # # WEATHER FLOW
            # # ============================================================

            # weather_icon(driver, self, test_flow_steps)
            # # calendar_date(driver, self, test_flow_steps)
            # forecast(driver, self, test_flow_steps)
            # hours_button(driver, self, test_flow_steps)
            # days_button(driver, self, test_flow_steps)
            # close_icon(driver, self, test_flow_steps)
            # share_icon(driver, self, test_flow_steps)
            # android_back(driver, self, test_flow_steps)
            # maximise_icon(driver, self, test_flow_steps)
            # android_back(driver, self, test_flow_steps)
            # notification_icon(driver, self, test_flow_steps)
            # expert_comments(driver, self, test_flow_steps)
            # crop_stress(driver, self, test_flow_steps)
            # android_back(driver, self, test_flow_steps)

            # ============================================================
            # SOIL MOISTURE FLOW
            # ============================================================
            # soil_moisture_navigation(driver, self, test_flow_steps)
            # android_back(driver, self, test_flow_steps)
            # soil_moisture_share(driver, self, test_flow_steps)
            # android_back(driver, self, test_flow_steps)
            # soil_moisture_maximise(driver, self, test_flow_steps)
            # android_back(driver, self, test_flow_steps)

            # ============================================================
            # LEAF MOISTURE FLOW
            # ============================================================
            # leaf_moisture_card(driver, self, test_flow_steps)
            leaf_moisture_navigation(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            leaf_moisture_share_icon(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)
            leaf_moisture_maximise(driver, self, test_flow_steps)
            android_back(driver, self, test_flow_steps)

            # ============================================================
            # Crop Health with date slider
            # ============================================================
            date_slider(driver, self, test_flow_steps)
            plus_icon(driver, self, test_flow_steps)
            minus_icon(driver, self, test_flow_steps)
         

        finally:

            os.makedirs("test-flows", exist_ok=True)

            with open(
                "test-flows/crop_health_flow_success.json",
                "w"
            ) as f:
                json.dump(test_flow_steps, f, indent=4)