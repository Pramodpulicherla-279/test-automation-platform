import allure
# --- NEW IMPORTS for the modern W3C Actions API ---
from selenium.webdriver.common.actions.action_builder import ActionBuilder
import sys
sys.dont_write_bytecode = True

def tap_at_coordinates(driver, x, y):
    """
    Performs a tap action at the specified x and y coordinates on the screen.
    This function uses the W3C Actions API, which is compatible with the latest
    Appium Python Client (v3+).

    Args:
        driver: The Appium driver instance.
        x (int): The x-coordinate for the tap.
        y (int): The y-coordinate for the tap.
    """
    try:
        print(f"Attempting to tap at coordinates: (x={x}, y={y})")
        
        # 1. Create an ActionBuilder object, which is the entry point for all actions.
        actions = ActionBuilder(driver)
        
        # 2. Get a reference to the 'pointer' (i.e., your finger on the screen).
        finger = actions.pointer_action
        
        # 3. Define the sequence of actions for a tap:
        #    - Move the pointer to the target coordinates.
        #    - Press the pointer down (touch the screen).
        #    - Pause briefly to ensure the tap registers reliably.
        #    - Lift the pointer up (release the touch).
        finger.move_to_location(x, y)
        finger.pointer_down()
        finger.pause(0.1)
        finger.pointer_up()
        
        # 4. Execute the entire sequence of actions.
        actions.perform()
        
        print(f"Successfully tapped at (x={x}, y={y}).")
        allure.attach(f"Tapped at coordinates (x={x}, y={y})", name="Coordinate Tap", attachment_type=allure.attachment_type.TEXT)
        return True
    except Exception as e:
        print(f"Failed to tap at coordinates: {e}")
        allure.attach(f"Failed to tap at (x={x}, y={y}): {e}", name="Coordinate Tap Error", attachment_type=allure.attachment_type.TEXT)
        return False
