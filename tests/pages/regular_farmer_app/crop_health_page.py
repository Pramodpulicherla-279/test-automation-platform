from socket import timeout
import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
import re
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import (
    find_and_click,
    scroll_and_click_by_text_robust,
    smart_click,
    scroll_and_tap_by_text,
    scroll_and_click_card_icon,
    scroll_to_card_and_click_icon,
   
)
from utils.ui_actions import android_back as _do_android_back
import sys
sys.dont_write_bytecode = True


def load_locators_once(self, request):
    """Loads locators once per test class and attaches them to the class."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    locators_path = os.path.join(project_root, "locators", "regular_farmer.json")
    with open(locators_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    raw = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', raw)
    xpaths = json.loads(raw)
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
    
    # # Diary screen
    # request.cls.add_activity_button_xpath = diary_xpaths.get("add_activity_button")
    # request.cls.activity_placeholder_xpath = diary_xpaths.get("activity_placeholder")
    # request.cls.activity_input_field_xpath = diary_xpaths.get("activity_input_field")
    # request.cls.cost_field_xpath = diary_xpaths.get("cost_field")
    # request.cls.cost_input_field_xpath = diary_xpaths.get("cost_input_field")
    # request.cls.submit_button_xpath = diary_xpaths.get("submit_button")
    # request.cls.back_button_xpath = diary_xpaths.get("back_button")
    # # Weather screen
    # request.cls.weather_icon_xpath = weather_xpaths.get("weather_icon")
    # request.cls.calendar_date_xpath = weather_xpaths.get("calendar_date")
    # request.cls.weather_alert_xpath = weather_xpaths.get("weather_alert")
    # request.cls.forecast_xpath = weather_xpaths.get("forecast")
    # request.cls.hours_button_xpath = weather_xpaths.get("hours_button")
    # request.cls.days_button_xpath = weather_xpaths.get("days_button")
    # request.cls.close_icon_xpath = weather_xpaths.get("close_icon")
    # request.cls.share_icon_xpath = weather_xpaths.get("share_icon")
    # request.cls.maximise_icon_xpath = weather_xpaths.get("maximise_icon")
    # request.cls.notification_icon_xpath = weather_xpaths.get("notification_icon")
    # request.cls.expert_comments_xpath = weather_xpaths.get("expert_comments")
    # request.cls.crop_stress_xpath = weather_xpaths.get("crop_stress")

    # Soil Moisture icons
    # request.cls.soil_moisture_card_xpath = soil_moisture_xpaths.get("soil_moisture_card")
    # request.cls.soil_moisture_navigation_xpath   = soil_moisture_xpaths.get("soil_moisture_navigation")
    # request.cls.soil_moisture_share_icon_xpath   = soil_moisture_xpaths.get("soil_moisture_share_icon")
    # request.cls.soil_moisture_maximise_icon_xpath = soil_moisture_xpaths.get("soil_moisture_maximise_icon")
 
    # Leaf Moisture icons
    request.cls.leaf_moisture_card_xpath = leaf_moisture_xpaths.get("leaf_moisture_card")
    request.cls.leaf_moisture_navigation_xpath   = leaf_moisture_xpaths.get("leaf_moisture_navigation")
    request.cls.leaf_moisture_share_icon_xpath   = leaf_moisture_xpaths.get("leaf_moisture_share_icon")
    request.cls.leaf_moisture_maximise_icon_xpath = leaf_moisture_xpaths.get("leaf_moisture_maximise_icon")
    
    


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

# def diary_icon(driver, obj, test_flow_steps):
#     with allure.step("4. Click diary icon"):
#         time.sleep(2)
#         if not smart_click(driver, "Click diary icon", obj.diary_icon_xpath):
#             pytest.fail("Could not find or click the 'diary icon'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click diary icon", "status": "Success"})

# def add_activity_button(driver, obj, test_flow_steps):
#     with allure.step("5. Click Add Activity button"):
#         time.sleep(2)
#         if not smart_click(driver, "Click Add Activity button", obj.add_activity_button_xpath, "Add Activity"):
#             pytest.fail("Could not find or click the 'Add Activity' button.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click Add Activity button", "status": "Success"})
        
# def activity_placeholder(driver, obj, test_flow_steps):
#     with allure.step("6. Click activity placeholder and enter activity name"):
#         time.sleep(2)
#         if not smart_click(driver, "Click activity placeholder", obj.activity_placeholder_xpath):
#             pytest.fail("Could not find or click the activity placeholder.")
#         time.sleep(1)
#         test_flow_steps.append({"step": "Click Add Activity button", "status": "Success"})

# def activity_input_field(driver, obj, test_flow_steps):
#     with allure.step("6. Click activity placeholder and enter activity name"):
#         time.sleep(2)
#         try:
#             activity_input = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((AppiumBy.XPATH, obj.activity_input_field_xpath))
#             )
#             activity_input.clear()
#             activity_input.send_keys("Ram")
#             print("[INFO] Entered activity name: 'Ram'")
#             test_flow_steps.append({
#                 "step": "Enter activity name",
#                 "status": "Success",
#                 "value": "Ram"
#             })
#         except Exception as e:
#             pytest.fail(f"Could not enter activity name: {str(e)}")
        
    
# def cost_field(driver, obj, test_flow_steps):
#     with allure.step("7. Click cost field"):
#         time.sleep(2)
#         if not smart_click(driver, "Click cost field", obj.cost_field_xpath, "Cost"):
#             pytest.fail("Could not find or click the 'cost field'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click cost field", "status": "Success"})


# def cost_input_field(driver, obj, test_flow_steps):
#     with allure.step("8. Enter cost amount"):
#         try:
#             # Wait for cost input popup field
#             cost_input = WebDriverWait(driver, 15).until(
#                 EC.element_to_be_clickable(
#                     (AppiumBy.XPATH, obj.cost_input_field_xpath)
#                 )
#             )

#             # Click on field
#             cost_input.click()
#             time.sleep(1)

#             # Clear existing value safely
#             try:
#                 cost_input.clear()
#             except Exception:
#                 pass

#             # Enter cost amount
#             cost_input.send_keys("10000")
#             print("[INFO] Entered cost amount: '10000'")

#             time.sleep(1)
#             test_flow_steps.append({
#                 "step": "Enter cost amount",
#                 "status": "Success",
#                 "value": "10000"
#             })

#         except Exception as e:
#             pytest.fail(f"Could not enter cost amount: {str(e)}")

#         time.sleep(2)

# def submit_button(driver, obj, test_flow_steps):
#     with allure.step("9. Click Submit button"):
#         submit_clicked = False
#         for attempt in range(2):
#             try:
#                 submit_btn = WebDriverWait(driver, 10).until(
#                     EC.element_to_be_clickable(
#                         (AppiumBy.XPATH, obj.submit_button_xpath)
#                     )
#                 )
#                 submit_btn.click()
#                 time.sleep(3)
#                 # Check if submit popup still exists
#                 remaining_submit_buttons = driver.find_elements(
#                     AppiumBy.XPATH,
#                     obj.submit_button_xpath
#                 )
#                 if len(remaining_submit_buttons) == 0:
#                     submit_clicked = True
#                     break
#                 else:
#                     print("[WARNING] Submit button still visible, retrying...")
#             except Exception as e:
#                 print(f"[WARNING] Submit attempt failed: {str(e)}")
#             time.sleep(2)
#         # Final validation
#         if not submit_clicked:
#             pytest.fail(
#                 "Submit popup still visible after 2 attempts."
#             )
#         time.sleep(5)
#         test_flow_steps.append({
#             "step": "Click Submit button",
#             "status": "Success"
#         })
# # ====================================================================
# # WEATHER FLOW SECTION
# # ====================================================================
    
# def weather_icon(driver, obj, test_flow_steps):
#     with allure.step("11. Click weather icon"):
#         time.sleep(2)
#         if not smart_click(driver, "Click weather icon", obj.weather_icon_xpath):
#             pytest.fail("Could not find or click the 'weather icon'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click weather icon", "status": "Success"})

# # def calendar_date(driver, obj, test_flow_steps):
# #     with allure.step("13. Click weather alert"):
# #         time.sleep(2)
# #         if not smart_click(driver, "Click calendar date", obj.calendar_date_xpath):
# #             pytest.fail("Could not find or click the 'weather alert'.")
# #         time.sleep(2)
# #         test_flow_steps.append({"step": "Click weather alert", "status": "Success"})

# def forecast(driver, obj, test_flow_steps):
#     with allure.step("14. Click Forecast"):
#         time.sleep(2)
#         if not smart_click(driver, "Click forecast", obj.forecast_xpath):
#             pytest.fail("Could not find or click the 'forecast'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click forecast", "status": "Success"})

# def hours_button(driver, obj, test_flow_steps):
#     with allure.step("15. Click hours button"):
#         time.sleep(2)
#         if not smart_click(driver, "Click hours button", obj.hours_button_xpath):
#             pytest.fail("Could not find or click the 'hours button'.")
#         time.sleep(3)
        
#         test_flow_steps.append({
#             "step": "Click hours button",
#             "status": "Success"
#         })

# # def days(driver, obj, test_flow_steps):
# #     with allure.step("16. Click days button"):
# #         time.sleep(2)
# #         if not smart_click(driver, "Click days button", obj.days_xpath):
# #             pytest.fail("Could not find or click the 'days button'.")
# #         # Android swipe instead of execute_script
# #         try:
# #             size = driver.get_window_size()
# #             start_x = size["width"] // 2
# #             start_y = int(size["height"] * 0.8)
# #             end_x = size["width"] // 2
# #             end_y = int(size["height"] * 0.3)
# #             driver.swipe(start_x, start_y, end_x, end_y, 1000)
# #             print("[INFO] Swipe completed successfully")
# #         except Exception as e:
# #             print(f"[WARNING] Swipe failed: {str(e)}")
# #         time.sleep(2)
# #         test_flow_steps.append({
# #             "step": "Click days button",
# #             "status": "Success"
# #         })
# def days_button(driver, obj, test_flow_steps):
#     with allure.step("16. Click days button"):
#         time.sleep(2)
#         if not smart_click(driver, "Click days button", obj.days_button_xpath):
#             pytest.fail("Could not find or click the 'days button'.")
#         time.sleep(2)
#         test_flow_steps.append({
#             "step": "Click days button",
#             "status": "Success"
#         })

# def close_icon(driver, obj, test_flow_steps):
#     with allure.step("17. Click close icon"):
#         time.sleep(2)
#         if not smart_click(driver, "Click close icon", obj.close_icon_xpath):
#             pytest.fail("Could not find or click the 'close icon'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click close icon", "status": "Success"})

# def share_icon(driver, obj, test_flow_steps):
#     with allure.step("18. Click share icon"):
#         time.sleep(2)
#         if not smart_click(driver, "Click share icon", obj.share_icon_xpath):
#             pytest.fail("Could not find or click the 'share icon'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click share icon", "status": "Success"})
        
#         time.sleep(2) 
# def maximise_icon(driver, obj, test_flow_steps):
#     with allure.step("20. Click maximise icon"):
#         time.sleep(2)
#         if not smart_click(driver, "Click maximise icon", obj.maximise_icon_xpath):
#             pytest.fail("Could not find or click the 'maximise icon'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click maximise icon", "status": "Success"})

# def notification_icon(driver, obj, test_flow_steps):
#     with allure.step("18. Click notification icon"):
#         time.sleep(2)
#         if not smart_click(driver, "Click notification icon", obj.notification_icon_xpath):
#             pytest.fail("Could not find or click the 'notification icon'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click notification icon", "status": "Success"})
#         time.sleep(2)

# def expert_comments(driver, obj, test_flow_steps):        
#     with allure.step("18. Click expert comments"):
#         time.sleep(2)
#         if not smart_click(driver, "Click expert comments", obj.expert_comments_xpath):
#             pytest.fail("Could not find or click the 'expert comments'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click expert comments", "status": "Success"})
#         time.sleep(2)

# def crop_stress(driver, obj, test_flow_steps):        
#     with allure.step("18. Click crop stress"):
#         time.sleep(2)
#         if not smart_click(driver, "Click crop stress", obj.crop_stress_xpath):
#             pytest.fail("Could not find or click the 'crop stress'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click crop stress", "status": "Success"})
#         time.sleep(2)
  
# # ── 2. SOIL MOISTURE FUNCTIONS (UPDATED) ─────────────────────────────────────
# def soil_moisture_card(driver, obj):
#     with allure.step("30. Click on Soil Moisture card"):
#         time.sleep(2)
#         if not scroll_and_click_card_icon(
#             driver,
#             card_text="Soil Moisture",          # ← correct
#             icon_xpath=obj.soil_moisture_card_xpath,
#         ):
#             pytest.fail("Could not find or click the 'Soil Moisture card'.")
#             time.sleep(2)
#             test_flow_steps.append({"step": "Click on Soil Moisture card", "status": "Success"})

# def soil_moisture_navigation(driver, obj, test_flow_steps):
#     """
#     Scrolls to the Soil Moisture card, then clicks its Navigation icon.
#     Uses Y-position filtering so it never hits Crop Health's Navigation icon.
#     """
#     with allure.step("31. Click navigation icon in Soil Moisture"):
#         time.sleep(2)
#         if not scroll_to_card_and_click_icon(
#             driver,
#             card_title_text="Soil Moisture",
#             icon_xpath=obj.soil_moisture_navigation_xpath,
#             name="Soil Moisture – Navigation",
#         ):
#             pytest.fail("Could not find or click the 'Soil Moisture navigation icon'.")
#         time.sleep(2)
#         test_flow_steps.append({
#             "step": "Click navigation icon in Soil Moisture",
#             "status": "Success",
#         })
 
 
# def soil_moisture_share(driver, obj, test_flow_steps):
#     """
#     Scrolls to the Soil Moisture card, then clicks its Share icon.
#     """
#     with allure.step("33. Click share icon in Soil Moisture"):
#         time.sleep(2)
#         if not scroll_to_card_and_click_icon(
#             driver,
#             card_title_text="Soil Moisture",
#             icon_xpath=obj.soil_moisture_share_icon_xpath,   # ← was using maximise_icon_xpath by mistake
#             name="Soil Moisture – Share",
#         ):
#             pytest.fail("Could not find or click the 'Soil Moisture share icon'.")
#         time.sleep(2)
#         test_flow_steps.append({
#             "step": "Click share icon in Soil Moisture",
#             "status": "Success",
#         })
 
 
# def soil_moisture_maximise(driver, obj, test_flow_steps):
#     """
#     Scrolls to the Soil Moisture card, then clicks its Maximize icon.
#     """
#     with allure.step("36. Click maximize icon in Soil Moisture"):
#         time.sleep(2)
#         if not scroll_to_card_and_click_icon(
#             driver,
#             card_title_text="Soil Moisture",
#             icon_xpath=obj.soil_moisture_maximise_icon_xpath,
#             name="Soil Moisture – Maximize",
#         ):
#             pytest.fail("Could not find or click the 'Soil Moisture maximize icon'.")
#         time.sleep(2)
#         test_flow_steps.append({
#             "step": "Click maximize icon in Soil Moisture",
#             "status": "Success",
#         })
 
 
# ── 3. LEAF MOISTURE FUNCTIONS (UPDATED) ─────────────────────────────────────
def leaf_moisture_card(driver, obj, test_flow_steps):
    with allure.step("22. Click on Leaf Moisture card"):
        time.sleep(2)
        if not scroll_and_click_card_icon(driver, card_text="Leaf Moisture", icon_xpath=obj.leaf_moisture_card_xpath):
            pytest.fail("Could not find or click the 'Leaf Moisture card'.")
            time.sleep(2)
        test_flow_steps.append({"step": "Click on Leaf Moisture card", "status": "Success"})
 
# def leaf_moisture_navigation(driver, obj, test_flow_steps):
#     """
#     Scrolls to the Leaf Moisture card, then clicks its Navigation icon.
#     """
#     with allure.step("23. Click navigation icon in Leaf Moisture"):
#         time.sleep(2)
#         if not scroll_to_card_and_click_icon(driver, card_title_text="Leaf Moisture", icon_xpath=obj.leaf_moisture_navigation_xpath, name="Leaf Moisture – Navigation" ):
#             pytest.fail("Could not find or click the 'Leaf Moisture navigation icon'.")
#         time.sleep(2)
#         test_flow_steps.append({"step": "Click navigation icon in Leaf Moisture", "status": "Success"})

def leaf_moisture_navigation(driver, obj, test_flow_steps):
    with allure.step("23. Click navigation icon in Leaf Moisture"):
        time.sleep(2)
        if not smart_click(driver, "Leaf Moisture", obj.leaf_moisture_navigation_xpath):
            print(obj.leaf_moisture_navigation_xpath)
            pytest.fail("Could not find or click the 'Leaf Moisture navigation icon'.")
        time.sleep(2)
        test_flow_steps.append({"step": "Click navigation icon in Leaf Moisture", "status": "Success"})

 
def leaf_moisture_share_icon(driver, obj, test_flow_steps):
    """
    Scrolls to the Leaf Moisture card, then clicks its Share icon.
    """
    with allure.step("25. Click share icon in Leaf Moisture"):
        time.sleep(2)
        if not scroll_to_card_and_click_icon(
            driver,
            card_title_text="Leaf Moisture",
            icon_xpath=obj.leaf_moisture_share_icon_xpath,
            name="Leaf Moisture – Share",
        ):
            pytest.fail("Could not find or click the 'Leaf Moisture share icon'.")
        time.sleep(2)
        test_flow_steps.append({
            "step": "Click share icon in Leaf Moisture",
            "status": "Success",
        })
 
 
def leaf_moisture_maximise(driver, obj, test_flow_steps):
    """
    Scrolls to the Leaf Moisture card, then clicks its Maximize icon.
    """
    with allure.step("28. Click maximize icon in Leaf Moisture"):
        time.sleep(2)
        if not scroll_to_card_and_click_icon(
            driver,
            card_title_text="Leaf Moisture",
            icon_xpath=obj.leaf_moisture_maximise_icon_xpath,
            name="Leaf Moisture – Maximize",
        ):
            pytest.fail("Could not find or click the 'Leaf Moisture maximize icon'.")
        time.sleep(2)
        test_flow_steps.append({
            "step": "Click maximize icon in Leaf Moisture",
            "status": "Success",
        })
 
 
# ── 4. CROP HEALTH DATE SLIDER FUNCTIONS (UNCHANGED LOGIC, FIXED ATTRS) ──────
#
#  These failed with AttributeError because load_locators_once never set
#  date_slider_xpath / plus_icon_xpath / minus_icon_xpath.
#  The updated load_locators_once above fixes that.
#  The function bodies below are identical to what you already have.
 
def date_slider(driver, obj, test_flow_steps):
    with allure.step("2. Click date slider"):
        time.sleep(2)
        # Scroll back to top of crop health card first so the date slider is visible
        _swipe_vertical_w3c_top(driver)
        time.sleep(1)
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
 
 
# ── NOTE: Add this helper at the top of Crophealth.py (or in wait_utils.py) ──
# It scrolls back to the top so the Crop Health date slider is visible after
# all the Soil/Leaf Moisture scrolling.
 
def _swipe_vertical_w3c_top(driver):
    """Scroll back toward top of page (upward swipe)."""
    from selenium.webdriver.common.actions.action_builder import ActionBuilder
    size = driver.get_window_size()
    start_x = size["width"] // 2
    # Swipe UP: start at 20% of screen, end at 80%
    actions = ActionBuilder(driver)
    f = actions.pointer_action
    f.move_to_location(start_x, int(size["height"] * 0.2))
    f.pointer_down()
    f.pause(0.05)
    f.move_to_location(start_x, int(size["height"] * 0.8))
    f.pointer_up()
    actions.perform()