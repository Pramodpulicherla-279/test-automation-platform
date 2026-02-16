import time
import allure
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy

# W3C Actions Imports
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction

# Local Utility Imports
from tests.utils.touch_utils import perform_scroll
from utils.ocr_utils import click_element_by_ocr_text

def scroll_to_find(driver, locator, max_scrolls=5):
    """
    Scrolls down vertically until the element defined by 'locator' is found.
    Handles both Tuple locators and raw XPath strings.
    
    :param driver: The Appium/Selenium driver instance.
    :param locator: A tuple (By.ID, "some_id") OR a raw XPath string.
    :param max_scrolls: Maximum number of times to scroll before giving up.
    :return: The web element if found, otherwise raises NoSuchElementException.
    """
    
    # --- FIX: Handle raw string XPaths ---
    if isinstance(locator, str):
        locator = (AppiumBy.XPATH, locator)
    # -------------------------------------

    for _ in range(max_scrolls):
        try:
            # Try to find the element
            element = driver.find_element(*locator)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            # If not found, ignore error and try scrolling
            pass
            
        # Perform a scroll using the utility
        perform_scroll(driver)
        time.sleep(1)  # Brief wait for scroll animation to settle

    # Try one last time after the final scroll
    return driver.find_element(*locator)


def find_and_click(driver, by, value, fallback_text=None, timeout=20):
    """
    Tries to find and click an element by its primary locator.
    If that fails and a fallback_text is provided, it tries to click by text.
    """
    try:
        # 1. Try to click using the primary locator
        print(f"Attempting to click element with locator: {by}='{value}'")
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        print("Click successful using primary locator.")
        return True
    except TimeoutException:
        print(f"Primary locator failed. Trying fallback text: '{fallback_text}'")
        
        # 2. If primary locator fails, try the fallback text
        if fallback_text:
            try:
                # Construct a generic XPath to find any element containing the text
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


def smart_find_element(driver, name, xpath, fallback_text=None, screenshot_path="screenshots/ocr_fallback.png"):
    """
    Find element with DOM text fallback before expensive OCR.
    Strategy:
    1. Precise XPath
    2. DOM Text Search (Fast)
    3. OCR (Slow Visual Fallback)
    """
    # 1. Primary XPath Strategy
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, xpath))
        )
        return element, False
    except:
        print(f"[{name}] Not found via Primary XPath.")

    # 2. Secondary Strategy: DOM Text Search (Much faster than OCR)
    if fallback_text:
        try:
            print(f"   -> Attempting DOM fallback for text '{fallback_text}'...")
            # Search for any element containing the text or content-desc
            text_xpath = f"//*[contains(@text, '{fallback_text}') or contains(@content-desc, '{fallback_text}')]"
            
            # Simple scroll attempts to find the text in DOM
            for i in range(3): 
                try:
                    element = WebDriverWait(driver, 1).until(
                        EC.presence_of_element_located((AppiumBy.XPATH, text_xpath))
                    )
                    print(f"   -> Found '{fallback_text}' via DOM search! Skipping OCR.")
                    return element, False
                except:
                    # Scroll down a bit and retry
                    if i < 2:
                        print("   -> Text not visible, scrolling down...")
                        perform_scroll(driver) # Use robust scroll utility
        except Exception as e:
            print(f"   -> DOM text search failed: {e}")

    # 3. OCR Strategy (Last Resort - Slow)
    print("   -> Initiating OCR fallback (this may take time)...")
    try:
        driver.save_screenshot(screenshot_path)
    except:
        pass # Handle case where screenshot folder doesn't exist

    if fallback_text:
        try:
            found = click_element_by_ocr_text(driver, fallback_text, screenshot_path)
            if found:
                print(f"OCR clicked on '{fallback_text}' successfully.")
                return None, True 
            else:
                print(f"OCR failed to find '{fallback_text}' on screen.")
        except Exception as e:
            print(f"OCR Utility failed: {e}")

    return None, False

def smart_click(driver, name, xpath, fallback_text=None, screenshot_path="screenshots/ocr_fallback.png"):
    """
    Wrapper around smart_find_element to perform a click.
    """
    element, used_ocr = smart_find_element(driver, name, xpath, fallback_text, screenshot_path)
    if element:
        try:
            element.click()
            return True
        except Exception as e:
            print(f"Failed to click element '{name}': {e}")
            return False
    return used_ocr

def scroll_and_click_by_text_robust(driver, text_to_find, max_swipes=5):
    """
    Scrolls down to find an element with specific text, then attempts to click it.
    If the element itself isn't clickable, it tries to click its clickable parent.
    """
    for _ in range(max_swipes):
        try:
            # First, find the element by its text
            element_xpath = f"//*[contains(@text, '{text_to_find}')]"
            text_element = driver.find_element(AppiumBy.XPATH, element_xpath)
            
            # --- THE CRITICAL LOGIC ---
            # Check if the element itself is clickable. If not, find its ancestor.
            if text_element.get_attribute('clickable') == 'true':
                print(f"Text element '{text_to_find}' is directly clickable. Clicking it.")
                text_element.click()
                return True
            else:
                print(f"Element with text '{text_to_find}' is not clickable. Searching for a clickable parent...")
                # This XPath finds the first ancestor of the text element that IS clickable.
                parent_xpath = f"({element_xpath})/ancestor::*[@clickable='true']"
                clickable_parent = driver.find_element(AppiumBy.XPATH, parent_xpath)
                
                print("Found a clickable parent. Clicking it.")
                clickable_parent.click()
                return True

        except NoSuchElementException:
            # If the element isn't on screen, scroll down
            print(f"'{text_to_find}' not found, scrolling...")
            perform_scroll(driver) # Use robust scroll utility

    print(f"Failed to find or click '{text_to_find}' after {max_swipes} swipes.")
    return False

def scroll_and_tap_by_text(driver, text_to_find, max_swipes=5):
    """
    Scrolls down to find an element by its text and performs a coordinate-based tap
    on its center. Uses W3C Pointer Actions to ensure compatibility.
    """
    for i in range(max_swipes):
        try:
            # 1. Use the universal XPath to find the element
            universal_xpath = f"//*[contains(@text, '{text_to_find}') or contains(@content-desc, '{text_to_find}')]"
            element = driver.find_element(AppiumBy.XPATH, universal_xpath)
            
            # 2. Dynamically get the element's location
            location = element.location
            size = element.size
            center_x = location['x'] + size['width'] / 2
            center_y = location['y'] + size['height'] / 2
            
            print(f"Found '{text_to_find}'. Tapping at dynamic coordinates: ({center_x}, {center_y})")
            allure.attach(f"Tapping '{text_to_find}' at ({center_x}, {center_y})", 
                          name="Dynamic Coordinate Tap", attachment_type=allure.attachment_type.TEXT)
            
            # 3. Perform the raw tap action using W3C Actions (FIXED for 'mouse_button' error)
            # Create a touch input
            touch_input = PointerInput(interaction.POINTER_TOUCH, "touch")
            
            actions = ActionBuilder(driver, mouse_button=None)
            actions.devices = [touch_input] # Force use of touch input
            
            pointer = actions.pointer_action
            pointer.move_to_location(center_x, center_y)
            pointer.pointer_down()
            pointer.pause(0.1)
            pointer.pointer_up()
            
            actions.perform()
            return True
            
        except NoSuchElementException:
            # 4. If not found, scroll down and try again
            if i < max_swipes - 1:
                print(f"'{text_to_find}' not found, scrolling down...")
                perform_scroll(driver)
            else:
                print(f"Could not find element '{text_to_find}' after {max_swipes} swipes.")
                return False
                
    return False