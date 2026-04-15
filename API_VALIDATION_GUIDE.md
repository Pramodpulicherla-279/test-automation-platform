# API Test Validation Integration Guide

**Date:** April 10, 2026  
**Status:** ✅ Complete

---

## Overview

API validation utilities allow your pytest test cases to verify both UI and API behavior in the same test. This ensures data consistency between the UI layer and backend APIs.

## Quick Start

### 1. Import the Validator

```python
from utils.api_validator import APIValidator
```

### 2. Create Fixture in Your Test Class

```python
@pytest.fixture(autouse=True)
def setup(self):
    self.api = APIValidator(base_url="http://localhost:3000")
    yield
```

### 3. Use in Your Test

```python
def test_login_with_api(self, driver):
    with allure.step("Verify API is accessible"):
        self.api.assert_endpoint(
            method="GET",
            endpoint="/api/auth/health",
            expected_status=200
        )
```

---

## APIValidator Methods

### `validate_endpoint()`
Validates a single API endpoint without raising exceptions.

```python
passed = self.api.validate_endpoint(
    method="GET",
    endpoint="/api/users",
    expected_status=200,
    description="Fetch all users"
)

if passed:
    print("API call successful")
```

### `assert_endpoint()`
Validates endpoint and raises AssertionError if it fails (good for pytest).

```python
self.api.assert_endpoint(
    method="POST",
    endpoint="/api/users",
    expected_status=201,
    data={"name": "John", "email": "john@example.com"},
    description="Create new user"
)
```

### `validate_endpoints()`
Validates multiple endpoints at once.

```python
endpoints = [
    {
        "method": "GET",
        "endpoint": "/api/users",
        "expected_status": 200,
        "description": "List users"
    },
    {
        "method": "GET",
        "endpoint": "/api/profile",
        "expected_status": 200,
        "description": "Get profile"
    }
]

all_passed = self.api.validate_endpoints(endpoints)
assert all_passed, "API validation failed"
```

### `get_results()`
Get all API test results.

```python
results = self.api.get_results()
for result in results:
    print(f"{result['method']} {result['endpoint']}: {result['status']}")
```

### `get_summary()`
Get summary statistics.

```python
summary = self.api.get_summary()
print(f"Passed: {summary['passed']}/{summary['total']}")
print(f"Success rate: {summary['success_rate']}%")
```

---

## Integration Examples

### Example 1: Login Test with API Validation

```python
@allure.epic("Authentication")
class TestLoginWithAPI:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = APIValidator()
        yield
    
    def test_login_success(self, driver):
        with allure.step("1. Verify auth endpoint"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/auth/status",
                expected_status=200
            )
        
        with allure.step("2. Perform UI login"):
            # Your UI login code here
            username = "test@example.com"
            password = "password123"
            # ... click login button, enter credentials, etc
        
        with allure.step("3. Verify session via API"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/user/me",
                expected_status=200,
                description="Verify user session"
            )
        
        # Ensure all API tests passed
        assert self.api.get_summary()["failed"] == 0
```

### Example 2: Dashboard Test with Data Validation

```python
def test_dashboard_loads_api_data(self, driver):
    
    with allure.step("Load dashboard"):
        # UI code to load dashboard
        pass
    
    with allure.step("Validate dashboard data APIs"):
        endpoints = [
            {"method": "GET", "endpoint": "/api/dashboard/stats"},
            {"method": "GET", "endpoint": "/api/dashboard/activities"},
            {"method": "GET", "endpoint": "/api/dashboard/notifications"}
        ]
        
        assert self.api.validate_endpoints(endpoints)
```

### Example 3: Create and Verify via API

```python
def test_create_item_via_ui_verify_via_api(self, driver):
    item_id = None
    
    with allure.step("Create item via UI"):
        # UI code to create item
        item_id = "12345"
    
    with allure.step("Verify item exists in API"):
        self.api.assert_endpoint(
            method="GET",
            endpoint=f"/api/items/{item_id}",
            expected_status=200,
            description=f"Verify item {item_id} in backend"
        )
```

### Example 4: POST Request with Data

```python
def test_create_user_api(self, driver):
    
    with allure.step("Create user via API"):
        self.api.assert_endpoint(
            method="POST",
            endpoint="/api/users",
            expected_status=201,
            data={
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890"
            },
            headers={"Content-Type": "application/json"},
            description="Create new user account"
        )
```

### Example 5: Query Parameters

```python
def test_search_with_params(self, driver):
    
    with allure.step("Search users"):
        self.api.assert_endpoint(
            method="GET",
            endpoint="/api/users/search",
            expected_status=200,
            params={
                "query": "john",
                "page": 1,
                "limit": 10
            },
            description="Search for users containing 'john'"
        )
```

---

## Best Practices

### 1. Always Use Fixtures
```python
@pytest.fixture(autouse=True)
def setup(self):
    self.api = APIValidator()
    yield
```

### 2. Use Descriptive Descriptions
```python
self.api.assert_endpoint(
    method="GET",
    endpoint="/api/users",
    expected_status=200,
    description="Fetch all active users"  # Clear description
)
```

### 3. Validate Multiple Endpoints
```python
# Good: Multiple endpoints in one validation
self.api.validate_endpoints([...])

# Instead of: Multiple individual calls
self.api.validate_endpoint(...)
self.api.validate_endpoint(...)
self.api.validate_endpoint(...)
```

### 4. Check Summary at End
```python
def teardown_method(self):
    summary = self.api.get_summary()
    assert summary["failed"] == 0, f"Failed {summary['failed']} API tests"
```

### 5. Log Results to Allure
```python
with allure.step("API Validations"):
    self.api.validate_endpoints(endpoints)
    
summary = self.api.get_summary()
allure.attach(
    json.dumps(summary),
    name="API Test Summary",
    attachment_type=allure.attachment_type.JSON
)
```

---

## Common Patterns

### Pattern 1: UI Action + API Verification

```python
def test_user_profile_update(self, driver):
    with allure.step("1. Update profile via UI"):
        # Click edit, change name, save
        pass
    
    with allure.step("2. Verify changes via API"):
        self.api.assert_endpoint(
            method="GET",
            endpoint="/api/user/profile",
            expected_status=200
        )
```

### Pattern 2: Pre-condition via API + UI Test

```python
def test_order_cancellation(self, driver):
    order_id = None
    
    with allure.step("1. Create order via API"):
        self.api.assert_endpoint(
            method="POST",
            endpoint="/api/orders",
            expected_status=201,
            data={"items": [...]}
        )
        # Extract order_id from response
    
    with allure.step("2. Cancel via UI"):
        # Click cancel button
        pass
    
    with allure.step("3. Verify cancellation via API"):
        self.api.assert_endpoint(
            method="GET",
            endpoint=f"/api/orders/{order_id}",
            expected_status=200
        )
```

### Pattern 3: Data Consistency Check

```python
def test_data_consistency(self, driver):
    ui_data = {}
    
    with allure.step("1. Extract UI data"):
        ui_data = scrape_ui_data_from_screen()
    
    with allure.step("2. Fetch API data"):
        response = requests.get("/api/items/123")
        api_data = response.json()
    
    with allure.step("3. Compare"):
        assert ui_data["name"] == api_data["name"]
        assert ui_data["status"] == api_data["status"]
```

---

## Environment Configuration

### Using Different Base URLs

```python
# Development
api = APIValidator(base_url="http://localhost:3000")

# Staging
api = APIValidator(base_url="https://staging-api.example.com")

# Production
api = APIValidator(base_url="https://api.example.com")
```

### With Custom Timeout

```python
api = APIValidator(
    base_url="http://localhost:3000",
    timeout=30  # 30 seconds
)
```

---

## Running Your Tests

### Single Test with API Validation
```bash
pytest tests/test_cases/test_login_with_api.py::TestLoginWithAPI::test_login_success -v --allure-features="UI + API"
```

### All Combined Tests
```bash
pytest tests/test_cases/example_combined_testing.py -v
```

### Generate Allure Report
```bash
pytest tests/test_cases/ -v --alluredir=allure-results
allure serve allure-results
```

---

## Troubleshooting

### Issue: API returns 404
- Verify endpoint path is correct
- Check base_url is accessible
- Ensure API server is running

### Issue: API returns 500
- Check backend logs
- Verify request data format
- Ensure required fields are provided

### Issue: Test hangs on API call
- Increase timeout: `timeout=60`
- Check network connectivity
- Review API response time

### Issue: CORS errors
- Configure API CORS headers
- Or run tests on same origin
- Or use proxy in test environment

---

## File Locations

- **Validator:** `tests/utils/api_validator.py`
- **Example Tests:** `tests/test_cases/example_combined_testing.py`
- **Import:** `from utils.api_validator import APIValidator`

---

## Features

✅ Single and batch endpoint validation  
✅ Pytest integration with fixtures  
✅ Allure report integration  
✅ Automatic result tracking  
✅ Summary statistics  
✅ Custom headers and authentication  
✅ Query parameters support  
✅ JSON data body support  
✅ Timeout handling  
✅ Error logging  

---

**Ready to use!** Add API validation to your test cases now! 🚀
