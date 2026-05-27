from __future__ import annotations

import os
import time
import logging

import cv2

logger = logging.getLogger(__name__)

# ─── Default directory ─────────────────────────────────────────────────────────
_DEFAULT_SCREENSHOT_DIR = "screenshots/crop_health"

# ─── Title-region box returned to OCR helpers ─────────────────────────────────
# (left, top, right, bottom) in pixels — adjust to match your device resolution.
# This region should cover the card/screen title text visible on the screenshots.
# Calibrate by opening a reference screenshot and measuring the title text area.
_TITLE_REGION: tuple[int, int, int, int] = (0, 50, 1080, 200)


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _make_dirs(folder: str) -> None:
    """Create the screenshot output folder if it does not already exist."""
    os.makedirs(folder, exist_ok=True)


def _build_path(folder: str, name: str, suffix: str = "") -> str:
    ts = int(time.time())
    filename = f"{name}_{ts}{suffix}.png"
    return os.path.join(folder, filename)


def _crop_and_save(image_path: str, roi: tuple[int, int, int, int],
                   crop_path: str) -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(
            f"screenshot_utils: cannot read image at '{image_path}'"
        )

    img_h, img_w = img.shape[:2]
    x, y, w, h = roi

    # Clamp roi to image bounds so a slightly-off roi never crashes the run.
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(1, min(w, img_w - x))
    h = max(1, min(h, img_h - y))

    if w <= 0 or h <= 0:
        raise ValueError(
            f"screenshot_utils: ROI {roi} is entirely outside image "
            f"({img_w}×{img_h}). Check MAP_ROI / CARD_ROI constants."
        )

    cropped = img[y : y + h, x : x + w]
    cv2.imwrite(crop_path, cropped)
    logger.debug("Cropped %s → %s  roi=%s", image_path, crop_path, roi)
    return crop_path


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def capture_screen(
    driver,
    name: str,
    folder: str = _DEFAULT_SCREENSHOT_DIR,
) -> str:
    _make_dirs(folder)
    path = _build_path(folder, name)
    driver.save_screenshot(path)
    logger.info("Screenshot saved: %s", path)
    return path


def capture_and_crop_map(
    driver,
    name: str,
    folder: str,
    roi: tuple[int, int, int, int],
) -> tuple[str, str]:
    full_path   = capture_screen(driver, name, folder)
    crop_path   = _build_path(folder, name, suffix="_map_crop")
    _crop_and_save(full_path, roi, crop_path)
    return full_path, crop_path


def capture_and_crop_card(
    driver,
    name: str,
    folder: str,
    roi: tuple[int, int, int, int],
) -> tuple[str, str]:
    full_path   = capture_screen(driver, name, folder)
    crop_path   = _build_path(folder, name, suffix="_card_crop")
    _crop_and_save(full_path, roi, crop_path)
    return full_path, crop_path


def get_title_region_pil() -> tuple[int, int, int, int]:
    return _TITLE_REGION