# -*- coding: utf-8 -*-
import time
import json
import os
import sys
import logging

import allure
import pytest
from utils.opencv_crop_health import (
    validate_crop_health,
    validate_leaf_moisture,
    validate_soil_moisture,
    validate_date_slider_changed,
    get_stress_level,
    calibrate_moisture_pixels,
    LEAF_MOISTURE_REFERENCE_PIXEL,
    SOIL_MOISTURE_REFERENCE_PIXEL,
    MOISTURE_SAMPLE_X,
    MOISTURE_SAMPLE_Y,
)
from utils.ocr_validation import (
    identify_moisture_screen,
    extract_card_title,
)
from utils.screenshot_utils import (
    capture_screen,
    capture_and_crop_map,
    capture_and_crop_card,
    get_title_region_pil,
)
from tests.pages.regular_farmer_app.crop_health_page import (
    load_locators_once,
    # hamburger_menu,
    # historical_farms,
    active_farms,
    navigation_button,
    farm_location,
    current_location,
    android_back,
    diary_icon,
    add_activity_button,
    activity_placeholder,
    activity_input_field,
    cost_field,
    cost_input_field,
    submit_button,
    weather_icon,
    forecast,
    hours_button,
    days_button,
    close_icon,
    share_icon,
    maximise_icon,
    notification_icon,
    expert_comments,
    crop_stress,
    close_tab,
    plus_icon,
    minus_icon,
)
from utils.wait_utils import wait_for_loader_to_disappear

sys.dont_write_bytecode = True
logger = logging.getLogger(__name__)

MAP_ROI        = (50, 250, 980, 1150)
CARD_ROI       = (0, 1450, 1080, 500)
SCREENSHOT_DIR = "screenshots/crop_health"


def step(steps: list, action: str, result):
    """Append a timestamped step record to the steps list."""
    steps.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "action":    action,
        "result":    result,
    })


def warn_if_not_calibrated(name: str, ref: dict):
    """Log a warning when a reference pixel dict has not been calibrated yet."""
    if all(v == 0 for v in ref.values()):
        logger.warning(
            "CALIBRATION NEEDED: %s reference pixel is all zeros. "
            "Run calibrate_moisture_pixels() and update cv_validator.py.", name
        )


@allure.epic("Crop Health Flow")
@allure.feature("Weather and Moisture Validation")
class TestCropHealth:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        load_locators_once(self, request)
        warn_if_not_calibrated("LEAF_MOISTURE", LEAF_MOISTURE_REFERENCE_PIXEL)
        warn_if_not_calibrated("SOIL_MOISTURE", SOIL_MOISTURE_REFERENCE_PIXEL)

    @allure.story("Crop Health Complete Flow")
    @allure.title("TC_001 -- Crop Health, Diary, Weather, Notification, leaf & soil Moisture Flow")
    def test_crop_health_diary_activity_flow(self, driver):
        steps: list[dict] = []

        try:
            # -----------------------------------------------------------------
            # FARM FLOW
            # -----------------------------------------------------------------
            # hamburger_menu(driver, self, steps)
            # historical_farms(driver, self, steps)
            active_farms(driver, self, steps)
            navigation_button(driver, self, steps)
            current_location(driver, self, steps)
            farm_location(driver, self, steps)
            android_back(driver, self, steps)

            # -----------------------------------------------------------------
            # CROP HEALTH — initial green pixel validation
            # Screen starts on the LATEST date so plus (+) is disabled.
            # Capture initial state before any slider interaction.
            # -----------------------------------------------------------------
            wait_for_loader_to_disappear(driver, timeout=5)
            time.sleep(2)

            full_init, crop_init = capture_and_crop_map(
                driver, "crop_health_initial_latest_date", SCREENSHOT_DIR, MAP_ROI
            )
            ch_result   = validate_crop_health(crop_init)
            stress_init = get_stress_level(crop_init)
            step(steps, "crop_health_pixel_check_initial", ch_result)
            step(steps, "stress_level_at_latest_date", stress_init)
            logger.info(
                "Initial crop health at latest date → valid=%s | stress=%s",
                ch_result, stress_init
            )

            # -----------------------------------------------------------------
            # DATE SLIDER — STEP 1: scroll back to crop health card, then MINUS
            # Latest date is shown by default so plus (+) is disabled.
            # Minus (−) moves back to a previous date.
            # -----------------------------------------------------------------
            before_minus_full, before_minus_crop = capture_and_crop_map(
                driver, "date_slider_before_minus", SCREENSHOT_DIR, MAP_ROI
            )
            step(steps, "date_slider_before_minus_captured", "ok")

            minus_icon(driver, self, steps)                # ← go to previous date
            wait_for_loader_to_disappear(driver, timeout=5)
            time.sleep(2)

            after_minus_full, after_minus_crop = capture_and_crop_map(
                driver, "date_slider_after_minus", SCREENSHOT_DIR, MAP_ROI
            )
            minus_diff  = validate_date_slider_changed(before_minus_crop, after_minus_crop)
            stress_prev = get_stress_level(after_minus_crop)
            step(steps, "date_slider_minus_map_changed", minus_diff)
            step(steps, "stress_level_at_previous_date", stress_prev)
            logger.info(
                "After MINUS click → map_changed=%s | stress=%s",
                minus_diff, stress_prev
            )

            # -----------------------------------------------------------------
            # DATE SLIDER — STEP 2: PLUS (return toward latest date)
            # Now that minus was clicked, plus (+) is enabled.
            # -----------------------------------------------------------------
            before_plus_full, before_plus_crop = capture_and_crop_map(
                driver, "date_slider_before_plus", SCREENSHOT_DIR, MAP_ROI
            )
            step(steps, "date_slider_before_plus_captured", "ok")

            plus_icon(driver, self, steps)                 # ← go forward to latest date
            wait_for_loader_to_disappear(driver, timeout=5)
            time.sleep(2)

            after_plus_full, after_plus_crop = capture_and_crop_map(
                driver, "date_slider_after_plus", SCREENSHOT_DIR, MAP_ROI
            )
            plus_diff    = validate_date_slider_changed(before_plus_crop, after_plus_crop)
            stress_after = get_stress_level(after_plus_crop)
            step(steps, "date_slider_plus_map_changed", plus_diff)
            step(steps, "stress_level_after_returning_to_latest", stress_after)
            logger.info(
                "After PLUS click → map_changed=%s | stress=%s",
                plus_diff, stress_after
            )

            # -----------------------------------------------------------------
            # DIARY FLOW
            # -----------------------------------------------------------------
            diary_icon(driver, self, steps)
            add_activity_button(driver, self, steps)
            activity_placeholder(driver, self, steps)
            activity_input_field(driver, self, steps)
            cost_field(driver, self, steps)
            cost_input_field(driver, self, steps)
            submit_button(driver, self, steps)
            android_back(driver, self, steps)

            # -----------------------------------------------------------------
            # WEATHER FLOW
            # -----------------------------------------------------------------
            weather_icon(driver, self, steps)
            forecast(driver, self, steps)
            hours_button(driver, self, steps)
            days_button(driver, self, steps)
            close_icon(driver, self, steps)
            share_icon(driver, self, steps)
            wait_for_loader_to_disappear(driver, timeout=5)
            android_back(driver, self, steps)
            maximise_icon(driver, self, steps)
            close_tab(driver, self, steps)
            notification_icon(driver, self, steps)
            expert_comments(driver, self, steps)
            crop_stress(driver, self, steps)
            android_back(driver, self, steps)
            android_back(driver, self, steps)

            # # -----------------------------------------------------------------
            # # SOIL MOISTURE — navigation + OCR + pixel fingerprint
            # # -----------------------------------------------------------------
            # soil_moisture_navigation(driver, self, steps)
            # wait_for_loader_to_disappear(driver, timeout=5)
            # time.sleep(1.0)

            # full_sm, card_sm = capture_and_crop_card(
            #     driver, "soil_moisture", SCREENSHOT_DIR, CARD_ROI
            # )
            # title_region = get_title_region_pil()
            # ocr_label_s  = identify_moisture_screen(full_sm, title_region)
            # ocr_title_s  = extract_card_title(full_sm, title_region)
            # step(steps, "soil_moisture_ocr",
            #      {"identified_as": ocr_label_s, "raw_title": ocr_title_s})
            # if ocr_label_s != "soil_moisture":
            #     logger.warning(
            #         "OCR identified '%s' (title=%r) -- expected soil_moisture.",
            #         ocr_label_s, ocr_title_s
            #     )
            # sm_pixel = validate_soil_moisture(card_sm, MOISTURE_SAMPLE_X, MOISTURE_SAMPLE_Y)
            # step(steps, "soil_moisture_pixel_fingerprint", sm_pixel)
            # android_back(driver, self, steps)

            # soil_moisture_share(driver, self, steps)
            # android_back(driver, self, steps)
            # soil_moisture_maximise(driver, self, steps)
            # android_back(driver, self, steps)

            # # -----------------------------------------------------------------
            # # LEAF MOISTURE — card tap + OCR + pixel fingerprint
            # # leaf_moisture_card scrolls to and opens the Leaf Moisture card.
            # # Capture + validate before navigating into the detail screen.
            # # -----------------------------------------------------------------
            # wait_for_loader_to_disappear(driver, timeout=5)
            # time.sleep(1.0)

            # full_lm_card, card_lm_card = capture_and_crop_card(
            #     driver, "leaf_moisture_card_view", SCREENSHOT_DIR, CARD_ROI
            # )
            # title_region_lm  = get_title_region_pil()
            # ocr_label_lm_card = identify_moisture_screen(full_lm_card, title_region_lm)
            # ocr_title_lm_card = extract_card_title(full_lm_card, title_region_lm)
            # step(steps, "leaf_moisture_card_ocr",
            #      {"identified_as": ocr_label_lm_card, "raw_title": ocr_title_lm_card})
            # if ocr_label_lm_card != "leaf_moisture":
            #     logger.warning(
            #         "OCR identified '%s' (title=%r) on card view -- expected leaf_moisture.",
            #         ocr_label_lm_card, ocr_title_lm_card
            #     )
            # lm_card_pixel = validate_leaf_moisture(card_lm_card, MOISTURE_SAMPLE_X, MOISTURE_SAMPLE_Y)
            # step(steps, "leaf_moisture_card_pixel_fingerprint", lm_card_pixel)

            # # Navigate into the Leaf Moisture detail screen and validate again
            # leaf_moisture_navigation(driver, self, steps)
            # wait_for_loader_to_disappear(driver, timeout=5)
            # time.sleep(1.0)

            # full_lm, card_lm = capture_and_crop_card(
            #     driver, "leaf_moisture_detail", SCREENSHOT_DIR, CARD_ROI
            # )
            # ocr_label_l = identify_moisture_screen(full_lm, title_region_lm)
            # ocr_title_l = extract_card_title(full_lm, title_region_lm)
            # step(steps, "leaf_moisture_navigation_ocr",
            #      {"identified_as": ocr_label_l, "raw_title": ocr_title_l})
            # if ocr_label_l != "leaf_moisture":
            #     logger.warning(
            #         "OCR identified '%s' (title=%r) on detail screen -- expected leaf_moisture.",
            #         ocr_label_l, ocr_title_l
            #     )
            # lm_pixel = validate_leaf_moisture(card_lm, MOISTURE_SAMPLE_X, MOISTURE_SAMPLE_Y)
            # step(steps, "leaf_moisture_detail_pixel_fingerprint", lm_pixel)
            # android_back(driver, self, steps)

            # leaf_moisture_share_icon(driver, self, steps)
            # android_back(driver, self, steps)
            # leaf_moisture_maximise(driver, self, steps)
            # android_back(driver, self, steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            out = "test-flows/crop_health_regular_farmer_flow.json"
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(steps, fh, indent=4)
            with open(out, "rb") as fh:
                allure.attach(
                    fh.read(),
                    name="test_flow_steps",
                    attachment_type=allure.attachment_type.JSON,
                )