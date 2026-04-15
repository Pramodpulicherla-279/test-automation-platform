# How to Modify Your Existing Tests - Step by Step

This guide shows you exactly how to add API validation to your existing tests.

---

## Your Current Test Structure

Your existing test (`test_login_pytest.py`) looks like this:

```python
@allure.epic("Login Flow")
@allure.feature("Authentication")
class TestLogin:
    
    def test_login_success(self, driver):
        # Step 1: Click Next on language screen
        # Step 2: Allow permissions
        # Step 3: Enter phone number
        # Step 4: Verify OTP
        # Etc...
```

---

## Step 1: Add Imports

At the top of your test file, add these imports:

```python
# Add these 2 lines to your imports
from utils.api_validator import APIValidator
import pytest
```

**Your imports should now look like:**

```python
import time
import allure
import pytest  # ✅ Already there or add it
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_find_element, smart_click
from utils.ocr_utils import extract_text_with_coordinates
from utils.api_validator import APIValidator  # ✅ ADD THIS
import json
import os
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import find_and_click
import sys
sys.dont_write_bytecode = True
```

---

## Step 2: Add the Fixture

Inside your `TestLogin` class, add this fixture method right after the class declaration:

```python
class TestLogin:
    
    # ✅ ADD THIS - initializes API validator for all tests
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize API validator before each test"""
        self.api = APIValidator(base_url="http://localhost:8000")  # Change URL if needed
        yield
    
    @allure.story("Successful Login")
    @allure.title("Verify user can login with valid credentials")
    def test_login_success(self, driver):
        # ... rest of your test code
```

---

## Step 3: Add API Validation Steps

After each major UI step or at the end of your test, add API validation steps.

### Option A: Validate at End of Test (Easiest)

Add this code after your last UI step, before the test ends:

```python
def test_login_success(self, driver):
    # ... your existing UI code ...
    
    with allure.step("8. Wait for OTP and verify"):
        time.sleep(20)
        if not smart_click(driver, "Verify (login)", verify_button_login_xpath, "Verify"):
            pytest.fail("Could not find or click the 'Verify' button.")
        test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
    
    # ✅ ADD THIS - Validate API endpoints
    with allure.step("9. Verify session via API"):
        """Verify that user is authenticated by checking backend API"""
        self.api.assert_endpoint(
            method="GET",
            endpoint="/api/auth/verify",  # Change to your actual endpoint
            expected_status=200,
            description="Verify user session is active"
        )
    
    with allure.step("10. Verify user profile via API"):
        """Verify that user profile is accessible"""
        self.api.assert_endpoint(
            method="GET",
            endpoint="/api/user/profile",  # Change to your actual endpoint
            expected_status=200,
            description="Get user profile from backend"
        )
    
    with allure.step("11. Check API test results"):
        """Assert all API calls passed"""
        summary = self.api.get_summary()
        assert summary["failed"] == 0, f"API validation failed: {summary}"
```

### Option B: Validate Inline (After Specific Steps)

Add validation steps right after key UI interactions:

```python
with allure.step("7. Tap next button"):
    if not smart_click(driver, "Next (login)", next_button_login_xpath, "Next"):
        pytest.fail("Could not find or click the 'Next' button after entering phone number.")
    test_flow_steps.append({"step": "Click Next after entering phone number", "status": "Success"})

# ✅ ADD THIS - Validate login API was called
with allure.step("7b. Verify login API was called"):
    self.api.assert_endpoint(
        method="POST",
        endpoint="/api/auth/login",
        expected_status=[200, 201],  # Accept either status
        description="Verify login endpoint was successful"
    )
```

---

## Complete Modified Test Example

Here's what your complete modified `test_login_pytest.py` should look like:

```python
import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_find_element, smart_click
from utils.ocr_utils import extract_text_with_coordinates
from utils.api_validator import APIValidator  # ✅ NEW
import json
import os
from selenium.common.exceptions import WebDriverException
from utils.wait_utils import find_and_click
import sys
sys.dont_write_bytecode = True

@allure.epic("Login Flow")
@allure.feature("Authentication")
class TestLogin:
    
    # ✅ NEW - Initialize API validator
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize API validator"""
        self.api = APIValidator(base_url="http://localhost:8000")
        yield
    
    @allure.story("Successful Login")
    @allure.title("Verify user can login with valid credentials")
    def test_login_success(self, driver):
        test_flow_steps = []
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locators_path = os.path.join(project_root, "locators", "regular_farmer.json")

        with open(locators_path, 'r') as f:
            xpaths = json.load(f)

        login_screen_xpaths = xpaths.get("login_screen", {})
        language_next_xpath = login_screen_xpaths.get("next_button_language_login")
        allow_picture_button_xpath = login_screen_xpaths.get("allow_picture_button")
        allow_location_button_xpath = login_screen_xpaths.get("allow_location_button")
        allow_audio_button_xpath = login_screen_xpaths.get("allow_audio_button")
        allow_notifications_button_xpath = login_screen_xpaths.get("allow_notifications_button")
        phone_number_input_xpath = login_screen_xpaths.get("phone_number_input")
        next_button_login_xpath = login_screen_xpaths.get("next_button_login")
        verify_button_login_xpath = login_screen_xpaths.get("verify_button_login")

        try:
            with allure.step("1. Next button on language selection screen"):
                if not smart_click(driver, "Next Button (Language)", language_next_xpath, "Next"):
                    pytest.fail("Could not find or click the 'Next button on language selection' button.")
                test_flow_steps.append({"step": "Click Next button on language selection", "status": "Success"})
            
            # ... rest of your UI steps ...
            
            with allure.step("8. Wait for OTP and verify"):
                time.sleep(20)
                if not smart_click(driver, "Verify (login)", verify_button_login_xpath, "Verify"):
                    pytest.fail("Could not find or click the 'Verify' button.")
                test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})
            
            # ✅ NEW - Add API validation
            with allure.step("9. Verify session via API"):
                self.api.assert_endpoint(
                    method="GET",
                    endpoint="/api/auth/verify",
                    expected_status=200,
                    description="User session is active"
                )
            
            with allure.step("10. Verify user profile"):
                self.api.assert_endpoint(
                    method="GET",
                    endpoint="/api/user/profile",
                    expected_status=200,
                    description="User profile accessible"
                )
            
            with allure.step("11. Validate all APIs"):
                summary = self.api.get_summary()
                print(f"API Results: {summary}")
                assert summary["failed"] == 0, f"API tests failed: {summary}"
        
        except Exception as e:
            pytest.fail(f"Test failed: {str(e)}")
```

---

## What API Endpoints to Call?

Identify the APIs your backend calls during login. Examples might be:

| API | Method | Purpose |
|-----|--------|---------|
| `/api/auth/login` | POST | Authenticate user |
| `/api/auth/verify` | GET | Check if session is active |
| `/api/user/profile` | GET | Get user profile |
| `/api/user/me` | GET | Get current user info |
| `/api/auth/session` | GET | Check session status |

**To find these:**
1. Check your backend API documentation
2. Look at network tab in browser DevTools (if web) or Appium logs
3. Ask your backend team which APIs should be verified

---

## Different Validation Patterns

### Pattern 1: Single Endpoint (Simplest)

```python
with allure.step("Verify session"):
    self.api.assert_endpoint(
        method="GET",
        endpoint="/api/user/me",
        expected_status=200
    )
```

### Pattern 2: Multiple Endpoints (Batch)

```python
with allure.step("Verify all APIs"):
    endpoints = [
        {"method": "GET", "endpoint": "/api/auth/verify", "expected_status": 200},
        {"method": "GET", "endpoint": "/api/user/profile", "expected_status": 200},
        {"method": "GET", "endpoint": "/api/dashboard", "expected_status": 200},
    ]
    assert self.api.validate_endpoints(endpoints)
```

### Pattern 3: With Authentication Headers

```python
with allure.step("Verify authenticated request"):
    self.api.assert_endpoint(
        method="GET",
        endpoint="/api/user/profile",
        expected_status=200,
        headers={
            "Authorization": f"Bearer {your_token}",
            "Content-Type": "application/json"
        }
    )
```

### Pattern 4: POST Request with Data

```python
with allure.step("Verify API accepts POST"):
    self.api.assert_endpoint(
        method="POST",
        endpoint="/api/data/save",
        expected_status=201,
        data={"name": "test", "value": 123}
    )
```

### Pattern 5: Check Results Later

```python
with allure.step("Test multiple endpoints"):
    self.api.validate_endpoint(
        method="GET",
        endpoint="/api/endpoint1",
        expected_status=200
    )
    self.api.validate_endpoint(
        method="GET",
        endpoint="/api/endpoint2",
        expected_status=200
    )

with allure.step("Verify all passed"):
    results = self.api.get_results()
    summary = self.api.get_summary()
    print(f"Passed: {summary['passed']}, Failed: {summary['failed']}")
    assert all(r["status"] == "pass" for r in results)
```

---

## Running Your Modified Test

### Before Modifications (UI Only)
```bash
pytest tests/test_cases/regular_farmer_test_cases/test_login_pytest.py -v
```

### After Modifications (UI + API)
```bash
# Make sure backend is running!
# python -m uvicorn server:app --reload

pytest tests/test_cases/regular_farmer_test_cases/test_login_pytest.py -v
```

### With Allure Report
```bash
pytest tests/test_cases/regular_farmer_test_cases/test_login_pytest.py -v --alluredir=allure-results
allure serve allure-results
```

---

## Troubleshooting

### Error: "APIValidator not found"
- Make sure `tests/utils/api_validator.py` exists
- Make sure you're in the `d:\test-automation-platform` directory
- Check your Python path includes `tests/`

### Error: "Connection refused" on API calls
- Make sure your backend is running: `python -m uvicorn server:app --reload`
- Check the `base_url` parameter points to correct server
- Check firewall isn't blocking the connection

### API returns 404 or 403
- Verify the endpoint path is correct
- Check if authentication is required
- Look at your API documentation

### Test passes UI but fails API
- The UI actions don't match backend state
- API might be slow to update
- Add `time.sleep()` between UI action and API call

---

## Examples for Your Test Files

### For `test_login_pytest.py` (Already shown above)

### For `TestOnboarding.py`

```python
class TestOnboarding:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = APIValidator(base_url="http://localhost:8000")
        yield
    
    def test_onboarding_flow(self, driver):
        # ... UI steps ...
        
        with allure.step("Verify onboarding completed"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/user/onboarding/status",
                expected_status=200
            )
```

### For `login_pytest.py`

Same pattern - add fixture and validation steps.

---

## Quick Checklist

- [ ] Added imports: `from utils.api_validator import APIValidator` and `import pytest`
- [ ] Added setup fixture with `@pytest.fixture(autouse=True)`
- [ ] Added `self.api = APIValidator(base_url="...")`  in setup
- [ ] Identified which APIs to validate
- [ ] Added API validation steps with `self.api.assert_endpoint(...)`
- [ ] Added final summary check: `assert self.api.get_summary()["failed"] == 0`
- [ ] Backend is running when you run tests
- [ ] Tests execute successfully with Allure steps

---

## Ready to Modify?

1. **Open:** `tests/test_cases/regular_farmer_test_cases/test_login_pytest.py`
2. **Add imports** from Step 1
3. **Add fixture** from Step 2
4. **Add API validation** from Step 3
5. **Run test:** `pytest tests/test_cases/regular_farmer_test_cases/test_login_pytest.py -v`

**That's it!** Your test now validates both UI and API! 🎉
