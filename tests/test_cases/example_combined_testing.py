"""
Example: Combined UI and API Testing
Shows how to validate both UI and API behavior in the same test
"""

import pytest
import allure
import requests
from utils.api_validator import APIValidator


@allure.epic("Combined Testing")
@allure.feature("UI + API Validation")
class TestLoginWithAPIValidation:
    """
    Example test class showing combined UI and API validation
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup API validator for the test"""
        self.api = APIValidator(base_url="http://localhost:3000")
        yield
        # Log API results after test
        print(f"\nAPI Test Summary: {self.api.get_summary()}")
    
    @allure.story("Login with API validation")
    @allure.title("User login succeeds and API endpoints work")
    def test_login_with_api_validation(self, driver):
        """
        Test UI login flow and validate API endpoints
        
        Steps:
        1. Verify login API is accessible
        2. Perform UI login
        3. Validate user session API
        4. Verify data consistency between UI and API
        """
        
        with allure.step("1. Verify auth API is accessible"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/auth/health",
                expected_status=200,
                description="Check if auth service is running"
            )
        
        with allure.step("2. Perform login on UI"):
            # Your UI login code here
            print("Logging in via UI...")
            # (existing UI test code)
        
        with allure.step("3. Validate user session API"):
            # After login, verify API returns user data
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/user/me",
                expected_status=200,
                description="Verify user session is active"
            )
        
        with allure.step("4. Validate user profile API"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/user/profile",
                expected_status=200,
                description="Fetch user profile"
            )
        
        # Assert all API tests passed
        summary = self.api.get_summary()
        assert summary["failed"] == 0, f"API validation failed: {summary}"
        
        allure.attach(
            f"API Test Results:\n{summary}",
            name="API Summary",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.story("Dashboard with API data")
    @allure.title("Dashboard displays data from API")
    def test_dashboard_with_api_validation(self, driver):
        """
        Test that UI dashboard displays data correctly from API
        """
        with allure.step("1. Load dashboard"):
            print("Loading dashboard on UI...")
            # UI dashboard load
        
        with allure.step("2. Validate dashboard API endpoints"):
            endpoints = [
                {
                    "method": "GET",
                    "endpoint": "/api/dashboard/stats",
                    "expected_status": 200,
                    "description": "Get dashboard statistics"
                },
                {
                    "method": "GET",
                    "endpoint": "/api/dashboard/recent-activities",
                    "expected_status": 200,
                    "description": "Get recent activities"
                },
                {
                    "method": "GET",
                    "endpoint": "/api/dashboard/summary",
                    "expected_status": 200,
                    "description": "Get dashboard summary"
                }
            ]
            
            # Validate all endpoints
            all_passed = self.api.validate_endpoints(endpoints)
            assert all_passed, "Some dashboard APIs failed"
        
        with allure.step("3. Verify data consistency"):
            # Validate that UI displays the data from API
            print("Verifying UI displays API data...")
        
        # Report results
        summary = self.api.get_summary()
        print(f"\n✓ All {summary['passed']} API calls successful")


@allure.epic("Order Management")
@allure.feature("Order with API Validation")
class TestOrderWithAPIValidation:
    """
    Example: Create order via UI and verify via API
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = APIValidator()
        yield
    
    @allure.story("Create and verify order")
    @allure.title("Order created in UI is accessible via API")
    def test_create_order_and_verify_api(self, driver):
        """
        Create order through UI, then verify it via API
        """
        created_order_id = None
        
        with allure.step("1. Create order via UI"):
            print("Creating order through UI...")
            # Your UI order creation code
            created_order_id = "12345"  # Get from UI
        
        with allure.step("2. Verify order via API"):
            # Query API for the created order
            self.api.assert_endpoint(
                method="GET",
                endpoint=f"/api/orders/{created_order_id}",
                expected_status=200,
                description=f"Verify order {created_order_id} exists in API"
            )
        
        with allure.step("3. Validate order details"):
            # Get order details from API
            try:
                response = requests.get(
                    f"http://localhost:3000/api/orders/{created_order_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    order_data = response.json()
                    
                    # Verify order has required fields
                    required_fields = ["id", "status", "created_at", "total"]
                    for field in required_fields:
                        assert field in order_data, f"Missing field: {field}"
                    
                    allure.attach(
                        str(order_data),
                        name="Order Data",
                        attachment_type=allure.attachment_type.JSON
                    )
            except Exception as e:
                pytest.fail(f"Failed to fetch order details: {str(e)}")


# Usage Examples
@pytest.mark.skip(reason="Example only - modify for your API")
def test_example_usage():
    """
    Show how to use APIValidator in tests
    """
    
    # Initialize validator
    api = APIValidator(base_url="http://localhost:3000")
    
    # Single endpoint validation
    api.validate_endpoint(
        method="GET",
        endpoint="/api/users",
        expected_status=200
    )
    
    # Multiple endpoints
    api.validate_endpoints([
        {
            "method": "GET",
            "endpoint": "/api/users",
            "expected_status": 200,
            "description": "List all users"
        },
        {
            "method": "POST",
            "endpoint": "/api/users",
            "expected_status": 201,
            "data": {"name": "Test User", "email": "test@example.com"},
            "description": "Create new user"
        },
    ])
    
    # Get summary
    summary = api.get_summary()
    print(f"Passed: {summary['passed']}/{summary['total']}")
