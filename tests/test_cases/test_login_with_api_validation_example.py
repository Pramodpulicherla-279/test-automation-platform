"""
Example: Real Test Case with API Validation
Modify your existing test_login_pytest.py to include API validation
"""

import time
import allure
import pytest
from utils.api_validator import APIValidator
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@allure.epic("Login Flow")
@allure.feature("Authentication + API Validation")
class TestLoginWithAPIValidation:
    """
    Original login test enhanced with API validation.
    This shows how to integrate API tests into existing UI tests.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup API validator for this test class"""
        self.api = APIValidator(base_url="http://localhost:3000")
        yield
        
        # After test completes, validate API stats
        summary = self.api.get_summary()
        print(f"\nAPI Test Summary: {summary}")
    
    @allure.story("Successful Login with API Validation")
    @allure.title("User login succeeds, session verified via API")
    def test_login_success_with_api_validation(self, driver):
        """
        Enhanced login test that validates:
        1. API endpoints are accessible
        2. UI login works
        3. User session is active via API
        4. User data is consistent between UI and API
        """
        
        # ========================================
        # STEP 1: Verify API is running
        # ========================================
        with allure.step("1. Verify Auth API is accessible"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/auth/health",
                expected_status=200,
                description="Check if authentication service is healthy"
            )
        
        # ========================================
        # STEP 2: UI Login (Your existing code)
        # ========================================
        with allure.step("2. Perform UI login"):
            # Insert your existing UI login code here
            # Example:
            try:
                language_next = driver.find_element(AppiumBy.XPATH, "//button[@text='Next']")
                language_next.click()
                
                # Allow permissions
                # ... your UI code ...
                
                print("✓ UI Login completed")
            except Exception as e:
                pytest.fail(f"UI Login failed: {e}")
        
        # ========================================
        # STEP 3: Verify Session via API
        # ========================================
        with allure.step("3. Verify user session is active"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/user/me",
                expected_status=200,
                description="Verify user session is authenticated"
            )
        
        # ========================================
        # STEP 4: Validate User Data Endpoints
        # ========================================
        with allure.step("4. Validate user profile API"):
            # Validate multiple user-related endpoints
            user_endpoints = [
                {
                    "method": "GET",
                    "endpoint": "/api/user/profile",
                    "expected_status": 200,
                    "description": "Get user profile"
                },
                {
                    "method": "GET",
                    "endpoint": "/api/user/preferences",
                    "expected_status": 200,
                    "description": "Get user preferences"
                },
                {
                    "method": "GET",
                    "endpoint": "/api/user/roles",
                    "expected_status": 200,
                    "description": "Get user roles/permissions"
                }
            ]
            
            assert self.api.validate_endpoints(user_endpoints), "User profile APIs failed"
        
        # ========================================
        # STEP 5: Verify Dashboard Access
        # ========================================
        with allure.step("5. Verify dashboard access"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/dashboard/summary",
                expected_status=200,
                description="Verify access to dashboard data"
            )
        
        # ========================================
        # STEP 6: Report API Results
        # ========================================
        with allure.step("6. Verify all API tests passed"):
            summary = self.api.get_summary()
            
            # Attach results to Allure report
            allure.attach(
                f"API Tests Summary:\n"
                f"  Total: {summary['total']}\n"
                f"  Passed: {summary['passed']}\n"
                f"  Failed: {summary['failed']}\n"
                f"  Success Rate: {summary['success_rate']:.1f}%",
                name="API Validation Results",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Fail test if any API test failed
            assert summary['failed'] == 0, f"API validation failed: {summary['failed']} endpoints"
        
        print(f"\n✓ Login test with API validation passed")
        print(f"✓ API endpoints verified: {self.api.get_summary()['passed']}/{self.api.get_summary()['total']}")


@allure.epic("Dashboard")
@allure.feature("Dashboard + API Validation")
class TestDashboardWithAPIValidation:
    """
    Dashboard test that validates both UI display and API data
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = APIValidator()
        yield
    
    @allure.story("Dashboard loads with correct data")
    @allure.title("Dashboard displays API data correctly")
    def test_dashboard_load_with_api_validation(self, driver):
        """
        Test dashboard loads and verify data comes from API
        """
        
        with allure.step("1. Login to app"):
            # Your UI login code
            print("Logging in...")
        
        with allure.step("2. Navigate to dashboard"):
            # Your UI navigation code
            print("Navigating to dashboard...")
        
        with allure.step("3. Validate dashboard data APIs"):
            dashboard_endpoints = [
                {"method": "GET", "endpoint": "/api/dashboard/stats", "description": "Dashboard statistics"},
                {"method": "GET", "endpoint": "/api/dashboard/activity-log", "description": "Activity log"},
                {"method": "GET", "endpoint": "/api/dashboard/notifications", "description": "Notifications"},
                {"method": "GET", "endpoint": "/api/dashboard/metrics", "description": "Performance metrics"},
            ]
            
            assert self.api.validate_endpoints(dashboard_endpoints), "Dashboard APIs failed"
        
        with allure.step("4. Verify UI displays API data"):
            # Extract data from UI
            print("Verifying UI shows API data...")
            # Your UI data extraction logic
        
        # Success - API data verified
        assert self.api.get_summary()['failed'] == 0


# ========================================
# HOW TO INTEGRATE INTO EXISTING TESTS
# ========================================
"""
To integrate API validation into your existing test_login_pytest.py:

1. Import APIValidator:
   from utils.api_validator import APIValidator

2. Add fixture to your test class:
   @pytest.fixture(autouse=True)
   def setup(self):
       self.api = APIValidator()
       yield

3. Add API validation steps in your test methods:
   with allure.step("Verify API is accessible"):
       self.api.assert_endpoint(
           method="GET",
           endpoint="/api/auth/health",
           expected_status=200
       )

4. After UI actions, validate API endpoints:
   # In an existing test_login_success method
   with allure.step("Verify session via API"):
       self.api.assert_endpoint(
           method="GET",
           endpoint="/api/user/me",
           expected_status=200
       )

5. Check results at end:
   assert self.api.get_summary()["failed"] == 0

That's it! Your test now validates both UI and API behavior.
"""
