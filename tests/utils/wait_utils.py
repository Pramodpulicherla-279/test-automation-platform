from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy
from utils.ocr_utils import click_element_by_ocr_text
from selenium.common.exceptions import NoSuchElementException
from appium.webdriver.common.appiumby import AppiumBy
import allure
# --- NEW IMPORTS for the modern W3C Actions API ---
from selenium.webdriver.common.actions.action_builder import ActionBuilder

def find_and_click(driver, by, value, fallback_text=None, timeout=20):
    """
    Tries to find and click an element by its primary locator.
    If that fails and a fallback_text is provided, it tries to click by text.

    Args:
        driver: The Appium driver instance.
        by: The locator strategy (e.g., AppiumBy.XPATH).
        value: The locator string (e.g., "//your/xpath").
        fallback_text: The visible text to use as a fallback locator.
        timeout: The maximum time to wait for the element.

    Returns:
        True if the element was clicked successfully, False otherwise.
    """
    try:
        # 1. Try to click using the primary locator (e.g., XPath)
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


# def smart_find_element(driver, name, xpath, fallback_text=None, screenshot_path="screenshots/ocr_fallback.png"):
#     """
#     Find element with OCR fallback.
#     Returns tuple: (element, was_found_by_ocr)
#     """
#     try:
#         # Try finding by XPath first
#         element = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, xpath))
#         )
#         return element, False
#     except:
#         print(f"Element '{name}' not found via XPath. Trying OCR fallback...")

#         # Take screenshot
#         driver.save_screenshot(screenshot_path)

#         # Try clicking by text via OCR
#         if fallback_text:
#             found = click_element_by_ocr_text(driver, fallback_text, screenshot_path)
#             if found:
#                 print(f"OCR clicked on '{fallback_text}' successfully.")
#                 return None, True  # Indicate OCR was used
#             else:
#                 print(f"OCR failed to find '{fallback_text}' on screen.")

#         return None, False
    
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
            # Search for any element containing the text
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
                        size = driver.get_window_size()
                        driver.swipe(size['width']//2, int(size['height']*0.8), size['width']//2, int(size['height']*0.2), 400)
        except Exception as e:
            print(f"   -> DOM text search failed: {e}")

    # 3. OCR Strategy (Last Resort - Slow)
    print("   -> Initiating OCR fallback (this may take time)...")
    driver.save_screenshot(screenshot_path)

    if fallback_text:
        found = click_element_by_ocr_text(driver, fallback_text, screenshot_path)
        if found:
            print(f"OCR clicked on '{fallback_text}' successfully.")
            return None, True 
        else:
            print(f"OCR failed to find '{fallback_text}' on screen.")

    return None, False

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
            size = driver.get_window_size()
            start_x = size['width'] / 2
            start_y = size['height'] * 0.8
            end_y = size['height'] * 0.2
            driver.swipe(start_x, start_y, start_x, end_y, 400)

    print(f"Failed to find or click '{text_to_find}' after {max_swipes} swipes.")
    return False

def scroll_and_tap_by_text(driver, text_to_find, max_swipes=5):
    """
    Scrolls down to find an element by its text and performs a coordinate-based tap
    on its center. This version uses the W3C Actions API, making it compatible with
    the latest Appium Python Client and robust for parallel testing.

    Args:
        driver: The Appium driver instance.
        text_to_find: The visible text of the element to tap.
        max_swipes: The maximum number of swipes to prevent an infinite loop.

    Returns:
        True if the element was found and tapped, False otherwise.
    """
    for i in range(max_swipes):
        try:
            # 1. Use the universal XPath to find the element (this part is correct)
            universal_xpath = f"//*[contains(@text, '{text_to_find}') or contains(@content-desc, '{text_to_find}')]"
            element = driver.find_element(AppiumBy.XPATH, universal_xpath)
            
            # 2. Dynamically get the element's location (this part is correct)
            location = element.location
            size = element.size
            center_x = location['x'] + size['width'] / 2
            center_y = location['y'] + size['height'] / 2
            
            print(f"Found '{text_to_find}'. Tapping at dynamic coordinates: ({center_x}, {center_y})")
            allure.attach(f"Tapping '{text_to_find}' on {driver.capabilities.get('deviceName')} at ({center_x}, {center_y})", 
                          name="Dynamic Coordinate Tap", attachment_type=allure.attachment_type.TEXT)
            
            # --- REPLACEMENT for TouchAction ---
            # 3. Perform the raw tap action using W3C Actions
            actions = ActionBuilder(driver)
            finger = actions.pointer_action
            finger.move_to_location(center_x, center_y)
            finger.pointer_down()
            finger.pause(0.1) # A brief pause improves tap reliability
            finger.pointer_up()
            actions.perform()
            # --- END REPLACEMENT ---
            
            return True
            
        except NoSuchElementException:
            # 4. If not found, scroll down and try again
            if i < max_swipes - 1:
                print(f"'{text_to_find}' not found, scrolling down...")
                screen_size = driver.get_window_size()
                start_x = screen_size['width'] / 2
                start_y = screen_size['height'] * 0.8
                end_y = screen_size['height'] * 0.2
                
                # --- REPLACEMENT for driver.swipe() ---
                # 5. Perform the swipe using W3C Actions
                actions = ActionBuilder(driver)
                finger = actions.pointer_action
                finger.move_to_location(start_x, start_y)
                finger.pointer_down()
                finger.move_to_location(start_x, end_y)
                finger.pointer_up()
                actions.perform()
                # --- END REPLACEMENT ---
                
            else:
                # This is the last swipe attempt, and it still wasn't found.
                print(f"Could not find element '{text_to_find}' after {max_swipes} swipes.")
                return False
                
    return False