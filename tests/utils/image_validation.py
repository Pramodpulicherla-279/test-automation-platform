import os
import time
import cv2

def capture_screen(driver, name):
    folder = "screenshots/crop_health"
    os.makedirs(folder, exist_ok=True)

    path = f"{folder}/{name}_{int(time.time())}.png"

    driver.save_screenshot(path)

    return path


def crop_map_area(image_path):

    image = cv2.imread(image_path)

    # Example coordinates
    cropped = image[250:1400, 50:1000]

    crop_path = image_path.replace(".png", "_crop.png")

    cv2.imwrite(crop_path, cropped)

    return crop_path