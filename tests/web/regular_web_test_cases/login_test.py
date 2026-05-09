# import json
# import pytest
# from browser_manager import BrowserManager
# from web.pages.login_page import LoginPage
# from pathlib import Path


# data_path = Path(__file__).parent.parent / "data" / "login_data.json"

# @pytest.mark.asyncio
# async def test_login():
#     # Load test data
#     with open(data_path) as f:
#         data = json.load(f)

#     browser = BrowserManager()
#     page = await browser.start()

#     login_page = LoginPage(page)

#     # Steps
#     await login_page.navigate(data["url"])
#     await login_page.login(data["username"], data["password"])

#     # Assertion
#     dashboard_text = await login_page.get_dashboard_text()
#     assert data["expected_text"] in dashboard_text



#     await browser.stop()

# login_onboarding_test.py
import json
import pytest
from browser_manager import BrowserManager
from web.pages.login_page import LoginPage
from web.pages.onboarding_page import OnboardingPage
from pathlib import Path

data_path = Path(__file__).parent.parent / "data" / "login_data.json"

@pytest.mark.asyncio
async def test_login_and_onboarding():
    # Load test data
    with open(data_path) as f:
        data = json.load(f)

    browser = BrowserManager()
    page = await browser.start()

    try:
        # --- Step 1: Login ---
        login_page = LoginPage(page)
        await login_page.navigate(data["url"])
        await login_page.login(data["username"], data["password"])

        dashboard_text = await login_page.get_dashboard_text()
        assert data["expected_text"] in dashboard_text

        # --- Step 2: Onboarding (reuses same logged-in page) ---
        onboarding = OnboardingPage(page)
        await onboarding.complete_onboarding_flow()
        # await page.wait_for_selector("text=Add New Farmer")

    finally:
        await browser.stop()  # ✅ always closes even if test fails