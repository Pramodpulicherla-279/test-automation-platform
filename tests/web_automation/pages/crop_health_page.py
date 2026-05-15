import cv2
import numpy as np
from pathlib import Path

# ─────────────────────────────────────────────
# Load Image
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent

image_path = BASE_DIR / "crop_health.png"

img = cv2.imread(str(image_path))

if img is None:
    raise Exception(f"Image not found: {image_path}")

# ─────────────────────────────────────────────
# Crop Required Area (Adjust if needed)
# ─────────────────────────────────────────────

crop = img[100:700, 500:1200]

# Convert BGR → HSV
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

# ─────────────────────────────────────────────
# COLOR RANGES
# ─────────────────────────────────────────────

# YELLOW → Caution
lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([35, 255, 255])

# ORANGE → Warning
lower_orange = np.array([10, 120, 120])
upper_orange = np.array([20, 255, 255])

# PINK → Stressed
lower_pink = np.array([140, 50, 50])
upper_pink = np.array([170, 255, 255])

# RED → Severe Stress
lower_red1 = np.array([0, 120, 120])
upper_red1 = np.array([10, 255, 255])

lower_red2 = np.array([170, 120, 120])
upper_red2 = np.array([180, 255, 255])

# ─────────────────────────────────────────────
# CREATE MASKS
# ─────────────────────────────────────────────

yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

orange_mask = cv2.inRange(hsv, lower_orange, upper_orange)

pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)

red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

red_mask = red_mask1 + red_mask2

# ─────────────────────────────────────────────
# COUNT PIXELS
# ─────────────────────────────────────────────

yellow_pixels = cv2.countNonZero(yellow_mask)
orange_pixels = cv2.countNonZero(orange_mask)
pink_pixels = cv2.countNonZero(pink_mask)
red_pixels = cv2.countNonZero(red_mask)

# ─────────────────────────────────────────────
# TOTAL DETECTED PIXELS
# ─────────────────────────────────────────────

total = (
    yellow_pixels +
    orange_pixels +
    pink_pixels +
    red_pixels
)

if total == 0:
    raise Exception("No health pixels detected")

# ─────────────────────────────────────────────
# PERCENTAGE CALCULATION
# ─────────────────────────────────────────────

yellow_percent = (yellow_pixels / total) * 100
orange_percent = (orange_pixels / total) * 100
pink_percent = (pink_pixels / total) * 100
red_percent = (red_pixels / total) * 100

# ─────────────────────────────────────────────
# PRINT RESULTS
# ─────────────────────────────────────────────

print(f"Caution (Yellow): {yellow_percent:.2f}%")
print(f"Warning (Orange): {orange_percent:.2f}%")
print(f"Stressed (Pink): {pink_percent:.2f}%")
print(f"Severe Stress (Red): {red_percent:.2f}%")

# ─────────────────────────────────────────────
# OPTIONAL → SAVE DETECTED MASKS
# ─────────────────────────────────────────────

cv2.imwrite("yellow_mask.png", yellow_mask)
cv2.imwrite("orange_mask.png", orange_mask)
cv2.imwrite("pink_mask.png", pink_mask)
cv2.imwrite("red_mask.png", red_mask)

print("Masks saved successfully")