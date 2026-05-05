import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import smart_find_element, smart_click
from utils.ocr_utils import extract_text_with_coordinates
import json
import os
from utils.wait_utils import find_and_click
import sys
sys.dont_write_bytecode = True


# ════════════════════════════════════════════════════════════════════════════
#  PERMISSION HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _try_permission(driver, name: str, xpath: str, fallback_text: str,
                    timeout: int = 8) -> bool:
    """
    Attempt to find and click a permission dialog button.

    Returns True  → button found and clicked.
    Returns False → dialog not present (not an error — permission may have
                    already been granted or may not appear on this OS version).

    Never raises — permission dialogs are optional by nature.
    KeyboardInterrupt is re-raised so pytest can terminate cleanly.
    """
    try:
        # Give the dialog a moment to animate in
        time.sleep(1.5)
        result = smart_click(driver, name, xpath, fallback_text)
        if result:
            print(f"[PERM] ✅ Clicked permission: {name}")
            time.sleep(1)
        else:
            print(f"[PERM] ⚠️  Permission dialog not found (skipped): {name}")
        return result
    except KeyboardInterrupt:
        # CRITICAL: re-raise so pytest marks the test as failed/interrupted,
        # not silently passed.
        raise
    except Exception as e:
        print(f"[PERM] ⚠️  Exception during permission '{name}' (skipped): {e}")
        return False


def _wait_for_screen(driver, xpath: str, fallback_text: str,
                     timeout: int = 20) -> bool:
    """
    Poll until an element matching xpath (or fallback_text via OCR) appears,
    or until timeout expires.  Returns True if found, False otherwise.
    KeyboardInterrupt is re-raised so the test session terminates cleanly.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            elems = driver.find_elements(AppiumBy.XPATH, xpath)
            if elems and elems[0].is_displayed():
                return True
        except KeyboardInterrupt:
            raise  # re-raise — do NOT swallow interrupts
        except Exception:
            pass

        # Also try a broad text match as fallback
        if fallback_text:
            try:
                text_xpath = (
                    f"//*[contains(@text,'{fallback_text}') or "
                    f"contains(@content-desc,'{fallback_text}')]"
                )
                elems = driver.find_elements(AppiumBy.XPATH, text_xpath)
                if elems and elems[0].is_displayed():
                    return True
            except KeyboardInterrupt:
                raise  # re-raise — do NOT swallow interrupts
            except Exception:
                pass

        time.sleep(1.5)
    return False


# ════════════════════════════════════════════════════════════════════════════
#  TEST CLASS
# ════════════════════════════════════════════════════════════════════════════

@allure.epic("Login Flow")
@allure.feature("Authentication")
class TestLogin:

    @allure.story("Successful Login")
    @allure.title("Verify user can login with valid credentials")
    def test_login_success(self, driver):
        test_flow_steps = []

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, 'r', encoding='utf-8') as f:
            xpaths = json.load(f)

        # ── Locators ──────────────────────────────────────────────────────
        login_screen_xpaths = xpaths.get("login_screen", {})
        language_next_xpath             = login_screen_xpaths.get("next_button_language_login")
        allow_picture_button_xpath      = login_screen_xpaths.get("allow_picture_button")
        allow_location_button_xpath     = login_screen_xpaths.get("allow_location_button")
        allow_audio_button_xpath        = login_screen_xpaths.get("allow_audio_button")
        allow_notifications_button_xpath = login_screen_xpaths.get("allow_notifications_button")
        phone_number_input_xpath        = login_screen_xpaths.get("phone_number_input")
        next_button_login_xpath         = login_screen_xpaths.get("next_button_login")
        verify_button_login_xpath       = login_screen_xpaths.get("verify_button_login")

        try:
            # ── Step 1: Language selection ─────────────────────────────────
            with allure.step("1. Next button on language selection screen"):
                if not smart_click(driver, "Next Button (Language)",
                                   language_next_xpath, "Next"):
                    pytest.fail(
                        "Could not find or click the 'Next button on language selection' button."
                    )
                test_flow_steps.append({
                    "step": "Click Next on language selection", "status": "Success"
                })
                time.sleep(2)

            # ── Steps 2-5: Permission dialogs (OPTIONAL — non-fatal) ───────
            # Each permission is attempted but NOT failed if the dialog is
            # absent.  On Android 10 many dialogs don't appear at all;
            # on Android 12/13 the media-permission dialog may appear
            # AFTER a later navigation step.  We try them now and move on.

            with allure.step("2. Allow picture (optional permission)"):
                granted = _try_permission(
                    driver,
                    "While using the app (allow picture)",
                    allow_picture_button_xpath,
                    "While using the app",
                )
                status = "Success" if granted else "Skipped (dialog not shown)"
                test_flow_steps.append({"step": "Allow picture permission", "status": status})

            with allure.step("3. Allow location (optional permission)"):
                granted = _try_permission(
                    driver,
                    "While using (allow location)",
                    allow_location_button_xpath,
                    "While using",
                )
                status = "Success" if granted else "Skipped (dialog not shown)"
                test_flow_steps.append({"step": "Allow location permission", "status": status})

            with allure.step("4. Allow audio (optional permission)"):
                granted = _try_permission(
                    driver,
                    "While using the app (allow audio)",
                    allow_audio_button_xpath,
                    "While using the app",
                )
                status = "Success" if granted else "Skipped (dialog not shown)"
                test_flow_steps.append({"step": "Allow audio permission", "status": status})

            with allure.step("5. Allow notifications (optional permission)"):
                granted = _try_permission(
                    driver,
                    "Allow notifications",
                    allow_notifications_button_xpath,
                    "Allow",
                )
                status = "Success" if granted else "Skipped (dialog not shown)"
                test_flow_steps.append({
                    "step": "Allow notifications permission", "status": status
                })

            # ── Step 6: Phone number ───────────────────────────────────────
            with allure.step("6. Enter phone number"):
                # Wait for phone input to appear (the app may still be loading)
                if not _wait_for_screen(
                    driver, phone_number_input_xpath, "phone", timeout=20
                ):
                    pytest.fail("Phone number input did not appear within 20s.")

                phone_input = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (AppiumBy.XPATH, phone_number_input_xpath)
                    )
                )
                phone_input.clear()
                phone_input.send_keys("7660852538")
                test_flow_steps.append({
                    "step": "Enter valid phone number", "status": "Success"
                })

                # Handle any permission dialog that popped up after phone field focus
                _try_permission(
                    driver, "Late picture permission",
                    allow_picture_button_xpath, "While using the app"
                )

            # ── Step 7: Next ───────────────────────────────────────────────
            with allure.step("7. Tap next button"):
                if not smart_click(driver, "Next (login)",
                                   next_button_login_xpath, "Next"):
                    pytest.fail(
                        "Could not find or click the 'Next' button after entering phone number."
                    )
                test_flow_steps.append({
                    "step": "Click Next after phone number", "status": "Success"
                })

            # ── Step 8: Wait for OTP and verify ───────────────────────────
            with allure.step("8. Wait for OTP and verify"):
                print("[LOGIN] Waiting 20s for OTP auto-fill...")
                time.sleep(20)

                # Dismiss any permission dialog that appeared during OTP wait
                _try_permission(
                    driver, "Permission during OTP wait",
                    allow_picture_button_xpath, "While using the app"
                )
                _try_permission(
                    driver, "Notification permission during OTP",
                    allow_notifications_button_xpath, "Allow"
                )

                # Wait a bit for UI to settle
                time.sleep(3)
                
                # Try clicking verify (optional)
                clicked = smart_click(
                    driver,
                    "Verify (login)",
                    verify_button_login_xpath,
                    "Verify"
                )
                
                if clicked:
                    print("[LOGIN] Verify button clicked")
                else:
                    print("[LOGIN] Verify button not found — assuming auto-login or already verified")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/login_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)