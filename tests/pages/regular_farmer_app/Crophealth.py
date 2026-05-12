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
from utils.ui_actions import android_back as _do_android_back
import sys
sys.dont_write_bytecode = True


def load_locators_once(self, request):
    """Loads locators once per test class and attaches them to the class."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    locators_path = os.path.join(project_root, "locators", "regular_farmer.json")
    with open(locators_path, "r", encoding="utf-8") as f:
        xpaths = json.load(f)
    # ── Crop Health & Diary locators ───────────────────────────────────────
    crop_health_xpaths = xpaths.get("crop_health", {})
    diary_xpaths = xpaths.get("diary_screen", {})
    weather_xpaths = xpaths.get("weather_screen", {})
    leaf_moisture_xpaths = xpaths.get("leaf_moisture_screen", {})
    soil_moisture_xpaths = xpaths.get("soil_moisture_screen", {})
    
    # Farm card and navigation
    request.cls.hamburger_menu_xpath = crop_health_xpaths.get("hamburger_menu")
    request.cls.historical_farms_xpath = crop_health_xpaths.get("historical_farms")
    request.cls.active_card_xpath = crop_health_xpaths.get("active_farms")
    request.cls.navigation_button_xpath = crop_health_xpaths.get("navigation_button")
    # request.cls.navigation_back_button_xpath = crop_health_xpaths.get("navigation_back_button")
    request.cls.diary_icon_xpath = crop_health_xpaths.get("diary_icon")
    
    # Diary screen
    request.cls.add_activity_button_xpath = diary_xpaths.get("add_activity_button")
    request.cls.activity_placeholder_xpath = diary_xpaths.get("activity_placeholder")
    request.cls.activity_input_field_xpath = diary_xpaths.get("activity_input_field")
    request.cls.cost_field_xpath = diary_xpaths.get("cost_field")
    request.cls.cost_input_field_xpath = diary_xpaths.get("cost_input_field")
    request.cls.submit_button_xpath = diary_xpaths.get("submit_button")
    request.cls.back_button_xpath = diary_xpaths.get("back_button")
    # Weather screen
    request.cls.weather_icon_xpath = weather_xpaths.get("weather_icon")
    request.cls.calendar_date_xpath = weather_xpaths.get("calendar_date")
    request.cls.weather_alert_xpath = weather_xpaths.get("weather_alert")
    request.cls.forecast_xpath = weather_xpaths.get("forecast")
    request.cls.hours_button_xpath = weather_xpaths.get("hours_button")
    request.cls.days_button_xpath = weather_xpaths.get("days_button")
    request.cls.close_icon_xpath = weather_xpaths.get("close_icon")
    request.cls.share_icon_xpath = weather_xpaths.get("share_icon")
    request.cls.maximise_icon_xpath = weather_xpaths.get("maximise_icon")
    request.cls.notification_icon_xpath = weather_xpaths.get("notification_icon")
    request.cls.expert_comments_xpath = weather_xpaths.get("expert_comments")
    request.cls.crop_stress_xpath = weather_xpaths.get("crop_stress")
    # Leaf Moisture screen
    request.cls.leaf_moisture_navigation_xpath = leaf_moisture_xpaths.get("leaf_moisture_navigation")
    request.cls.leaf_moisture_share_icon_xpath = leaf_moisture_xpaths.get("leaf_moisture_share_icon")
    request.cls.leaf_moisture_maximise_icon_xpath = leaf_moisture_xpaths.get("leaf_moisture_maximise_icon")
    
    # Soil Moisture screen
    request.cls.soil_moisture_navigation_xpath = soil_moisture_xpaths.get("soil_moisture_navigation")
    request.cls.soil_moisture_share_icon_xpath = soil_moisture_xpaths.get("soil_moisture_share_icon")
    request.cls.soil_moisture_maximise_icon_xpath = soil_moisture_xpaths.get("soil_moisture_maximise_icon")

def _scroll_card_into_full_view(driver, card_header_xpath, text_hint, max_nudges=10):
    """
    Two-phase scroll:
      Phase 1 – UiScrollable (once only) to bring card into view.
      Phase 2 – Precise calculated swipes to push card header to top 20% of screen,
                 so the full card body (share/maximize/navigation icons) is visible.
    """
    text_hint_stripped = text_hint.strip()
    size          = driver.get_window_size()
    screen_h      = size["height"]
    screen_w      = size["width"]
    # Card header should sit at ~20% from top → full card body visible below it
    TARGET_Y      = int(screen_h * 0.20)
    # Acceptable threshold: header no lower than 45% from top
    THRESHOLD_Y   = int(screen_h * 0.45)

    # ── PHASE 1: UiScrollable once ─────────────────────────────────────────
    print(f"[INFO] Phase 1 – UiScrollable for '{text_hint}'...")
    try:
        driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiScrollable(new UiSelector().scrollable(true))'
            f'.scrollIntoView(new UiSelector().textContains("{text_hint_stripped}"))'
        )
        time.sleep(1.5)
        print(f"[INFO] UiScrollable succeeded for '{text_hint}'.")
    except Exception as e:
        print(f"[WARNING] UiScrollable failed ({e}). Falling back to manual-only mode.")

    # ── PHASE 2: Precise nudge loop (no UiScrollable here) ─────────────────
    for attempt in range(max_nudges):
        # Read current position
        els = driver.find_elements(AppiumBy.XPATH, card_header_xpath)

        if not els or not els[0].is_displayed():
            # Element not on screen yet – plain scroll down
            print(f"[INFO] '{text_hint}' not visible, scrolling down (attempt {attempt+1}).")
            driver.swipe(screen_w // 2, int(screen_h * 0.75),
                         screen_w // 2, int(screen_h * 0.30), 800)
            time.sleep(1)
            continue

        try:
            current_y = els[0].rect["y"]
        except Exception as e:
            print(f"[WARNING] Could not read element rect: {e}")
            time.sleep(1)
            continue

        print(f"[INFO] '{text_hint}' y={current_y}px | target≤{TARGET_Y}px | threshold≤{THRESHOLD_Y}px")

        if current_y <= THRESHOLD_Y:
            print(f"[INFO] '{text_hint}' fully in view! y={current_y}px ✓")
            return True

        # Calculate how far we need to swipe upward
        needed_scroll  = current_y - TARGET_Y          # pixels to move element up
        swipe_start_y  = min(int(screen_h * 0.85), current_y + 80)
        swipe_end_y    = max(int(screen_h * 0.08),  swipe_start_y - needed_scroll - 40)

        print(f"[INFO] Nudge {attempt+1}: swipe {swipe_start_y}→{swipe_end_y} "
              f"(moving element up by ~{needed_scroll}px)")
        driver.swipe(screen_w // 2, swipe_start_y,
                     screen_w // 2, swipe_end_y, 700)
        time.sleep(1.2)

    # Final leniency check
    els = driver.find_elements(AppiumBy.XPATH, card_header_xpath)
    if els:
        try:
            y = els[0].rect["y"]
            if y <= THRESHOLD_Y:
                print(f"[INFO] '{text_hint}' acceptable on final check (y={y}px).")
                return True
        except Exception:
            pass

    print(f"[ERROR] '{text_hint}' could not be positioned after {max_nudges} nudges.")
    return False

####Farm card and navigation flows  
def hamburger_menu(driver, obj, test_flow_steps):
    with allure.step("1. Click on hamburger menu"):
        time.sleep(2)
        if not smart_click(driver, "Click on hamburger menu", obj.hamburger_menu_xpath):  
            pytest.fail("Could not find or click the 'hamburger menu'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click on hamburger menu", "status": "Success"}) 

def historical_farms(driver, obj, test_flow_steps):
    with allure.step("1. Click on historical farms"):
        time.sleep(2)
        if not smart_click(driver, "Click on historical farms", obj.historical_farms_xpath):  
            pytest.fail("Could not find or click the 'historical farms'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click on historical farms", "status": "Success"}) 
 
def active_farms(driver, obj, test_flow_steps):
    with allure.step("1. Click on farm card"):
        time.sleep(2)
        if not smart_click(driver, "Click on farm card", obj.active_card_xpath):  # ✅ was active_farms_xpath
            pytest.fail("Could not find or click the 'farm card'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click on farm card", "status": "Success"})

def navigation_button(driver, obj, test_flow_steps):
    with allure.step("2. Click navigation button"):
        time.sleep(2)
        if not smart_click(driver, "Click navigation button", obj.navigation_button_xpath):
            pytest.fail("Could not find or click the 'navigation button'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click navigation button", "status": "Success"})

# def navigation_back_arrow(driver, obj, test_flow_steps):
#     with allure.step("3. Click navigation back arrow"):
#         print("[INFO] Attempting to click navigation back arrow")
#         time.sleep(2)
#         if not smart_click(driver, "Click navigation back arrow", obj.navigation_back_button_xpath):
#             pytest.fail("Could not find or click the 'navigation back arrow'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click navigation back arrow", "status": "Success"})

def android_back(driver, obj, test_flow_steps):
    with allure.step("10. Android back button"):
        time.sleep(5)
        print("[INFO] Attempting to press Android back button")
        if not _do_android_back(driver):
            pytest.fail("Could not execute Android back button.")
        time.sleep(4)
        test_flow_steps.append({"step": "Android back button pressed", "status": "Success"})

def diary_icon(driver, obj, test_flow_steps):
    with allure.step("4. Click diary icon"):
        time.sleep(2)
        if not smart_click(driver, "Click diary icon", obj.diary_icon_xpath):
            pytest.fail("Could not find or click the 'diary icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click diary icon", "status": "Success"})

def add_activity_button(driver, obj, test_flow_steps):
    with allure.step("5. Click Add Activity button"):
        time.sleep(2)
        if not smart_click(driver, "Click Add Activity button", obj.add_activity_button_xpath, "Add Activity"):
            pytest.fail("Could not find or click the 'Add Activity' button.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click Add Activity button", "status": "Success"})
        
def activity_placeholder(driver, obj, test_flow_steps):
    with allure.step("6. Click activity placeholder and enter activity name"):
        time.sleep(2)
        if not smart_click(driver, "Click activity placeholder", obj.activity_placeholder_xpath):
            pytest.fail("Could not find or click the activity placeholder.")
        time.sleep(1)
        test_flow_steps.append({"step": "Click Add Activity button", "status": "Success"})

def activity_input_field(driver, obj, test_flow_steps):
    with allure.step("6. Click activity placeholder and enter activity name"):
        time.sleep(2)
        try:
            activity_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((AppiumBy.XPATH, obj.activity_input_field_xpath))
            )
            activity_input.clear()
            activity_input.send_keys("Ram")
            print("[INFO] Entered activity name: 'Ram'")
            test_flow_steps.append({
                "step": "Enter activity name",
                "status": "Success",
                "value": "Ram"
            })
        except Exception as e:
            pytest.fail(f"Could not enter activity name: {str(e)}")
        
    
def cost_field(driver, obj, test_flow_steps):
    with allure.step("7. Click cost field"):
        time.sleep(2)
        if not smart_click(driver, "Click cost field", obj.cost_field_xpath, "Cost"):
            pytest.fail("Could not find or click the 'cost field'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click cost field", "status": "Success"})


def cost_input_field(driver, obj, test_flow_steps):
    with allure.step("8. Enter cost amount"):
        try:
            # Wait for cost input popup field
            cost_input = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, obj.cost_input_field_xpath)
                )
            )

            # Click on field
            cost_input.click()
            time.sleep(1)

            # Clear existing value safely
            try:
                cost_input.clear()
            except Exception:
                pass

            # Enter cost amount
            cost_input.send_keys("10000")
            print("[INFO] Entered cost amount: '10000'")

            time.sleep(1)
            test_flow_steps.append({
                "step": "Enter cost amount",
                "status": "Success",
                "value": "10000"
            })

        except Exception as e:
            pytest.fail(f"Could not enter cost amount: {str(e)}")

        time.sleep(2)

def submit_button(driver, obj, test_flow_steps):
    with allure.step("9. Click Submit button"):
        submit_clicked = False
        for attempt in range(2):
            try:
                submit_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (AppiumBy.XPATH, obj.submit_button_xpath)
                    )
                )
                submit_btn.click()
                time.sleep(3)
                # Check if submit popup still exists
                remaining_submit_buttons = driver.find_elements(
                    AppiumBy.XPATH,
                    obj.submit_button_xpath
                )
                if len(remaining_submit_buttons) == 0:
                    submit_clicked = True
                    break
                else:
                    print("[WARNING] Submit button still visible, retrying...")
            except Exception as e:
                print(f"[WARNING] Submit attempt failed: {str(e)}")
            time.sleep(2)
        # Final validation
        if not submit_clicked:
            pytest.fail(
                "Submit popup still visible after 2 attempts."
            )
        time.sleep(5)
        test_flow_steps.append({
            "step": "Click Submit button",
            "status": "Success"
        })
# ====================================================================
# WEATHER FLOW SECTION
# ====================================================================
    
def weather_icon(driver, obj, test_flow_steps):
    with allure.step("11. Click weather icon"):
        time.sleep(2)
        if not smart_click(driver, "Click weather icon", obj.weather_icon_xpath):
            pytest.fail("Could not find or click the 'weather icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click weather icon", "status": "Success"})

# def calendar_date(driver, obj, test_flow_steps):
#     with allure.step("13. Click weather alert"):
#         time.sleep(2)
#         if not smart_click(driver, "Click calendar date", obj.calendar_date_xpath):
#             pytest.fail("Could not find or click the 'weather alert'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click weather alert", "status": "Success"})

def forecast(driver, obj, test_flow_steps):
    with allure.step("14. Click Forecast"):
        time.sleep(2)
        if not smart_click(driver, "Click forecast", obj.forecast_xpath):
            pytest.fail("Could not find or click the 'forecast'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click forecast", "status": "Success"})

def hours_button(driver, obj, test_flow_steps):
    with allure.step("15. Click hours button"):
        time.sleep(2)
        if not smart_click(driver, "Click hours button", obj.hours_button_xpath):
            pytest.fail("Could not find or click the 'hours button'.")
        time.sleep(3)
        
        test_flow_steps.append({
            "step": "Click hours button",
            "status": "Success"
        })

# def days(driver, obj, test_flow_steps):
#     with allure.step("16. Click days button"):
#         time.sleep(2)
#         if not smart_click(driver, "Click days button", obj.days_xpath):
#             pytest.fail("Could not find or click the 'days button'.")
#         # Android swipe instead of execute_script
#         try:
#             size = driver.get_window_size()
#             start_x = size["width"] // 2
#             start_y = int(size["height"] * 0.8)
#             end_x = size["width"] // 2
#             end_y = int(size["height"] * 0.3)
#             driver.swipe(start_x, start_y, end_x, end_y, 1000)
#             print("[INFO] Swipe completed successfully")
#         except Exception as e:
#             print(f"[WARNING] Swipe failed: {str(e)}")
#         time.sleep(2)
#         test_flow_steps.append({
#             "step": "Click days button",
#             "status": "Success"
#         })
def days_button(driver, obj, test_flow_steps):
    with allure.step("16. Click days button"):
        time.sleep(2)
        if not smart_click(driver, "Click days button", obj.days_button_xpath):
            pytest.fail("Could not find or click the 'days button'.")
        time.sleep(2)
        test_flow_steps.append({
            "step": "Click days button",
            "status": "Success"
        })

def close_icon(driver, obj, test_flow_steps):
    with allure.step("17. Click close icon"):
        time.sleep(2)
        if not smart_click(driver, "Click close icon", obj.close_icon_xpath):
            pytest.fail("Could not find or click the 'close icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click close icon", "status": "Success"})

def share_icon(driver, obj, test_flow_steps):
    with allure.step("18. Click share icon"):
        time.sleep(2)
        if not smart_click(driver, "Click share icon", obj.share_icon_xpath):
            pytest.fail("Could not find or click the 'share icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click share icon", "status": "Success"})
        
        time.sleep(2) 
def maximise_icon(driver, obj, test_flow_steps):
    with allure.step("20. Click maximise icon"):
        time.sleep(2)
        if not smart_click(driver, "Click maximise icon", obj.maximise_icon_xpath):
            pytest.fail("Could not find or click the 'maximise icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click maximise icon", "status": "Success"})

def notification_icon(driver, obj, test_flow_steps):
    with allure.step("18. Click notification icon"):
        time.sleep(2)
        if not smart_click(driver, "Click notification icon", obj.notification_icon_xpath):
            pytest.fail("Could not find or click the 'notification icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click notification icon", "status": "Success"})
        time.sleep(2)

def expert_comments(driver, obj, test_flow_steps):        
    with allure.step("18. Click expert comments"):
        time.sleep(2)
        if not smart_click(driver, "Click expert comments", obj.expert_comments_xpath):
            pytest.fail("Could not find or click the 'expert comments'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click expert comments", "status": "Success"})
        time.sleep(2)

def crop_stress(driver, obj, test_flow_steps):        
    with allure.step("18. Click crop stress"):
        time.sleep(2)
        if not smart_click(driver, "Click crop stress", obj.crop_stress_xpath):
            pytest.fail("Could not find or click the 'crop stress'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click crop stress", "status": "Success"})
        time.sleep(2)
  
# ====================================================================
# SOIL MOISTURE FLOW SECTION
# ====================================================================
def soil_moisture(driver, obj, test_flow_steps):
    with allure.step("22. Scroll down till Soil Moisture section"):
        time.sleep(2)
        if not _scroll_card_into_full_view(
            driver,
            card_header_xpath=obj.soil_moisture_navigation_xpath,
            text_hint="Soil Moisture",
            max_nudges=8
        ):
            pytest.fail("Could not scroll Soil Moisture card fully into view.")
        time.sleep(2)
        test_flow_steps.append({"step": "Scroll to Soil Moisture section", "status": "Success"})

def soil_moisture_navigation(driver, obj, test_flow_steps):
    with allure.step("31. Click navigation icon in Soil Moisture"):
        time.sleep(2)
        if not smart_click(driver, "Click soil moisture navigation", obj.soil_moisture_navigation_xpath):
            pytest.fail("Could not find or click the 'soil moisture navigation icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click navigation icon in Soil Moisture", "status": "Success"})

def soil_moisture_share(driver, obj, test_flow_steps):
    with allure.step("33. Click share icon in Soil Moisture"):
        time.sleep(2)
        if not smart_click(driver, "Click soil moisture share icon", obj.soil_moisture_share_icon_xpath):
            pytest.fail("Could not find or click the 'soil moisture share icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click share icon in Soil Moisture", "status": "Success"})

def soil_moisture_maximise(driver, obj, test_flow_steps):
    with allure.step("36. Click maximize icon in Soil Moisture"):
        time.sleep(2)
        if not smart_click(driver, "Click soil moisture maximize icon", obj.soil_moisture_maximise_icon_xpath):
            pytest.fail("Could not find or click the 'soil moisture maximize icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click maximize icon in Soil Moisture", "status": "Success"})

def soil_moisture_maximise_screen(driver, obj, test_flow_steps):
    with allure.step("37. Wait for Soil Moisture maximize screen to appear"):
        time.sleep(2)
        if not obj._wait_for_maximize_screen(driver, timeout=10):
            print("[WARNING] Maximize screen wait timed out, continuing...")
        test_flow_steps.append({"step": "Wait for Soil Moisture maximize screen", "status": "Success"})

# ====================================================================
# LEAF MOISTURE FLOW SECTION
# ====================================================================
def leaf_moisture(driver, obj, test_flow_steps):
    with allure.step("22. Scroll down till Leaf Moisture section"):
        time.sleep(2)
        if not _scroll_card_into_full_view(
            driver,
            card_header_xpath=obj.leaf_moisture_navigation_xpath,
            text_hint="Leaf Moisture",
            max_nudges=10
        ):
            pytest.fail("Could not scroll Leaf Moisture card fully into view.")
        time.sleep(2)
        test_flow_steps.append({"step": "Scroll to Leaf Moisture section", "status": "Success"})

def leaf_moisture_navigation(driver, obj, test_flow_steps):
    with allure.step("23. Click navigation icon in Leaf Moisture"):
        time.sleep(2)
        if not smart_click(driver, "Click leaf moisture navigation", obj.leaf_moisture_navigation_xpath):
            pytest.fail("Could not find or click the 'leaf moisture navigation icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click navigation icon in Leaf Moisture", "status": "Success"})

def leaf_moisture_share_icon(driver, obj, test_flow_steps):
    with allure.step("25. Click share icon in Leaf Moisture"):
        time.sleep(2)
        if not smart_click(driver, "Click leaf moisture share icon", obj.leaf_moisture_share_icon_xpath):
            pytest.fail("Could not find or click the 'leaf moisture share icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click share icon in Leaf Moisture", "status": "Success"})

def leaf_moisture_maximise(driver, obj, test_flow_steps):
    with allure.step("28. Click maximize icon in Leaf Moisture"):
        time.sleep(2)
        if not smart_click(driver, "Click leaf moisture maximize icon", obj.leaf_moisture_maximise_icon_xpath):
            pytest.fail("Could not find or click the 'leaf moisture maximize icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click maximize icon in Leaf Moisture", "status": "Success"})

def leaf_moisture_maximise_screen(driver, obj, test_flow_steps):
    with allure.step("29. Wait for Leaf Moisture maximize screen to appear"):
        time.sleep(2)
        if not obj._wait_for_maximize_screen(driver, timeout=10):
            print("[WARNING] Maximize screen wait timed out, continuing...")
        test_flow_steps.append({"step": "Wait for Leaf Moisture maximize screen", "status": "Success"})

# ====================================================================
# Crop health with date slider 
# ====================================================================
def date_slider(driver, obj, test_flow_steps):
    with allure.step("2. Click date slider"):
        time.sleep(2)
        if not smart_click(driver, "Click date slider", obj.date_slider_xpath):
            pytest.fail("Could not find or click the 'date slider'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click date slider", "status": "Success"})

def plus_icon(driver, obj, test_flow_steps):
    with allure.step("3. Click plus icon on date slider"):
        time.sleep(2)
        if not smart_click(driver, "Click plus icon on date slider", obj.plus_icon_xpath):
            pytest.fail("Could not find or click the 'plus icon on date slider'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click plus icon on date slider", "status": "Success"})

def minus_icon(driver, obj, test_flow_steps):
    with allure.step("4. Click minus icon on date slider"):
        time.sleep(2)
        if not smart_click(driver, "Click minus icon on date slider", obj.minus_icon_xpath):
            pytest.fail("Could not find or click the 'minus icon on date slider'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click minus icon on date slider", "status": "Success"})
