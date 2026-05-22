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
from utils.ui_actions import scroll_to_element, wait_for_popup, wait_for_maximize_screen

from tests.pages.regular_farmer_app.onboarding_pages import (
    load_locators_once,
    add_farm,
    draw_on_map_button,           # FIX: Section 2 was calling undefined 'Draw_on_map' — use this
    Submit_farm,
    crop_name_input,
    crop_name_item,
    intercrop_name,
    intercrop_dropdown,
    plantation_date,
    sowing_date_input,
    transplanted_date,
    ok_button,
    submit_crop,
    update_crop,
    skip_crop,
    cancel_button,
    edit_farm,
    delete_farm,
    add_crop,
    edit_crop,
    delete_crop,
    android_back,
    three_dots_menu,
    save_approve_boundary,
    hamburger_menu,
    pending_farms_tab,
    type_dropdown,
    active_dropdown,
    historical_option,
    cross_button,
    all_dropdown,
    only_farms_option,
    all_tab,
    farm_card_three_dots,
    farms_with_no_crops_option,
    farms_with_no_boundary_option,
    overview_option,
    add_boundary_from_three_dots,
    edit_boundary_from_three_dots,
    draw_boundary_on_map,
)

sys.dont_write_bytecode = True


@allure.epic("Onboarding Flow")
@allure.feature("Farm crop Boundary Validation")
class TestOnboarding:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        load_locators_once(self, request)

    # =========================================================================
    @allure.story("Farm Crop Boundary Validation")
    @allure.title("FC_001 -- Farm Crop Boundary Validation Flow")
    def test_crop_health_diary_activity_flow(self, driver):
        test_flow_steps = []

        try:
            # =================================================================
            # Section 1 — Add Farm → Add Crop → Draw Boundary
            # =================================================================
            add_farm(driver, self, test_flow_steps)
            draw_on_map_button(driver, self, test_flow_steps)
            Submit_farm(driver, self, test_flow_steps)
            crop_name_input(driver, self, test_flow_steps)
            crop_name_item(driver, self, test_flow_steps)
            plantation_date(driver, self, test_flow_steps)
            ok_button(driver, self, test_flow_steps)
            submit_crop(driver, self, test_flow_steps)
            draw_boundary_on_map(driver, self, test_flow_steps)
            save_approve_boundary(driver, self, test_flow_steps)

            # =================================================================
            # Section 2 — Add Farm → Skip Crop → Draw Boundary
            # =================================================================
            # add_farm(driver, self, test_flow_steps)
            # draw_on_map_button(driver, self, test_flow_steps)   # ← FIX
            # Submit_farm(driver, self, test_flow_steps)
            # skip_crop(driver, self, test_flow_steps)
            # draw_boundary_on_map(driver, self, test_flow_steps)
            # save_approve_boundary(driver, self, test_flow_steps)

            # =================================================================
            # Section 3 — Pending Farms Flow
            # =================================================================
            hamburger_menu(driver, self, test_flow_steps)
            pending_farms_tab(driver, self, test_flow_steps)

            # # Filter by Type → Active
            # type_dropdown(driver, self, test_flow_steps)
            # active_dropdown(driver, self, test_flow_steps)

            # Edit a farm from its card three-dots menu
            farm_card_three_dots(driver, self, test_flow_steps)
            edit_farm(driver, self, test_flow_steps)
            Submit_farm(driver, self, test_flow_steps)

            # Delete a farm from its card three-dots menu
            farm_card_three_dots(driver, self, test_flow_steps)
            delete_farm(driver, self, test_flow_steps)

            # Add crop via three-dots menu
            farm_card_three_dots(driver, self, test_flow_steps)
            add_crop(driver, self, test_flow_steps)
            crop_name_input(driver, self, test_flow_steps)
            crop_name_item(driver, self, test_flow_steps)
            plantation_date(driver, self, test_flow_steps)
            ok_button(driver, self, test_flow_steps)
            intercrop_name(driver, self, test_flow_steps)
            intercrop_dropdown(driver, self, test_flow_steps)
            submit_crop(driver, self, test_flow_steps)
            draw_boundary_on_map(driver, self, test_flow_steps)
            save_approve_boundary(driver, self, test_flow_steps)

            # Edit crop → cancel
            farm_card_three_dots(driver, self, test_flow_steps)
            edit_crop(driver, self, test_flow_steps)
            crop_name_input(driver, self, test_flow_steps)
            crop_name_item(driver, self, test_flow_steps)
            plantation_date(driver, self, test_flow_steps)
            ok_button(driver, self, test_flow_steps)
            intercrop_name(driver, self, test_flow_steps)
            intercrop_dropdown(driver, self, test_flow_steps)
            update_crop(driver, self, test_flow_steps)

            farm_card_three_dots(driver, self, test_flow_steps)
            edit_crop(driver, self, test_flow_steps)
            

            # Delete crop
            farm_card_three_dots(driver, self, test_flow_steps)
            delete_crop(driver, self, test_flow_steps)

            # Add boundary via three-dots menu
            farm_card_three_dots(driver, self, test_flow_steps)
            add_boundary_from_three_dots(driver, self, test_flow_steps)
            draw_boundary_on_map(driver, self, test_flow_steps)
            save_approve_boundary(driver, self, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/crop_health_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)