import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.abspath(__file__))))
ALLURE_CMD = r"C:\Users\Pramo\scoop\shims\allure"
ALLURE_REPORT_DIR = os.path.join(BASE_DIR, "allure-report")

UI_SCREENSHOTS_BASE = Path(__file__).resolve().parents[1] / "artifacts" / "ui_screenshots"
UI_SCREENSHOTS_BASE.mkdir(parents=True, exist_ok=True)
