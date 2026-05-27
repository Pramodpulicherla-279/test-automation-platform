import time
import allure
import pytest
import json
import os
import re
import sys

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from utils.wait_utils import smart_click, scroll_up_and_tap_by_text
from utils.ui_actions import android_back_func

sys.dont_write_bytecode = True


def load_locators_once(self, request):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    locators_path = os.path.join(project_root, "locators", "regular_farmer.json")
    with open(locators_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    raw = re.sub(r"\\u(?![0-9a-fA-F]{4})", r"\\\\u", raw)
    xpaths = json.loads(raw)

    # ── section lookups ──────────────────────────────────────────────────────
    dashboard_xpaths = xpaths.get("dashboard_screen", {})
    add_crop_screen_xpaths = xpaths.get("add_crop_screen", {})
    determine_boundary_modal_xpaths = xpaths.get("determine_boundary_modal", {})
    add_farm_screen_xpaths = xpaths.get("add_farm_screen", {})
    direct_sowing_xpaths = add_crop_screen_xpaths.get("direct_sowing", {})
    draw_on_map_screen_xpaths = xpaths.get("draw_on_map_screen", {})
    pending_farms_xpaths = xpaths.get("pending_farms", {})
    three_dots_xpaths = xpaths.get("farm_card_three_dots_menu", {})

    # ── dashboard ────────────────────────────────────────────────────────────
    request.cls.add_farm_button_xpath = dashboard_xpaths.get("add_farm_button")
    request.cls.hamburger_menu_xpath = dashboard_xpaths.get("hamburger_menu")
    request.cls.three_dots_xpath = three_dots_xpaths.get("farm_card_three_dots")

    # ── determine boundary modal ──────────────────────────────────────────────
    request.cls.draw_on_map_button_xpath = determine_boundary_modal_xpaths.get(
        "draw_on_map_button"
    )

    # ── add farm screen ───────────────────────────────────────────────────────
    request.cls.farm_name_xpath = add_farm_screen_xpaths.get("farm_name_input")
    request.cls.submit_button_xpath = add_farm_screen_xpaths.get("submit_button")
    request.cls.cancel_button_xpath = add_farm_screen_xpaths.get("cancel_button")

    # ── add crop screen ───────────────────────────────────────────────────────
    request.cls.crop_name_input_xpath = add_crop_screen_xpaths.get("crop_name_input")
    request.cls.crop_name_item_xpath = add_crop_screen_xpaths.get("crop_name_item")
    request.cls.plantation_date_input_xpath = add_crop_screen_xpaths.get(
        "plantation_date_input"
    )
    request.cls.transplanted_date_input_xpath = add_crop_screen_xpaths.get(
        "transplanted_date"
    )
    request.cls.update_crop_button_xpath = add_crop_screen_xpaths.get(
        "update_crop_button"
    )
    request.cls.ok_button_xpath = add_crop_screen_xpaths.get("ok_button")
    request.cls.submit_crop_button_xpath = add_crop_screen_xpaths.get(
        "submit_crop_button"
    )
    request.cls.skip_button_xpath = add_crop_screen_xpaths.get("skip_button")
    request.cls.intercrop_name_xpath = direct_sowing_xpaths.get(
        "intercrop_name"
    ) or add_crop_screen_xpaths.get("intercrop_name")
    request.cls.sowing_date_input_xpath = direct_sowing_xpaths.get(
        "sowing_date_input"
    ) or add_crop_screen_xpaths.get("sowing_date_input")
    request.cls.intercrop_sowingdate_xpath = direct_sowing_xpaths.get(
        "intercrop_sowingdate"
    ) or add_crop_screen_xpaths.get("intercrop_sowingdate")

    # ── draw on map screen ────────────────────────────────────────────────────
    request.cls.save_approve_button_xpath = draw_on_map_screen_xpaths.get(
        "save_approve_button"
    )

    # ── pending farms ─────────────────────────────────────────────────────────
    request.cls.pending_farms_tab_xpath = pending_farms_xpaths.get("pending_farms_tab")
    request.cls.active_dropdown_xpath = pending_farms_xpaths.get("active_dropdown")
    request.cls.historical_xpath = pending_farms_xpaths.get("historical")
    request.cls.cross_button_xpath = pending_farms_xpaths.get("cross_button")
    request.cls.type_dropdown_xpath = pending_farms_xpaths.get("type_dropdown")
    request.cls.all_dropdown_xpath = pending_farms_xpaths.get("all_dropdown")
    request.cls.all_tab_xpath = pending_farms_xpaths.get("All_tab")
    request.cls.only_farms_xpath = pending_farms_xpaths.get("only_farms")
    request.cls.farms_with_no_crops_xpath = pending_farms_xpaths.get(
        "farms_with_no_crops"
    )
    request.cls.farms_with_no_boundary_xpath = pending_farms_xpaths.get(
        "farms_with_no_boundary"
    )
    request.cls.three_dots_pending_farms_xpath = pending_farms_xpaths.get(
        "three_dots_menu"
    )
    # ── farm card three-dots menu ─────────────────────────────────────────────
    request.cls.farm_card_three_dots_xpath = three_dots_xpaths.get(
        "farm_card_three_dots"
    )
    request.cls.Overview_xpath = three_dots_xpaths.get("Overview")
    request.cls.edit_farm_xpath = three_dots_xpaths.get("edit_farm")
    request.cls.delete_farm_xpath = three_dots_xpaths.get("delete_farm")
    request.cls.add_crop_xpath = three_dots_xpaths.get("add_crop")
    request.cls.edit_crop_xpath = three_dots_xpaths.get("edit_crop")
    request.cls.delete_crop_xpath = three_dots_xpaths.get("delete_crop")
    request.cls.add_boundary_xpath = three_dots_xpaths.get("add_boundary")
    request.cls.edit_boundary_xpath = three_dots_xpaths.get("edit_boundary")


# ===========================================================================
# TestOnboarding class — kept for backward compatibility
# ===========================================================================
@allure.epic("Onboarding Flow")
@allure.feature("Authentication")
class TestOnboarding:
    @pytest.fixture(scope="class", autouse=True)
    def _load_locators_once(request):
        """Delegates to the shared standalone loader."""
        load_locators_once(request.cls, request)


# ===========================================================================
# Page-action helpers
# ===========================================================================


def add_farm(driver, obj, test_flow_steps):
    with allure.step("1. Click Add Farm button"):
        time.sleep(3)
        if not smart_click(
            driver, "Add Farm button", obj.add_farm_button_xpath, "Add Farm"
        ):
            pytest.fail("Could not find or click the 'Add Farm' button.")
        test_flow_steps.append({"step": "Click Add Farm button", "status": "Success"})


def draw_on_map_button(driver, obj, test_flow_steps):
    with allure.step("2. Click Draw on Map button"):
        time.sleep(3)
        if not smart_click(
            driver,
            "Draw on map (button in determine boundary)",
            obj.draw_on_map_button_xpath,
            "Draw on map",
        ):
            pytest.fail("Could not find or click the 'draw on map' button.")
        test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})


def farm_name_populated(driver, obj, test_flow_steps):
    try:
        el = driver.find_element(AppiumBy.XPATH, obj.farm_name_xpath)
        text = (el.get_attribute("text") or "").strip()
        return el if text else False
    except NoSuchElementException:
        test_flow_steps.append({"step": "Farm name auto-populated", "status": "Success"})
    

def submit_farm(driver, obj, test_flow_steps):
    with allure.step("3. Click Submit Farm button"):
        time.sleep(3)
        if not smart_click(driver, "Submit farm", obj.submit_button_xpath, "Submit"):
            pytest.fail("Could not find or click the 'Submit farm' button.")
        test_flow_steps.append({"step": "Click Submit farm", "status": "Success"})


def crop_name_input(driver, obj, test_flow_steps):
    with allure.step("4. Click Crop Name input field"):
        time.sleep(10)
        if not smart_click(
            driver, "Crop name input", obj.crop_name_input_xpath, "Select Crop Name"
        ):
            pytest.fail("Could not find or click the 'Crop name input' field.")
        test_flow_steps.append({"step": "Click crop name input", "status": "Success"})


def crop_name_item(driver, obj, test_flow_steps):
    with allure.step("5. Select crop from dropdown (OCR)"):
        time.sleep(2)
        if not smart_click(
            driver,
            "select crop from dropdown (OCR)",
            obj.crop_name_item_xpath,
            "Apples",
            screenshot_path="screenshots/crop_dropdown.png",
            force_ocr=True,
            ocr_attempts=3,
        ):
            pytest.fail("Could not select the crop name via OCR.")
        test_flow_steps.append({"step": "Click Crop Name item", "status": "Success"})


def plantation_date(driver, obj, test_flow_steps):
    with allure.step("6. Click Plantation Date input"):
        time.sleep(2)
        if not smart_click(
            driver,
            "Plantation date input",
            obj.plantation_date_input_xpath,
            "Plantation date input",
        ):
            pytest.fail("Could not find or click the 'Plantation date input' field.")
        test_flow_steps.append(
            {"step": "Click plantation date input", "status": "Success"}
        )


def transplanted_date(driver, obj, test_flow_steps):
    with allure.step("7. Click Transplanted Date input"):
        time.sleep(2)
        if not smart_click(
            driver,
            "Transplanted date input",
            obj.transplanted_date_input_xpath,
            "Transplanted date input",
        ):
            pytest.fail("Could not find or click the 'Transplanted date input' field.")
        test_flow_steps.append(
            {"step": "Click transplanted date input", "status": "Success"}
        )


def intercrop_name(driver, obj, test_flow_steps):
    with allure.step("6. Click Inter-Crop Name input field"):
        time.sleep(10)
        if not smart_click(
            driver, "Inter-Crop Name input", obj.intercrop_name_xpath, "Inter-Crop Name"
        ):
            pytest.fail("Could not find or click the 'Inter Crop Name' input field.")
        test_flow_steps.append(
            {"step": "Click Inter Crop Name input", "status": "Success"}
        )


def intercrop_dropdown(driver, obj, test_flow_steps):

    with allure.step("7. Select intercrop from dropdown"):
        time.sleep(3)
        # Scroll until crop becomes visible and tap dynamically
        if not scroll_up_and_tap_by_text(driver, text_to_find="Beetroot", max_swipes=5):
            pytest.fail("Could not find/select intercrop name after scrolling.")
            test_flow_steps.append(
                {"step": "Select Intercrop Name item", "status": "Success"}
            )


def sowing_date_input(driver, obj, test_flow_steps):
    with allure.step("8. Click Sowing Date input"):
        time.sleep(2)
        if not smart_click(
            driver,
            "Sowing date input",
            obj.sowing_date_input_xpath,
            "Sowing date input",
        ):
            pytest.fail("Could not find or click the 'Sowing date input' field.")
        test_flow_steps.append({"step": "Click sowing date input", "status": "Success"})


def ok_button(driver, obj, test_flow_steps):
    with allure.step("9. Click OK on calendar"):
        if not smart_click(driver, "OK button on calendar", obj.ok_button_xpath, "OK"):
            pytest.fail("Could not find or click the 'OK' button.")
        test_flow_steps.append(
            {"step": "Click OK button on calendar", "status": "Success"}
        )


def submit_crop(driver, obj, test_flow_steps):
    with allure.step("10. Click Submit Crop button"):
        if not smart_click(
            driver, "Submit crop", obj.submit_crop_button_xpath, "Submit"
        ):
            pytest.fail("Could not find or click the 'Submit crop' button.")
        test_flow_steps.append({"step": "Click Submit crop", "status": "Success"})


def update_crop(driver, obj, test_flow_steps):
    with allure.step("11. Click Update Crop button"):
        if not smart_click(
            driver, "Update crop", obj.update_crop_button_xpath, "Update"
        ):
            pytest.fail("Could not find or click the 'Update crop' button.")
        test_flow_steps.append({"step": "Click Update crop", "status": "Success"})


def skip_crop(driver, obj, test_flow_steps):
    with allure.step("11. Click Skip to skip crop addition"):
        time.sleep(2)
        if not smart_click(driver, "Skip crop addition", obj.skip_button_xpath, "Skip"):
            pytest.fail("Could not find or click the 'Skip' button.")
        test_flow_steps.append(
            {"step": "Click Skip button to skip crop addition", "status": "Success"}
        )


def cancel_button(driver, obj, test_flow_steps):
    with allure.step("12. Click Cancel to cancel crop addition/editing"):
        time.sleep(2)
        if not smart_click(
            driver, "Cancel crop addition/editing", obj.cancel_button_xpath, "Cancel"
        ):
            pytest.fail("Could not find or click the 'Cancel' button.")
        test_flow_steps.append(
            {
                "step": "Click Cancel button to cancel crop addition/editing",
                "status": "Success",
            }
        )


def android_back(driver, obj, test_flow_steps):
    # ── Step 10: Android back ──────────────────────────────────────────
    with allure.step("Android back"):
        time.sleep(10)
        if not android_back_func(driver):
            pytest.fail("Failed Android back")

        test_flow_steps.append({"step": "Android back", "status": "Success"})


def three_dots_menu(driver, obj, test_flow_steps):
    with allure.step("14. Click Three Dots menu on farm card"):
        time.sleep(5)
        if not smart_click(
            driver, "Three dots menu", obj.three_dots_xpath, "Three dots menu"
        ):
            pytest.fail("Could not find or click the 'Three dots' menu.")
        test_flow_steps.append({"step": "Click three dots menu", "status": "Success"})


def save_approve_boundary(driver, obj, test_flow_steps):
    with allure.step("15. Click Save boundary"):
        time.sleep(5)

        wait = WebDriverWait(driver, 20)
        try:
            wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, obj.save_approve_button_xpath)
                )
            )
        except Exception:
            pass  # Fall through to smart_click which has its own retry

        if not smart_click(
            driver,
            "Save and approve boundary",
            obj.save_approve_button_xpath,
            "Save boundary",
        ):
            pytest.fail("Could not find or click the 'Save boundary' button.")
        test_flow_steps.append(
            {"step": "Click Save and approve boundary", "status": "Success"}
        )


def hamburger_menu(driver, obj, test_flow_steps):
    with allure.step("16. Click Hamburger menu"):
        time.sleep(5)
        if not smart_click(driver, "Hamburger menu", obj.hamburger_menu_xpath):
            print("hamburger_menu_xpath =", obj.hamburger_menu_xpath)
            pytest.fail("Could not find or click the 'Hamburger' menu.")
        test_flow_steps.append({"step": "Click Hamburger menu", "status": "Success"})


def pending_farms_tab(driver, obj, test_flow_steps):
    with allure.step("17. Navigate to Pending Farms tab"):
        time.sleep(5)
        if not smart_click(
            driver, "Pending Farms tab", obj.pending_farms_tab_xpath, "Pending Farms"
        ):
            pytest.fail("Could not find or click the 'Pending Farms' tab.")
        test_flow_steps.append({"step": "Click Pending Farms tab", "status": "Success"})


def type_dropdown(driver, obj, test_flow_steps):
    with allure.step("18. Click Type dropdown in Pending Farms"):
        time.sleep(2)
        if not smart_click(
            driver, "Type dropdown", obj.type_dropdown_xpath, "Type dropdown"
        ):
            pytest.fail("Could not find or click the 'Type' dropdown in Pending Farms.")
        test_flow_steps.append(
            {"step": "Click Type dropdown in Pending Farms", "status": "Success"}
        )


def active_dropdown(driver, obj, test_flow_steps):
    with allure.step("19. Click Active dropdown in Pending Farms"):
        time.sleep(2)
        if not smart_click(
            driver, "Active dropdown", obj.active_dropdown_xpath, "Active"
        ):
            pytest.fail(
                "Could not find or click the 'Active' dropdown in Pending Farms."
            )
        test_flow_steps.append(
            {"step": "Click Active dropdown in Pending Farms", "status": "Success"}
        )


def historical_option(driver, obj, test_flow_steps):
    with allure.step("20. Select Historical option in Active dropdown"):
        time.sleep(2)
        if not smart_click(
            driver, "Historical option", obj.historical_xpath, "Historical"
        ):
            pytest.fail(
                "Could not find or click the 'Historical' option in Active dropdown."
            )
        test_flow_steps.append(
            {"step": "Click Historical option in Active dropdown", "status": "Success"}
        )


def cross_button(driver, obj, test_flow_steps):
    with allure.step("21. Click Cross button to clear filters in Pending Farms"):
        time.sleep(2)
        if not smart_click(
            driver, "Cross button to clear filters", obj.cross_button_xpath, "Cross"
        ):
            pytest.fail("Could not find or click the 'Cross' button to clear filters.")
        test_flow_steps.append(
            {
                "step": "Click Cross button to clear filters in Pending Farms",
                "status": "Success",
            }
        )


def all_dropdown(driver, obj, test_flow_steps):
    with allure.step("22. Click All dropdown in Pending Farms"):
        time.sleep(2)
        if not smart_click(driver, "All dropdown", obj.all_dropdown_xpath, "All"):
            pytest.fail("Could not find or click the 'All' dropdown in Pending Farms.")
        test_flow_steps.append(
            {"step": "Click All dropdown in Pending Farms", "status": "Success"}
        )


def only_farms_option(driver, obj, test_flow_steps):
    with allure.step("23. Select Only Farms option in All dropdown"):
        time.sleep(2)
        if not smart_click(
            driver, "Only Farms option", obj.only_farms_xpath, "Only Farms"
        ):
            pytest.fail(
                "Could not find or click the 'Only Farms' option in All dropdown."
            )
        test_flow_steps.append(
            {"step": "Click Only Farms option in All dropdown", "status": "Success"}
        )


def all_tab(driver, obj, test_flow_steps):
    with allure.step("24. Click All tab in Pending Farms"):
        time.sleep(2)
        if not smart_click(driver, "All tab", obj.all_tab_xpath, "All"):
            pytest.fail("Could not find or click the 'All' tab in Pending Farms.")
        test_flow_steps.append(
            {"step": "Click All tab in Pending Farms", "status": "Success"}
        )


def farm_card_three_dots(driver, obj, test_flow_steps):
    with allure.step("25. Click Three Dots menu on farm card in Pending Farms"):
        time.sleep(5)
        if not smart_click(
            driver,
            "Three dots menu on farm card",
            obj.farm_card_three_dots_xpath,
            "Three dots on farm card",
        ):
            pytest.fail("Could not find or click the 'Three dots' menu on a farm card.")
        test_flow_steps.append(
            {
                "step": "Click three dots menu on farm card in Pending Farms",
                "status": "Success",
            }
        )


def pending_farms_three_dots_menu(driver, obj, test_flow_steps):
    with allure.step("25. Click Three Dots menu on farm card in Pending Farms"):
        time.sleep(10)
        if not smart_click(
            driver,
            "Three dots menu on farm card",
            obj.three_dots_pending_farms_xpath,
            "Three dots on farm card",
        ):
            pytest.fail("Could not find or click the 'Three dots' menu on a farm card.")
        test_flow_steps.append(
            {
                "step": "Click three dots menu on farm card in Pending Farms",
                "status": "Success",
            }
        )


def farms_with_no_crops_option(driver, obj, test_flow_steps):
    with allure.step("26. Select Farms With No Crops option in Type dropdown"):
        time.sleep(2)
        if not smart_click(
            driver,
            "Farms with no crops option",
            obj.farms_with_no_crops_xpath,
            "Farms with no crops",
        ):
            pytest.fail("Could not find or click the 'Farms with no crops' option.")
        test_flow_steps.append(
            {
                "step": "Click Farms with no crops option in Type dropdown",
                "status": "Success",
            }
        )


def farms_with_no_boundary_option(driver, obj, test_flow_steps):
    with allure.step("27. Select Farms With No Boundary option in Type dropdown"):
        time.sleep(2)
        if not smart_click(
            driver,
            "Farms with no boundary option",
            obj.farms_with_no_boundary_xpath,
            "Farms with no boundary",
        ):
            pytest.fail("Could not find or click the 'Farms with no boundary' option.")
        test_flow_steps.append(
            {
                "step": "Click Farms with no boundary option in Type dropdown",
                "status": "Success",
            }
        )


def overview_option(driver, obj, test_flow_steps):
    with allure.step("28. Click Overview option in Three Dots menu"):
        time.sleep(5)
        if not smart_click(driver, "Overview option", obj.Overview_xpath, "Overview"):
            pytest.fail(
                "Could not find or click the 'Overview' option in the three dots menu."
            )
        test_flow_steps.append(
            {"step": "Click Overview option in three dots menu", "status": "Success"}
        )


def edit_farm(driver, obj, test_flow_steps):
    with allure.step("29. Click Edit Farm in Three Dots menu"):
        time.sleep(5)
        if not smart_click(
            driver, "Edit farm (three dots menu)", obj.edit_farm_xpath, "Edit Farm"
        ):
            pytest.fail(
                "Could not find or click the 'Edit Farm' option in the three dots menu."
            )
        test_flow_steps.append(
            {"step": "Click Edit farm in three dots menu", "status": "Success"}
        )


def delete_farm(driver, obj, test_flow_steps):
    with allure.step("30. Click Delete Farm in Three Dots menu"):
        time.sleep(5)
        if not smart_click(
            driver,
            "Delete farm (three dots menu)",
            obj.delete_farm_xpath,
            "Delete Farm",
        ):
            pytest.fail(
                "Could not find or click the 'Delete Farm' option in the three dots menu."
            )
        test_flow_steps.append(
            {"step": "Click Delete farm in three dots menu", "status": "Success"}
        )


def add_crop(driver, obj, test_flow_steps):
    with allure.step("31. Click Add Crop in Three Dots menu"):
        time.sleep(5)
        if not smart_click(
            driver, "Add crop (three dots menu)", obj.add_crop_xpath, "Add Crop"
        ):
            pytest.fail(
                "Could not find or click the 'Add Crop' option in the three dots menu."
            )
        test_flow_steps.append(
            {"step": "Click Add crop in three dots menu", "status": "Success"}
        )


def edit_crop(driver, obj, test_flow_steps):
    with allure.step("32. Click Edit Crop in Three Dots menu"):
        time.sleep(5)
        if not smart_click(
            driver, "Edit crop (three dots menu)", obj.edit_crop_xpath, "Edit Crop"
        ):
            pytest.fail(
                "Could not find or click the 'Edit Crop' option in the three dots menu."
            )
        test_flow_steps.append(
            {"step": "Click Edit crop in three dots menu", "status": "Success"}
        )


def delete_crop(driver, obj, test_flow_steps):
    with allure.step("33. Click Delete Crop in Three Dots menu"):
        time.sleep(5)
        if not smart_click(
            driver,
            "Delete crop (three dots menu)",
            obj.delete_crop_xpath,
            "Delete Crop",
        ):
            pytest.fail(
                "Could not find or click the 'Delete Crop' option in the three dots menu."
            )
        test_flow_steps.append(
            {"step": "Click Delete crop in three dots menu", "status": "Success"}
        )


def add_boundary_from_three_dots(driver, obj, test_flow_steps):
    with allure.step("34. Click Add Boundary in Three Dots menu"):
        time.sleep(5)
        if not smart_click(
            driver, "Add Boundary option", obj.add_boundary_xpath, "Add Boundary"
        ):
            pytest.fail(
                "Could not find or click the 'Add Boundary' option in the three dots menu."
            )
        test_flow_steps.append(
            {
                "step": "Click Add Boundary option in three dots menu",
                "status": "Success",
            }
        )


def edit_boundary_from_three_dots(driver, obj, test_flow_steps):
    with allure.step("35. Click Edit Boundary in Three Dots menu"):
        time.sleep(5)
        if not smart_click(
            driver, "Edit Boundary option", obj.edit_boundary_xpath, "Edit Boundary"
        ):
            pytest.fail(
                "Could not find or click the 'Edit Boundary' option in the three dots menu."
            )
        test_flow_steps.append(
            {
                "step": "Click Edit Boundary option in three dots menu",
                "status": "Success",
            }
        )


def draw_boundary_on_map(driver, obj, test_flow_steps):
    with allure.step("36. Draw boundary polygon on map"):
        time.sleep(15)  # Wait for map to fully load
        coordinates = [
            (390, 760),  # Top-left corner
            (690, 760),  # Top-right corner
            (690, 1160),  # Bottom-right corner
            (390, 1160),  # Bottom-left corner
            (390, 760),  # Close the polygon (first point)
            (390, 760),  # Confirm close
        ]
        for coord in coordinates:
            driver.tap([coord], 100)  # 100 ms per tap
        test_flow_steps.append({"step": "Draw Boundary on Map", "status": "Success"})
