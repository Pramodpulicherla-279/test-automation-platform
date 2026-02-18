import os
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction

# Import your OCR utility
from utils.ocr_utils import click_element_by_ocr_text

def scroll_to_find(driver, locator, max_scrolls=5):
    """
    Scrolls vertically until the element defined by 'locator' is found.
    Uses W3C Actions for compatibility.
    
    :param driver: Appium driver instance.
    :param locator: A tuple (AppiumBy.XPATH, "...") or raw XPath string.
    :param max_scrolls: Maximum number of scrolls.
    """
    # Handle raw string XPaths
    if isinstance(locator, str):
        locator = (AppiumBy.XPATH, locator)

    for _ in range(max_scrolls):
        try:
            element = driver.find_element(*locator)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            pass
        
        # Scroll logic (Swipe Up)
        print("   -> Element not found, scrolling...")
        size = driver.get_window_size()
        start_x = size['width'] / 2
        start_y = size['height'] * 0.8
        end_y = size['height'] * 0.2
        
        actions = ActionBuilder(driver)
        finger = actions.pointer_action
        finger.move_to_location(start_x, start_y)
        finger.pointer_down()
        finger.pause(0.1)
        finger.move_to_location(start_x, end_y)
        finger.pointer_up()
        actions.perform()
        time.sleep(1) # Settle time

    # Try one last time
    return driver.find_element(*locator)

def smart_find_element(driver, name, xpath, fallback_text=None, screenshot_path="screenshots/ocr_fallback.png", force_ocr=False, ocr_attempts=1):
    """
    Find element with DOM text fallback or forced OCR.
    """
    # 0. Forced OCR Strategy
    if force_ocr:
        print(f"[{name}] Force OCR requested. Skipping XPath/DOM search.")
    else:
        # 1. Primary XPath Strategy
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath))
            )
            return element, False
        except:
            print(f"[{name}] Not found via Primary XPath.")

        # 2. Secondary Strategy: DOM Text Search
        if fallback_text:
            try:
                print(f"   -> Attempting DOM fallback for text '{fallback_text}'...")
                text_xpath = f"//*[contains(@text, '{fallback_text}') or contains(@content-desc, '{fallback_text}')]"
                
                for i in range(3): 
                    try:
                        element = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located((AppiumBy.XPATH, text_xpath))
                        )
                        print(f"   -> Found '{fallback_text}' via DOM search! Skipping OCR.")
                        return element, False
                    except:
                        if i < 2:
                            print("   -> Text not visible, scrolling down...")
                            # Inline scroll to avoid circular imports
                            size = driver.get_window_size()
                            driver.swipe(size['width']//2, int(size['height']*0.8), size['width']//2, int(size['height']*0.2), 400)
            except Exception as e:
                print(f"   -> DOM text search failed: {e}")

    # 3. OCR Strategy
    print(f"   -> Initiating OCR fallback for '{fallback_text}'...")
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
    
    for attempt in range(ocr_attempts):
        try:
            driver.save_screenshot(screenshot_path)
            if fallback_text:
                found = click_element_by_ocr_text(driver, fallback_text, screenshot_path)
                if found:
                    print(f"OCR clicked on '{fallback_text}' successfully.")
                    return None, True 
                else:
                    print(f"OCR attempt {attempt+1}/{ocr_attempts} failed to find '{fallback_text}'.")
        except Exception as e:
            print(f"OCR Error: {e}")
            
    return None, False

def smart_click(driver, name, xpath, fallback_text=None, screenshot_path="screenshots/ocr_fallback.png", force_ocr=False, ocr_attempts=1):
    """
    Wrapper around smart_find_element to perform a click.
    """
    element, used_ocr = smart_find_element(driver, name, xpath, fallback_text, screenshot_path, force_ocr, ocr_attempts)
    
    if element:
        try:
            element.click()
            return True
        except Exception as e:
            print(f"Failed to click element '{name}': {e}")
            return False
            
    return used_ocr

def smart_send_keys(driver, xpath, text, name, fallback_text=None):
    """
    Smartly finds an element and sends text to it.
    """
    print(f"[{name}] Attempting to send keys: '{text}'")
    element, used_ocr = smart_find_element(driver, name, xpath, fallback_text)
    
    if element:
        try:
            element.click()
            try: element.clear()
            except: pass
            element.send_keys(text)
            try: driver.hide_keyboard()
            except: pass
            return True
        except Exception as e:
            print(f"[{name}] Failed standard send_keys: {e}")
            return False
    elif used_ocr:
        print(f"[{name}] Element found via OCR. Blind typing '{text}'...")
        try:
            actions = ActionBuilder(driver)
            key_input = actions.key_action
            for char in text:
                key_input.send_keys(char)
                key_input.pause(0.05)
            actions.perform()
            try: driver.hide_keyboard()
            except: pass
            return True
        except Exception as e:
            print(f"[{name}] Failed blind typing: {e}")
            return False
    return False

def find_and_click(driver, by, value, fallback_text=None, timeout=20):
    try:
        print(f"Attempting to click element with locator: {by}='{value}'")
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return True
    except TimeoutException:
        if fallback_text:
            try:
                fallback_xpath = f"//*[contains(@text, '{fallback_text}')]"
                element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((AppiumBy.XPATH, fallback_xpath))
                )
                element.click()
                return True
            except:
                return False
    return False