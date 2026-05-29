import platform
import logging
import re
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

logger = logging.getLogger(__name__)

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

_CFG_BLOCK  = "--psm 6 --oem 3"
_CFG_SPARSE = "--psm 11 --oem 3"

LEAF_MOISTURE_KEYWORDS  = ["leaf moisture", "leaf wetness", "leaf wet"]
SOIL_MOISTURE_KEYWORDS  = ["soil moisture", "soil wet"]
CROP_HEALTH_KEYWORDS    = ["crop health", "ndvi", "vegetation"]


def _preprocess(pil_img: Image.Image) -> Image.Image:
    img = pil_img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img


def _crop_pil(pil_img: Image.Image, region: tuple | None) -> Image.Image:
    return pil_img.crop(region) if region else pil_img


def extract_text(image_path: str, region: tuple | None = None,
                 sparse: bool = False) -> str:
    img  = Image.open(image_path)
    img  = _crop_pil(img, region)
    img  = _preprocess(img)
    cfg  = _CFG_SPARSE if sparse else _CFG_BLOCK
    raw  = pytesseract.image_to_string(img, config=cfg)
    text = re.sub(r"[^\x20-\x7E\n]", " ", raw)
    text = re.sub(r" {2,}", " ", text).strip()
    logger.debug("OCR: %r  (region=%s)", text, region)
    return text


def extract_card_title(image_path: str,
                       title_region: tuple | None = None) -> str:
    """
    Extract text from the card title band.
    title_region is a PIL (left, top, right, bottom) tuple.
    If omitted, defaults to the top 20% of the image.
    """
    if title_region is None:
        img  = Image.open(image_path)
        w, h = img.size
        title_region = (0, int(h * 0.05), w, int(h * 0.20))
    return extract_text(image_path, region=title_region, sparse=True)


def _contains_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in keywords)


# ─────────────────────────────────────────────────────────────────────────────
# OCR is used as the PRIMARY identification method here.
# Pixel fingerprint (cv_validator) acts as secondary confirmation.
# Together they give two independent signals for each moisture screen.
# ─────────────────────────────────────────────────────────────────────────────

def identify_moisture_screen(image_path: str,
                              title_region: tuple | None = None) -> str:
    """
    Read the card title and return 'leaf_moisture', 'soil_moisture', or 'unknown'.
    This is the primary screen-type oracle — use validate_leaf/soil_moisture()
    from cv_validator as a secondary pixel-level confirmation.
    """
    title = extract_card_title(image_path, title_region)
    if _contains_any(title, LEAF_MOISTURE_KEYWORDS):
        logger.info("OCR identified: leaf_moisture  (title=%r)", title)
        return "leaf_moisture"
    if _contains_any(title, SOIL_MOISTURE_KEYWORDS):
        logger.info("OCR identified: soil_moisture  (title=%r)", title)
        return "soil_moisture"
    logger.warning("OCR could not identify moisture screen (title=%r)", title)
    return "unknown"


def is_leaf_moisture_screen(image_path: str,
                             title_region: tuple | None = None) -> bool:
    return identify_moisture_screen(image_path, title_region) == "leaf_moisture"


def is_soil_moisture_screen(image_path: str,
                             title_region: tuple | None = None) -> bool:
    return identify_moisture_screen(image_path, title_region) == "soil_moisture"


def is_crop_health_screen(image_path: str,
                          title_region: tuple | None = None) -> bool:
    title = extract_card_title(image_path, title_region)
    found = _contains_any(title, CROP_HEALTH_KEYWORDS)
    logger.info("is_crop_health_screen=%s (title=%r)", found, title)
    return found


def validate_screen_title(image_path: str, expected_keyword: str,
                          region: tuple | None = None) -> str:
    text = extract_text(image_path, region=region, sparse=True)
    if expected_keyword.lower() not in text.lower():
        raise AssertionError(
            f"OCR title check failed: '{expected_keyword}' not found in:\n{text!r}"
        )
    logger.info("validate_screen_title PASSED: '%s' found", expected_keyword)
    return text