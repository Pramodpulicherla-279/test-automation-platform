"""
conftest.py — sync Playwright, Windows + anyio safe
=====================================================
Uses sync Playwright API throughout.
No async fixtures = no event loop conflicts with anyio on Windows.
Tests are written as plain `def` (not async def).
"""

import json
import pytest
import allure
from pathlib import Path
from playwright.sync_api import sync_playwright, Page


# ── module-level holders ──────────────────────────────────────────────
_pw      = None
_browser = None
_context = None
_page    = None


@pytest.fixture(scope="session", autouse=True)
def launch_browser():
    global _pw, _browser, _context, _page

    _pw = sync_playwright().start()
    _browser = _pw.chromium.launch(headless=False, slow_mo=200)
    _context = _browser.new_context(
        viewport={"width": 1440, "height": 900},
        permissions=["geolocation"],
        geolocation={
            "latitude": 17.3850,
            "longitude": 78.4867
        }
    )
    _context.set_default_timeout(15_000)
    _page = _context.new_page()

    yield

    _page.close()
    _context.close()
    _browser.close()
    _pw.stop()


@pytest.fixture(scope="session")
def shared_page() -> Page:
    return _page


@pytest.fixture(scope="session")
def test_data():
    path = Path(__file__).parent / "test_data" / "test_data.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def login_page(shared_page):
    from pages.login_page import LoginPage
    return LoginPage(shared_page)


@pytest.fixture(scope="session")
def onboarding_page(shared_page):
    from pages.onboarding_page import OnboardingPage
    return OnboardingPage(shared_page)

@pytest.fixture(scope="session")
def field_update_page(shared_page):
    from pages.field_update_page import Field_Update_Page
    return Field_Update_Page(shared_page)

@pytest.fixture(scope="session")
def crop_health_page(shared_page):
    from pages.crop_health_page import Crop_Health_Page
    return Crop_Health_Page(shared_page)

# ── screenshot on failure ─────────────────────────────────────────────
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("shared_page")
        if page:
            try:
                screenshot = page.screenshot()
                allure.attach(screenshot, name=f"failure_{item.name}",
                              attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass