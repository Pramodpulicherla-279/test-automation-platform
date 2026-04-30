import os
import time
import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy
from utils.ocr_utils import click_element_by_ocr_text
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
import sys
sys.dont_write_bytecode = True


def _console_log(msg: str) -> None:
    # flush=True is important when output is piped (subprocess -> backend -> UI)
    print(msg, flush=True)


def _auto_ui_shot(driver, label: str) -> None:
    """
    Optional automatic screenshot capture.
    Enable with: AUTO_UI_SHOTS=1
    Uses driver.ui_shot(label) if present (bound in conftest.py).
    """
    if os.getenv("AUTO_UI_SHOTS") != "1":
        return
    fn = getattr(driver, "ui_shot", None)
    if callable(fn):
        try:
            fn(label)
        except Exception:
            pass


def _xpath_literal(s: str) -> str:
    """Return an XPath string literal that safely handles quotes."""
    if s is None:
        return "''"
    if "'" not in s:
        return f"'{s}'"
    parts = s.split("'")
    return "concat(" + ", \"'\", ".join([f"'{p}'" for p in parts]) + ")"


def _escape_uiautomator_text(s: str) -> str:
    """Escape for embedding inside UiAutomator Java string literals."""
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


def _is_driver_alive(driver) -> bool:
    """
    FIX: Lightweight liveness probe before attempting W3C actions.
    Returns False if the driver session is dead (ANR, crash, network issue).
    Prevents InvalidElementStateException cascades from swipe on bad sessions.
    """
    if driver is None:
        return False
    try:
        _ = driver.current_activity
        return True
    except Exception as e:
        print(f"[HEALTH] Driver session unhealthy: {e}")
        return False


def _swipe_vertical_w3c(driver, start_y_ratio=0.8, end_y_ratio=0.2, x_ratio=0.5, pause_s=0.05):
    """
    Reliable vertical swipe using W3C actions (works in parallel / modern Appium).

    FIX: Added driver health check before performing swipe.
    If the session is dead (ANR/crash), swipe is skipped non-fatally so the
    caller (smart_find_element) can handle the missing element cleanly instead
    of crashing with InvalidElementStateException.
    """
    # ── Health check — skip swipe if driver session is unhealthy ──────────
    if not _is_driver_alive(driver):
        print("[SWIPE] Skipping swipe — driver session unhealthy.")
        return
    # ──────────────────────────────────────────────────────────────────────

    try:
        size = driver.get_window_size()
    except Exception as e:
        print(f"[SWIPE] Could not get window size: {e}")
        return

    start_x = int(size["width"] * x_ratio)
    start_y = int(size["height"] * start_y_ratio)
    end_y   = int(size["height"] * end_y_ratio)

    # Clamp to safe bounds — avoid coordinates outside the screen
    height = size["height"]
    start_y = max(10, min(start_y, height - 10))
    end_y   = max(10, min(end_y,   height - 10))

    try:
        touch = PointerInput(interaction.POINTER_TOUCH, "touch")
        actions = ActionBuilder(driver, mouse=touch)
        actions.pointer_action.move_to_location(start_x, start_y)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(pause_s)
        actions.pointer_action.move_to_location(start_x, end_y)
        actions.pointer_action.pause(pause_s)
        actions.pointer_action.release()
        actions.perform()
    except Exception as swipe_err:
        # FIX: Non-fatal — log and return. Do NOT re-raise.
        # Caller will handle missing element via TimeoutException.
        print(f"[SWIPE] W3C swipe failed (non-fatal): {swipe_err}")


def _android_scroll_into_view(driver, text: str):
    """
    Uses Android UiScrollable to scroll a scrollable container until an item
    with matching text/description is in view. Returns WebElement or None.
    """
    t = _escape_uiautomator_text(text)

    ua_text = (
        'new UiScrollable(new UiSelector().scrollable(true))'
        f'.scrollIntoView(new UiSelector().textContains("{t}"));'
    )
    try:
        el = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, ua_text)
        if el:
            return el
    except Exception:
        pass

    ua_desc = (
        'new UiScrollable(new UiSelector().scrollable(true))'
        f'.scrollIntoView(new UiSelector().descriptionContains("{t}"));'
    )
    try:
        el = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, ua_desc)
        if el:
            return el
    except Exception:
        pass

    return None


def _ocr_screenshot_path(driver, name: str, attempt: int) -> str:
    """
    Prefer saving OCR screenshots into the same per-test ui_screenshots folder.
    Falls back to local screenshots/ if driver.ui_shot_path is not available.
    """
    fn = getattr(driver, "ui_shot_path", None)
    if callable(fn):
        return fn(f"ocr__{name}__attempt_{attempt}")
    return "screenshots/ocr_fallback.png"


def find_and_click(driver, by, value, fallback_text=None, timeout=20):
    """
    Tries to find and click an element by its primary locator.
    If that fails and a fallback_text is provided, it tries to click by text.
    """
    try:
        print(f"Attempting to click element with locator: {by}='{value}'")
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        print("Click successful using primary locator.")
        return True
    except TimeoutException:
        print(f"Primary locator failed. Trying fallback text: '{fallback_text}'")

        if fallback_text:
            try:
                fallback_xpath = f"//*[contains(@text, '{fallback_text}')]"
                print(f"Attempting to click element with fallback locator: xpath='{fallback_xpath}'")
                element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((AppiumBy.XPATH, fallback_xpath))
                )
                element.click()
                print("Click successful using fallback text.")
                return True
            except TimeoutException:
                print(f"Fallback text '{fallback_text}' also failed.")
                return False

    return False


def smart_find_element(
    driver,
    name,
    xpath,
    fallback_text=None,
    screenshot_path="screenshots/ocr_fallback.png",
    max_swipes=6,
    per_try_wait_s=1.5,
    stop_if_no_change=True,
    *,
    force_ocr: bool = False,
    enable_scroll: bool = True,
    enable_dom_fallback: bool = True,
    ocr_attempts: int = 2,
    ocr_wait_s: float = 0.7,
):
    """
    Find element with optional OCR-first mode.

    If force_ocr=True:
      - try primary xpath once
      - then do OCR click attempts (no UiScrollable, no DOM/scroll loop)
    """
    # 1) Primary XPath Strategy (always try)
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, xpath))
        )
        _console_log(f"[FOUND] name='{name}' via XPATH")
        return element, False
    except TimeoutException:
        print(f"[{name}] Not found via Primary XPath.")

    # If user explicitly wants OCR, skip scroll/DOM strategies.
    if force_ocr:
        enable_scroll = False
        enable_dom_fallback = False

    # 2) Secondary Strategy (Android): UiScrollable (only if enabled)
    if fallback_text and enable_scroll:
        print(f"   -> Attempting Android UiScrollable scrollIntoView for {fallback_text!r}...")
        el = _android_scroll_into_view(driver, fallback_text)
        if el:
            print(f"   -> Found {fallback_text!r} via UiScrollable! Skipping OCR.")
            return el, False

    # 3) Secondary Strategy: DOM Text Search (only if enabled)
    if fallback_text and enable_dom_fallback:
        literal = _xpath_literal(fallback_text)
        text_xpath = f"//*[contains(@text, {literal}) or contains(@content-desc, {literal})]"
        print(f"   -> Attempting DOM fallback for text {fallback_text!r}...")

        last_source = None
        for i in range(max_swipes + 1):
            try:
                element = WebDriverWait(driver, per_try_wait_s).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, text_xpath))
                )
                print(f"   -> Found {fallback_text!r} via DOM search! Skipping OCR.")
                return element, False
            except TimeoutException:
                if not enable_scroll or i >= max_swipes:
                    break

                if stop_if_no_change:
                    try:
                        source = driver.page_source
                        if last_source is not None and source == last_source:
                            print("   -> Page source did not change after swipe; stopping DOM scroll search.")
                            break
                        last_source = source
                    except Exception:
                        pass

                print(f"   -> Not visible yet (attempt {i+1}/{max_swipes}). Scrolling down...")
                # FIX: Wrapped in try/except — swipe failure is non-fatal
                try:
                    _swipe_vertical_w3c(driver)
                except Exception as swipe_err:
                    print(f"[smart_find] Swipe skipped due to error: {swipe_err}")

    # 4) OCR Strategy (Last Resort or Forced)
    if fallback_text:
        print("   -> Initiating OCR fallback (this may take time)...")

        for attempt in range(1, max(1, int(ocr_attempts)) + 1):
            shot_path = _ocr_screenshot_path(driver, name, attempt)

            try:
                os.makedirs(os.path.dirname(shot_path) or ".", exist_ok=True)
            except Exception:
                pass

            try:
                driver.get_screenshot_as_file(shot_path)
            except Exception:
                try:
                    driver.save_screenshot(shot_path)
                except Exception:
                    pass

            found = click_element_by_ocr_text(driver, fallback_text, shot_path)
            if found:
                print(f"OCR clicked on '{fallback_text}' successfully.")
                return None, True

            print(f"OCR did not find '{fallback_text}' (attempt {attempt}/{ocr_attempts}).")
            time.sleep(ocr_wait_s)

    return None, False


def smart_click(
    driver,
    name,
    xpath,
    fallback_text=None,
    screenshot_path="screenshots/ocr_fallback.png",
    *,
    force_ocr: bool = False,
    enable_scroll: bool = True,
    enable_dom_fallback: bool = True,
    ocr_attempts: int = 2,
):
    """
    Wrapper around smart_find_element to perform a click.
    AUTO screenshots:
      - before click attempt
      - after success
      - after failure
    """
    _auto_ui_shot(driver, f"before__click__{name}")

    element, used_ocr = smart_find_element(
        driver,
        name,
        xpath,
        fallback_text=fallback_text,
        screenshot_path=screenshot_path,
        force_ocr=force_ocr,
        enable_scroll=enable_scroll,
        enable_dom_fallback=enable_dom_fallback,
        ocr_attempts=ocr_attempts,
    )

    if element:
        try:
            element.click()
            _auto_ui_shot(driver, f"after__click__{name}__ok")
            return True
        except Exception as e:
            print(f"Failed to click element '{name}': {e}")
            _auto_ui_shot(driver, f"after__click__{name}__exc")
            return False

    if used_ocr:
        _auto_ui_shot(driver, f"after__click__{name}__ocr_ok")
        return True

    _auto_ui_shot(driver, f"after__click__{name}__not_found")
    return False


def scroll_and_click_by_text_robust(driver, text_to_find, max_swipes=5):
    """
    Scrolls down to find an element with specific text, then attempts to click it.
    If the element itself isn't clickable, it tries to click its clickable parent.
    """
    for _ in range(max_swipes):
        try:
            element_xpath = f"//*[contains(@text, '{text_to_find}')]"
            text_element = driver.find_element(AppiumBy.XPATH, element_xpath)

            if text_element.get_attribute('clickable') == 'true':
                print(f"Text element '{text_to_find}' is directly clickable. Clicking it.")
                text_element.click()
                return True
            else:
                print(f"Element with text '{text_to_find}' is not clickable. Searching for a clickable parent...")
                parent_xpath = f"({element_xpath})/ancestor::*[@clickable='true']"
                clickable_parent = driver.find_element(AppiumBy.XPATH, parent_xpath)
                print("Found a clickable parent. Clicking it.")
                clickable_parent.click()
                return True

        except NoSuchElementException:
            print(f"'{text_to_find}' not found, scrolling...")
            # FIX: Use _swipe_vertical_w3c (health-checked) instead of driver.swipe()
            try:
                _swipe_vertical_w3c(driver)
            except Exception as e:
                print(f"[scroll_and_click_robust] Swipe failed (non-fatal): {e}")

    print(f"Failed to find or click '{text_to_find}' after {max_swipes} swipes.")
    return False


def scroll_and_tap_by_text(driver, text_to_find, max_swipes=5):
    """
    Scrolls down to find an element by its text and performs a coordinate-based tap
    on its center using W3C Actions API (compatible with latest Appium Python Client
    and robust for parallel testing).
    """
    for i in range(max_swipes):
        try:
            universal_xpath = f"//*[contains(@text, '{text_to_find}') or contains(@content-desc, '{text_to_find}')]"
            element = driver.find_element(AppiumBy.XPATH, universal_xpath)

            location = element.location
            size = element.size
            center_x = location['x'] + size['width'] / 2
            center_y = location['y'] + size['height'] / 2

            print(f"Found '{text_to_find}'. Tapping at dynamic coordinates: ({center_x}, {center_y})")
            allure.attach(
                f"Tapping '{text_to_find}' on {driver.capabilities.get('deviceName')} at ({center_x}, {center_y})",
                name="Dynamic Coordinate Tap",
                attachment_type=allure.attachment_type.TEXT
            )

            touch = PointerInput(interaction.POINTER_TOUCH, "touch")
            actions = ActionBuilder(driver, mouse=touch)
            actions.pointer_action.move_to_location(center_x, center_y)
            actions.pointer_action.pointer_down()
            actions.pointer_action.pause(0.1)
            actions.pointer_action.release()
            actions.perform()

            return True

        except NoSuchElementException:
            if i < max_swipes - 1:
                print(f"'{text_to_find}' not found, scrolling down...")
                # FIX: Use health-checked _swipe_vertical_w3c
                try:
                    _swipe_vertical_w3c(driver)
                except Exception as e:
                    print(f"[scroll_and_tap] Swipe failed (non-fatal): {e}")
            else:
                print(f"Could not find element '{text_to_find}' after {max_swipes} swipes.")
                return False

    return False