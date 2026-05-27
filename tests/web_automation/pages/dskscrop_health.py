import cv2
import numpy as np
from pathlib import Path

# =========================================================
# LOAD IMAGE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

image_path = BASE_DIR / "crop_health.png"

img = cv2.imread(str(image_path))

if img is None:
    raise Exception(f"Image not found: {image_path}")

# =========================================================
# CROP FARM AREA
# =========================================================

crop = img[100:700, 500:1200]

output = crop.copy()

# =========================================================
# CONVERT TO GRAYSCALE
# =========================================================

gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

# =========================================================
# DETECT CIRCULAR HEALTH DOTS
# =========================================================

circles = cv2.HoughCircles(
    gray,
    cv2.HOUGH_GRADIENT,
    dp=1.2,
    minDist=12,
    param1=50,
    param2=15,
    minRadius=6,
    maxRadius=12
)

if circles is None:
    raise Exception("No health dots detected")

circles = np.round(circles[0, :]).astype("int")

# =========================================================
# COUNTERS
# =========================================================

yellow_count = 0
orange_count = 0
pink_count = 0
red_count = 0
green_count = 0
black_count = 0

# =========================================================
# HSV IMAGE
# =========================================================

hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

# =========================================================
# CLASSIFY EACH DOT
# =========================================================

for (x, y, r) in circles:

    # Get center pixel HSV
    h, s, v = hsv[y, x]

    # GREEN
    if 35 <= h <= 85:
        green_count += 1
        color = (0, 255, 0)

    # YELLOW
    elif 20 <= h <= 35:
        yellow_count += 1
        color = (0, 255, 255)

    # ORANGE
    elif 10 <= h <= 20:
        orange_count += 1
        color = (0, 165, 255)

    # PINK
    elif 140 <= h <= 170:
        pink_count += 1
        color = (255, 0, 255)

    # RED
    elif (0 <= h <= 10) or (170 <= h <= 180):
        red_count += 1
        color = (0, 0, 255)

    # BLACK / ISSUE
    elif v < 40:
        black_count += 1
        color = (50, 50, 50)

    else:
        continue

    # Draw detected circles
    cv2.circle(output, (x, y), r, color, 2)

# =========================================================
# TOTAL HEALTH CELLS
# =========================================================

total_cells = (
    green_count +
    yellow_count +
    orange_count +
    pink_count +
    red_count +
    black_count
)

# =========================================================
# PERCENTAGES
# =========================================================

def calc(value):
    return round((value / total_cells) * 100, 2)

print("\n========== RESULTS ==========")

print(f"Green          : {calc(green_count)}%")
print(f"Caution Yellow : {calc(yellow_count)}%")
print(f"Warning Orange : {calc(orange_count)}%")
print(f"Stressed Pink  : {calc(pink_count)}%")
print(f"Severe Red     : {calc(red_count)}%")
print(f"Black Issue    : {calc(black_count)}%")

print(f"\nTotal Cells: {total_cells}")

# =========================================================
# SAVE OUTPUT
# =========================================================

cv2.imwrite("detected_dots.png", output)

print("\nDetection image saved")