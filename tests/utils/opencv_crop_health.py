import cv2
import numpy as np
import logging
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)

# ─── HSV color ranges ─────────────────────────────────────────────────────────
GREEN_LOWER = np.array([35, 40, 40])
GREEN_UPPER = np.array([90, 255, 255])

BLUE_LOWER  = np.array([90, 50, 50])
BLUE_UPPER  = np.array([140, 255, 255])

# ─── Percentage thresholds ────────────────────────────────────────────────────
CROP_HEALTH_GREEN_MIN_PCT = 5.0   # crop-health map must have ≥ 5% green pixels
CROP_HEALTH_BLUE_MAX_PCT  = 1.0   # crop-health map must have < 1% blue pixels
MOISTURE_BLUE_MIN_PCT     = 3.0   # moisture cards must have ≥ 3% blue pixels
MOISTURE_GREEN_MAX_PCT    = 1.0   # moisture cards must have < 1% green pixels
SSIM_CHANGE_THRESHOLD     = 0.95  # score < 0.95 → map changed after slider tap

# ─────────────────────────────────────────────────────────────────────────────
# PIXEL FINGERPRINT CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
# Both leaf moisture and soil moisture render the same blue colour family.
# The ONLY reliable way to tell them apart is to:
#   1. Manually open a known-good screenshot of each screen in any image editor.
#   2. Note the (x, y) of a stable, always-blue pixel in the card map area.
#   3. Read its RGB values and paste them below.
#   4. During the test, sample that exact pixel and check it falls within
#      PIXEL_TOLERANCE of the stored reference.
#
# HOW TO CALIBRATE:
#   python - <<'EOF'
#   from utils.cv_validator import get_pixel_rgb
#   # Run this after saving a reference screenshot from the device
#   print(get_pixel_rgb("screenshots/leaf_moisture_reference.png", 540, 900))
#   print(get_pixel_rgb("screenshots/soil_moisture_reference.png", 540, 900))
#   EOF
#
# Then replace the placeholder values below with the printed output.

LEAF_MOISTURE_REFERENCE_PIXEL = {"red": 0, "green": 0, "blue": 0}   # ← FILL IN
SOIL_MOISTURE_REFERENCE_PIXEL = {"red": 0, "green": 0, "blue": 0}   # ← FILL IN

# x, y pixel coordinate to sample on each screen (same point used for both)
MOISTURE_SAMPLE_X = 540   # ← adjust to centre of the coloured card map area
MOISTURE_SAMPLE_Y = 900   # ← adjust to centre of the coloured card map area

# How many RGB units of wiggle room we allow (device rendering variance)
PIXEL_TOLERANCE   = 20


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _load_and_crop(image_path: str, roi: tuple | None):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"cv_validator: cannot read '{image_path}'")
    if roi:
        x, y, w, h = roi
        img = img[y : y + h, x : x + w]
    return img


def _mask_color(img_bgr, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, lower, upper)


def _pct(mask: np.ndarray, total_pixels: int) -> float:
    return round(cv2.countNonZero(mask) / total_pixels * 100, 2)


def _pixel_within_tolerance(actual: dict, reference: dict,
                             tolerance: int = PIXEL_TOLERANCE) -> bool:
    """
    Return True if actual RGB is within `tolerance` units of reference RGB
    on all three channels.
    """
    return all(
        abs(actual[ch] - reference[ch]) <= tolerance
        for ch in ("red", "green", "blue")
    )


# ─── Pixel-level accessors ────────────────────────────────────────────────────

def get_pixel_rgb(image_path: str, x: int, y: int) -> dict:
    img = cv2.imread(image_path)
    b, g, r = img[y, x]
    return {"red": int(r), "green": int(g), "blue": int(b)}


def get_pixel_hsv(image_path: str, x: int, y: int) -> dict:
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[y, x]
    return {"hue": int(h), "saturation": int(s), "value": int(v)}


def calculate_pixel_intensity(pixel: dict) -> float:
    return round((pixel["red"] + pixel["green"] + pixel["blue"]) / 3, 2)


# ─── Percentage utilities ──────────────────────────────────────────────────────

def calculate_green_percentage(image_path: str, roi: tuple | None = None) -> float:
    img   = _load_and_crop(image_path, roi)
    mask  = _mask_color(img, GREEN_LOWER, GREEN_UPPER)
    total = img.shape[0] * img.shape[1]
    pct   = _pct(mask, total)
    logger.debug("Green%%: %.2f  path=%s", pct, image_path)
    return pct


def calculate_blue_percentage(image_path: str, roi: tuple | None = None) -> float:
    img   = _load_and_crop(image_path, roi)
    mask  = _mask_color(img, BLUE_LOWER, BLUE_UPPER)
    total = img.shape[0] * img.shape[1]
    pct   = _pct(mask, total)
    logger.debug("Blue%%: %.2f  path=%s", pct, image_path)
    return pct


# ─── Stress level ─────────────────────────────────────────────────────────────

STRESS_COLORS = {
    "healthy":  {"lower": np.array([40, 60, 60]),  "upper": np.array([85, 255, 255])},
    "moderate": {"lower": np.array([22, 60, 60]),  "upper": np.array([39, 255, 255])},
    "stressed": {"lower": np.array([0,  60, 60]),  "upper": np.array([21, 255, 255])},
    "severe":   {"lower": np.array([160,60, 60]),  "upper": np.array([179,255, 255])},
}


def get_stress_level(image_path: str, roi: tuple | None = None) -> dict:
    img   = _load_and_crop(image_path, roi)
    total = img.shape[0] * img.shape[1]
    result = {}
    for label, bounds in STRESS_COLORS.items():
        mask = _mask_color(img, bounds["lower"], bounds["upper"])
        result[f"{label}_pct"] = _pct(mask, total)
    dominant = max(
        ("healthy", "moderate", "stressed", "severe"),
        key=lambda k: result[f"{k}_pct"]
    )
    result["dominant"] = dominant
    logger.info("Stress level: %s", result)
    return result


# ─── SSIM image comparison ────────────────────────────────────────────────────

def compare_images_ssim(img1_path: str, img2_path: str,
                        roi: tuple | None = None) -> float:
    img1 = _load_and_crop(img1_path, roi)
    img2 = _load_and_crop(img2_path, roi)
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(gray1, gray2, full=True)
    logger.info("SSIM: %.4f  (%s vs %s)", score, img1_path, img2_path)
    return round(float(score), 4)


# ─── High-level validators ────────────────────────────────────────────────────

def validate_crop_health(image_path: str, roi: tuple | None = None) -> dict:
    """
    Assert crop-health map is visible:
      - green pixels ≥ threshold
      - blue  pixels < threshold  (no moisture bleed-in)
    """
    green_pct = calculate_green_percentage(image_path, roi)
    blue_pct  = calculate_blue_percentage(image_path, roi)
    passed    = (green_pct >= CROP_HEALTH_GREEN_MIN_PCT and
                 blue_pct  <  CROP_HEALTH_BLUE_MAX_PCT)
    result = {
        "screen":    "crop_health",
        "green_pct": green_pct,
        "blue_pct":  blue_pct,
        "passed":    passed,
        "reason":    (
            "OK" if passed else
            f"green={green_pct}% (need≥{CROP_HEALTH_GREEN_MIN_PCT}) | "
            f"blue={blue_pct}% (need<{CROP_HEALTH_BLUE_MAX_PCT})"
        ),
    }
    if not passed:
        raise AssertionError(f"[crop_health] {result['reason']}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MOISTURE SCREEN IDENTIFICATION VIA PIXEL FINGERPRINT
# ─────────────────────────────────────────────────────────────────────────────
# Because leaf moisture and soil moisture both render blue pixels at the same
# intensity, the ONLY way to differentiate them programmatically (without
# relying solely on OCR) is to compare the sampled pixel at a fixed (x, y)
# against a pre-calibrated reference value for each screen.
#
# Workflow:
#   Step 1 – Blue pixel check  →  confirms we are on a moisture screen at all
#   Step 2 – Pixel fingerprint →  identifies WHICH moisture screen
#   Step 3 – OCR title check   →  secondary confirmation (in ocr_utils.py)
# ─────────────────────────────────────────────────────────────────────────────

def _validate_moisture_common(image_path: str, roi: tuple | None) -> dict:
    """Shared blue-pixel check used by both leaf and soil validators."""
    blue_pct  = calculate_blue_percentage(image_path, roi)
    green_pct = calculate_green_percentage(image_path, roi)
    passed    = (blue_pct  >= MOISTURE_BLUE_MIN_PCT and
                 green_pct <  MOISTURE_GREEN_MAX_PCT)
    return {
        "blue_pct":  blue_pct,
        "green_pct": green_pct,
        "blue_check_passed": passed,
    }


def validate_leaf_moisture(image_path: str,
                            sample_x: int = MOISTURE_SAMPLE_X,
                            sample_y: int = MOISTURE_SAMPLE_Y,
                            roi: tuple | None = None) -> dict:

    common   = _validate_moisture_common(image_path, roi)
    actual   = get_pixel_rgb(image_path, sample_x, sample_y)
    fp_match = _pixel_within_tolerance(actual, LEAF_MOISTURE_REFERENCE_PIXEL)

    passed   = common["blue_check_passed"] and fp_match
    result   = {
        "screen":        "leaf_moisture",
        **common,
        "sample_xy":     (sample_x, sample_y),
        "actual_pixel":  actual,
        "reference_pixel": LEAF_MOISTURE_REFERENCE_PIXEL,
        "fingerprint_match": fp_match,
        "tolerance":     PIXEL_TOLERANCE,
        "passed":        passed,
        "reason":        (
            "OK" if passed else
            f"blue_check={common['blue_check_passed']} | "
            f"fp_match={fp_match} actual={actual} ref={LEAF_MOISTURE_REFERENCE_PIXEL}"
        ),
    }
    if not passed:
        raise AssertionError(f"[leaf_moisture] {result['reason']}")
    logger.info("validate_leaf_moisture PASSED: %s", result)
    return result


def validate_soil_moisture(image_path: str,
                            sample_x: int = MOISTURE_SAMPLE_X,
                            sample_y: int = MOISTURE_SAMPLE_Y,
                            roi: tuple | None = None) -> dict:
    
    common   = _validate_moisture_common(image_path, roi)
    actual   = get_pixel_rgb(image_path, sample_x, sample_y)
    fp_match = _pixel_within_tolerance(actual, SOIL_MOISTURE_REFERENCE_PIXEL)

    passed   = common["blue_check_passed"] and fp_match
    result   = {
        "screen":        "soil_moisture",
        **common,
        "sample_xy":     (sample_x, sample_y),
        "actual_pixel":  actual,
        "reference_pixel": SOIL_MOISTURE_REFERENCE_PIXEL,
        "fingerprint_match": fp_match,
        "tolerance":     PIXEL_TOLERANCE,
        "passed":        passed,
        "reason":        (
            "OK" if passed else
            f"blue_check={common['blue_check_passed']} | "
            f"fp_match={fp_match} actual={actual} ref={SOIL_MOISTURE_REFERENCE_PIXEL}"
        ),
    }
    if not passed:
        raise AssertionError(f"[soil_moisture] {result['reason']}")
    logger.info("validate_soil_moisture PASSED: %s", result)
    return result


# ─── Calibration helper ───────────────────────────────────────────────────────

def calibrate_moisture_pixels(leaf_screenshot: str,
                               soil_screenshot: str,
                               sample_x: int = MOISTURE_SAMPLE_X,
                               sample_y: int = MOISTURE_SAMPLE_Y) -> dict:
   
    leaf_pixel = get_pixel_rgb(leaf_screenshot, sample_x, sample_y)
    soil_pixel = get_pixel_rgb(soil_screenshot, sample_x, sample_y)
    print("=" * 50)
    print(f"LEAF_MOISTURE_REFERENCE_PIXEL = {leaf_pixel}")
    print(f"SOIL_MOISTURE_REFERENCE_PIXEL = {soil_pixel}")
    print(f"Sample coordinate: ({sample_x}, {sample_y})")
    print("=" * 50)
    return {"leaf": leaf_pixel, "soil": soil_pixel}


# ─── Date slider validator ────────────────────────────────────────────────────

def validate_date_slider_changed(before_path: str, after_path: str,
                                  roi: tuple | None = None) -> dict:
    """
    Confirm map re-rendered after a plus/minus tap (SSIM < threshold).
    Also records green-pixel delta and stress-level change across dates.
    """
    score  = compare_images_ssim(before_path, after_path, roi)
    changed = score < SSIM_CHANGE_THRESHOLD

    green_before   = calculate_green_percentage(before_path, roi)
    green_after    = calculate_green_percentage(after_path, roi)
    stress_before  = get_stress_level(before_path, roi)
    stress_after   = get_stress_level(after_path, roi)

    result = {
        "ssim_score":         score,
        "map_changed":        changed,
        "green_before_pct":   green_before,
        "green_after_pct":    green_after,
        "green_delta":        round(green_after - green_before, 2),
        "stress_before":      stress_before["dominant"],
        "stress_after":       stress_after["dominant"],
        "full_stress_before": stress_before,
        "full_stress_after":  stress_after,
    }
    if not changed:
        logger.warning("Slider may not have updated map (SSIM=%.4f)", score)
    else:
        logger.info("Slider map change confirmed (SSIM=%.4f): %s", score, result)
    return result