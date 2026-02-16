import json
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def find_and_click(driver, locator_strategy, locator_value, element_name, timeout=10):
    """
    Waits for an element to be clickable and clicks it.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"Attempting to find and click: {element_name}")
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((locator_strategy, locator_value))
        )
        element.click()
        print(f"Successfully clicked: {element_name}")
        return True
    except (TimeoutException, NoSuchElementException):
        print(f"Failed to find or click: {element_name}")
        return False
    except Exception as e:
        print(f"Error clicking {element_name}: {str(e)}")
        return False

def load_locators(file_name="elements.json"):
    """
    Loads the JSON file and flattens it so you can access keys directly.
    Example: accessing LOCATORS['crop_name_input'] will work even if it's nested.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, file_name)

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # --- FLATTENING LOGIC ---
        flat_locators = {}
        for screen, content in data.items():
            # Check if the content is a dictionary (like "farmer_screen": {...})
            if isinstance(content, dict):
                for key, value in content.items():
                    flat_locators[key] = value
            else:
                # If it's a top-level key, just add it
                flat_locators[screen] = content
                
        return flat_locators

    except FileNotFoundError:
        raise Exception(f"Locator file not found at: {file_path}")