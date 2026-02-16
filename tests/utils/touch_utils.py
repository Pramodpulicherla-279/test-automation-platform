from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction

def tap_at_coordinates(driver, x, y):
    """
    Taps at (x, y) using W3C Pointer Actions (Touch).
    Compatible with latest Appium/Selenium versions.
    """
    # Create a touch input device
    touch_input = PointerInput(interaction.POINTER_TOUCH, "touch")
    
    # --- FIX: Do NOT pass mouse_button to ActionBuilder ---
    actions = ActionBuilder(driver)
    actions.devices = [touch_input] # Force it to use our touch device
    
    pointer = actions.pointer_action
    pointer.move_to_location(x, y)
    pointer.pointer_down()
    pointer.pause(0.1)
    pointer.pointer_up()
    
    actions.perform()
    return True

def perform_scroll(driver, start_x=500, start_y=1500, end_x=500, end_y=500, duration=600):
    """
    Scrolls using W3C Pointer Actions.
    """
    touch_input = PointerInput(interaction.POINTER_TOUCH, "touch")
    
    # --- FIX: Do NOT pass mouse_button here either ---
    actions = ActionBuilder(driver)
    actions.devices = [touch_input]
    
    pointer = actions.pointer_action
    pointer.move_to_location(start_x, start_y)
    pointer.pointer_down()
    pointer.pause(duration / 1000)
    pointer.move_to_location(end_x, end_y)
    pointer.release()
    
    actions.perform()
    return True