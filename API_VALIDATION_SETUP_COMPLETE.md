# API Test Validation Integration - Complete Setup

**Date:** April 10, 2026  
**Status:** ✅ Complete & Ready to Use

---

## What Was Created

A complete API test validation system that allows your pytest test cases to verify both **UI and API behavior** in the same test execution.

### Files Created

1. **`tests/utils/api_validator.py`** (Core)
   - `APIValidator` class - Main validator for API endpoints
   - Pytest fixtures: `api_validator`, `api_validator_custom`
   - Methods: `validate_endpoint()`, `assert_endpoint()`, `validate_endpoints()`, `get_results()`, `get_summary()`

2. **`tests/test_cases/conftest.py`** (Fixtures)
   - Pytest fixtures for all test cases
   - `api_validator` fixture (auto-inject into tests)
   - `api_endpoints` fixture (common endpoints)
   - Multi-environment support

3. **`tests/test_cases/example_combined_testing.py`** (Examples)
   - `TestLoginWithAPIValidation` - Login + API validation
   - `TestOrderWithAPIValidation` - Order creation + verification
   - Complete examples showing all features

4. **`tests/test_cases/test_login_with_api_validation_example.py`** (Real-world Examples)
   - Enhanced login test with API checks
   - Dashboard test with API validation
   - Practical integration patterns

5. **`API_VALIDATION_GUIDE.md`** (Documentation)
   - Complete usage guide
   - Best practices
   - Common patterns
   - Troubleshooting

---

## Quick Start

### Step 1: Add to Your Test

```python
import pytest
from utils.api_validator import APIValidator

class TestMyFeature:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = APIValidator()
        yield
    
    def test_login_and_verify_api(self, driver):
        # Your existing UI test code here
        ...
        
        # Add API validation
        with allure.step("Verify API"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/user/me",
                expected_status=200
            )
```

### Step 2: Run Your Tests

```bash
pytest tests/test_cases/your_test.py -v
```

---

## Core Features

### Single Endpoint Validation
```python
self.api.validate_endpoint(
    method="GET",
    endpoint="/api/users",
    expected_status=200
)
```

### Multiple Endpoints
```python
endpoints = [
    {"method": "GET", "endpoint": "/api/users", "expected_status": 200},
    {"method": "POST", "endpoint": "/api/users", "expected_status": 201, "data": {...}},
]
assert self.api.validate_endpoints(endpoints)
```

### With Assertion (pytest style)
```python
self.api.assert_endpoint(
    method="GET",
    endpoint="/api/profile",
    expected_status=200,
    description="Get user profile"
)
```

### Get Results
```python
results = self.api.get_results()
summary = self.api.get_summary()
# {total: 10, passed: 9, failed: 1, success_rate: 90.0}
```

---

## Common Integration Patterns

### Pattern 1: Login Test with Session Verification

```python
def test_login_with_session_check(self, driver):
    # UI login
    with allure.step("UI Login"):
        self.login_ui(driver)
    
    # API verification
    with allure.step("Verify session via API"):
        self.api.assert_endpoint(
            method="GET",
            endpoint="/api/user/me",
            expected_status=200
        )
```

### Pattern 2: Create + Verify Pattern

```python
def test_create_and_verify(self, driver):
    item_id = None
    
    with allure.step("Create via UI"):
        item_id = self.create_item_ui(driver)
    
    with allure.step("Verify via API"):
        self.api.assert_endpoint(
            method="GET",
            endpoint=f"/api/items/{item_id}",
            expected_status=200
        )
```

### Pattern 3: Dashboard Data Validation

```python
def test_dashboard_data(self, driver):
    with allure.step("Load dashboard"):
        self.navigate_dashboard(driver)
    
    with allure.step("Validate APIs"):
        endpoints = [
            {"method": "GET", "endpoint": "/api/dashboard/stats"},
            {"method": "GET", "endpoint": "/api/dashboard/activities"},
        ]
        assert self.api.validate_endpoints(endpoints)
```

---

## Existing Test Integration

### For Your Existing `test_login_pytest.py`

**Before:**
```python
def test_login_success(self, driver):
    # Only UI validation
    # Click buttons, enter credentials, verify screen
```

**After:**
```python
def test_login_success(self, driver):
    # UI validation + API verification
    
    with allure.step("Perform UI login"):
        # Your existing UI code
        ...
    
    with allure.step("Verify session via API"):
        self.api.assert_endpoint(
            method="GET",
            endpoint="/api/user/me",
            expected_status=200
        )
```

---

## Fixture Usage

### Option 1: Use Built-in Fixture
```python
def test_something(self, api_validator):
    api_validator.assert_endpoint(...)
```

### Option 2: In-class Fixture
```python
@pytest.fixture(autouse=True)
def setup(self):
    self.api = APIValidator()
    yield

def test_something(self):
    self.api.assert_endpoint(...)
```

### Option 3: Custom Base URL
```python
@pytest.fixture(autouse=True)
def setup(self):
    self.api = APIValidator(base_url="http://custom-api:3000")
    yield
```

---

## What Your Tests Now Support

✅ **UI + API in one test** - Single test verifies both layers  
✅ **Automatic result tracking** - All API calls logged  
✅ **Allure integration** - Results appear in test report  
✅ **Multiple endpoints** - Batch validation  
✅ **Custom headers** - Authentication support  
✅ **Query parameters** - GET query strings  
✅ **POST/PUT data** - JSON body submission  
✅ **Status code validation** - Expected vs actual  
✅ **Error handling** - Timeout and exception handling  
✅ **Result summary** - Pass/fail statistics  

---

## Running Tests

### Single test file
```bash
pytest tests/test_cases/test_login_with_api_validation_example.py -v
```

### All combined tests
```bash
pytest tests/test_cases/example_combined_testing.py -v
```

### With Allure report
```bash
pytest tests/test_cases/ -v --alluredir=allure-results
allure serve allure-results
```

### Specific test
```bash
pytest tests/test_cases/test_login_with_api_validation_example.py::TestLoginWithAPIValidation::test_login_success_with_api_validation -v
```

---

## Example: Enhance Your Existing Test

Here's how to modify your existing `test_login_pytest.py`:

```python
# At top of file, add:
from utils.api_validator import APIValidator
import pytest

# In your test class:
class TestLogin:
    
    # Add this fixture
    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = APIValidator()
        yield
    
    # Modify existing test_login_success
    def test_login_success(self, driver):
        # Your existing UI code...
        
        # Add these API validation steps:
        with allure.step("Verify session via API"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/user/me",
                expected_status=200
            )
        
        with allure.step("Verify user profile"):
            self.api.assert_endpoint(
                method="GET",
                endpoint="/api/user/profile",
                expected_status=200
            )
        
        # Check all APIs passed
        assert self.api.get_summary()["failed"] == 0
```

---

## File Locations

| File | Purpose |
|------|---------|
| `tests/utils/api_validator.py` | Core validator class |
| `tests/test_cases/conftest.py` | Shared fixtures |
| `tests/test_cases/example_combined_testing.py` | Example tests |
| `tests/test_cases/test_login_with_api_validation_example.py` | Real-world examples |
| `API_VALIDATION_GUIDE.md` | Complete documentation |

---

## Next Steps

1. **Review examples** - Check `test_login_with_api_validation_example.py`
2. **Modify existing tests** - Add `APIValidator` to your test classes
3. **Define API endpoints** - List the APIs you want to validate
4. **Run tests** - Execute with pytest
5. **View reports** - Check Allure reports for results

---

## Features Summary

| Feature | Description | Example |
|---------|-------------|---------|
| Single validation | Test one endpoint | `validate_endpoint()` |
| Batch validation | Test multiple endpoints | `validate_endpoints([...])` |
| Assertions | Pytest-style assertions | `assert_endpoint()` |
| Results | Get all test results | `get_results()` |
| Summary | Statistics | `get_summary()` |
| Custom headers | Auth support | `headers={"Authorization": "..."}` |
| Query params | GET parameters | `params={"page": 1}` |
| POST data | Request body | `data={...}` |
| Timeout | Custom timeout | `APIValidator(timeout=30)` |
| Multi-env | Multiple endpoints | Parametrized fixtures |

---

## Benefits

✨ **Comprehensive Testing** - Validate entire feature (UI + API)  
✨ **Early Bug Detection** - Catch API issues before release  
✨ **Data Consistency** - Ensure UI matches backend data  
✨ **Regression Prevention** - API changes caught by tests  
✨ **Better Reports** - Allure shows complete test coverage  
✨ **Maintainability** - Reusable validators across tests  

---

**You're all set!** Start integrating API validation into your tests! 🚀

For detailed documentation, see: [API_VALIDATION_GUIDE.md](API_VALIDATION_GUIDE.md)
