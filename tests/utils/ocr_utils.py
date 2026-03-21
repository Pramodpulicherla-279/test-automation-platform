import pytesseract
from PIL import Image
import cv2
import numpy as np
import time
import os
import sys
sys.dont_write_bytecode = True

def extract_text_with_coordinates(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    texts = []
    for i in range(len(data["text"])):
        if int(data["conf"][i]) > 70:
            text = data["text"][i].strip()
            if text:
                (x, y, w, h) = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
                texts.append({"text": text, "coords": (x + w//2, y + h//2)})
    return texts

def click_element_by_ocr_text(driver, target_text, screenshot_path):
    matches = extract_text_with_coordinates(screenshot_path)
    print(f"[OCR] Looking for '{target_text}' in screenshot: {screenshot_path}")
    print(f"[OCR] Detected texts: {[m['text'] for m in matches]}")
    for match in matches:
        print(f"[OCR] Checking: '{match['text']}' at {match['coords']}")
        if target_text.lower() in match["text"].lower():
            x, y = match["coords"]
            print(f"[OCR] Match found! Tapping at ({x}, {y})")
            driver.tap([(x, y)], 100)  # duration=100ms
            return True
    print(f"[OCR] No match found for '{target_text}'")
    return False

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)
