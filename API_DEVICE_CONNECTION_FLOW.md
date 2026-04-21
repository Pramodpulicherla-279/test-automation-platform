# API Results Flow - Matrix Connected to Device

## Complete Architecture

Your automation now captures **real API responses from the device** and sends them to the matrix API backend.

---

## How It Works

### 1. **Device Makes API Calls** 
```python
# In your pytest test (test_login_pytest.py)
with allure.step("9. Verify session via API"):
    self.api.assert_endpoint(
        method="GET",
        endpoint="/api/auth/verify",
        expected_status=200
    )
```

### 2. **APIValidator Captures Response**
The `APIValidator` class (enhanced) now captures:
- ✅ Actual HTTP status code from device
- ✅ Full response body (JSON or text)
- ✅ Request/response headers
- ✅ Response time (duration_ms)
- ✅ URL called
- ✅ Any errors or timeouts

```python
# From tests/utils/api_validator.py
result = {
    "endpoint": "/api/auth/verify",
    "method": "GET",
    "actual_status": 200,
    "expected_status": 200,
    "passed": True,
    "response_body": {"user": "farmer", "authenticated": true},
    "response_headers": {...},
    "duration_ms": 45,
    "timestamp": "2026-04-10T14:22:33.123Z",
    "url": "http://localhost:8000/api/auth/verify"
}
```

### 3. **Pytest Plugin Collects Results**
After each test, the pytest hook automatically collects all API results:

```python
# From conftest.py - pytest_runtest_teardown()
for response in validator.captured_responses:
    response['test_name'] = 'test_login_success'
    response['test_file'] = 'test_login_pytest.py'
    _api_results_session.append(response)
```

### 4. **Results Saved When Tests Complete**
When all pytest tests finish, the hook saves to JSON:

```python
# pytest_sessionfinish() writes to:
# tests/.api_results_captured.json

{
    "timestamp": "2026-04-10T14:22:45.000Z",
    "total_results": 15,
    "results": [
        {
            "endpoint": "/api/auth/verify",
            "method": "GET",
            "actual_status": 200,
            "expected_status": 200,
            "passed": true,
            "response_body": {...actual response...},
            "test_name": "test_login_success",
            "test_file": "test_login_pytest.py"
        },
        ... more results ...
    ]
}
```

### 5. **Test Runner Reads Results**
After pytest completes, test_runner reads the captured file:

```python
# From test_runner.py - run_tests_and_get_suggestions()
api_results = extract_api_validator_results(project_root)
# Reads: tests/.api_results_captured.json
```

### 6. **Send to Matrix API**
All results sent to your matrix backend:

```python
# POST /api/matrix/automation-results
response = requests.post(
    "http://localhost:8000/api/matrix/automation-results",
    json=api_results,  # Full captured responses with actual device data
    timeout=10
)
```

### 7. **Matrix Stores Results**
Backend stores in "automation_results" suite:

```python
# From backend/server.py
storage.save_result(
    suite_id="automation_results",
    test_result={
        "endpoint": "/api/auth/verify",
        "status": 200,
        "response_body": {...},
        "passed": true
    }
)
```

---

## Files Changed

| File | Change |
|------|--------|
| `tests/utils/api_validator.py` | **Enhanced** - Now captures full response data, headers, duration |
| `tests/conftest.py` | **Added** - Pytest hooks to collect API results from fixtures |
| `tests/test_runner.py` | **Updated** - Reads captured results and sends to matrix API |
| `backend/server.py` | **Added** - `/api/matrix/automation-results` endpoint to store results |

---

## Data Captured Per API Call

```json
{
    "endpoint": "/api/auth/verify",
    "method": "GET",
    "actual_status": 200,
    "expected_status": 200,
    "passed": true,
    "description": "Verify user session is active after login",
    
    "response_body": {
        "user_id": "12345",
        "phone": "7660852538",
        "authenticated": true,
        "roles": ["farmer"]
    },
    
    "response_headers": {
        "content-type": "application/json",
        "server": "uvicorn"
    },
    
    "response_size": 156,
    "duration_ms": 45,
    "timestamp": "2026-04-10T14:22:33.123Z",
    "url": "http://localhost:8000/api/auth/verify",
    
    "test_name": "test_login_success",
    "test_file": "test_login_pytest.py"
}
```

---

## Complete Flow (End-to-End)

```
┌─────────────────────────────────────────────────────────┐
│ 1. User runs: pytest tests/test_cases/.../test_login_pytest.py --apk=app.apk
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ 2. Test runs with UI + API validation steps             │
│    - Step 1-8: UI interactions (login flow)             │
│    - Step 9-11: API validation                          │
│                                                          │
│    APIValidator captures:                               │
│    - HTTP status from device                            │
│    - Full response body (JSON)                          │
│    - Response headers                                   │
│    - Duration, timestamp                                │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ 3. pytest finishes                                      │
│    - pytest_runtest_teardown() collects each test's API│
│    - pytest_sessionfinish() saves all to .json file    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ 4. test_runner reads results                            │
│    - extract_api_validator_results() reads .json file  │
│    - Parses all captured API responses from device     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ 5. test_runner sends to matrix backend                 │
│    - POST /api/matrix/automation-results               │
│    - Sends full captured responses with device data    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ 6. Matrix API stores results                            │
│    - Creates/updates "automation_results" suite        │
│    - Stores each API response with full data           │
│    - Calculates summary (pass/fail)                    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ 7. Results visible in API Matrix dashboard             │
│    - See actual responses from device                  │
│    - View timing, status codes, response bodies        │
│    - Analyze full test execution traces                │
└─────────────────────────────────────────────────────────┘
```

---

## What You'll See in Matrix API

When you check the matrix backend, the "automation_results" suite will show:

```
Suite: Automation API Results
├─ Total Tests: 15
├─ Passed: 14
├─ Failed: 1
│
├─ Result 1: GET /api/auth/verify
│  Status: 200 ✓
│  Response: {"authenticated": true}
│  Duration: 45ms
│
├─ Result 2: GET /api/user/profile
│  Status: 200 ✓
│  Response: {"user": "farmer", "phone": "7660852538"}
│  Duration: 52ms
│
├─ Result 3: POST /api/data/save
│  Status: 201 ✓
│  Response: {"id": "123", "saved": true}
│  Duration: 89ms
│
└─ ... more results
```

---

## Testing It

### Option 1: Run Complete Flow
```bash
# 1. Start backend
cd backend
python -m uvicorn server:app --reload

# 2. In another terminal, run tests
cd tests
pytest tests/test_cases/regular_farmer_test_cases/test_login_pytest.py --apk=/path/to/app.apk -v

# 3. Results automatically sent to matrix
# Check matrix API dashboard → Automation API Results suite
```

### Option 2: Manual Test
```python
# Quick test of the flow
from tests.utils.api_validator import APIValidator

validator = APIValidator(base_url="http://localhost:8000")

# Simulate API calls
validator.validate_endpoint(
    method="GET",
    endpoint="/api/auth/verify",
    expected_status=200,
    description="Test session verification"
)

validator.validate_endpoint(
    method="GET", 
    endpoint="/api/user/profile",
    expected_status=200,
    description="Test profile access"
)

# Send to matrix
validator.send_results_to_matrix()

# Check matrix backend for results
```

---

## Key Benefits

✅ **Real Device Data** - Actual API responses from the device  
✅ **Full Response Capture** - Headers, body, status, timing  
✅ **Automatic Collection** - Pytest hooks capture without manual code  
✅ **Persistent Storage** - All results in matrix API database  
✅ **Test Context** - Know which test made each API call  
✅ **Timing Analysis** - See API performance per call  
✅ **Error Details** - Full error messages if something fails  

---

## Next Steps

1. **Run your modified test file** with the new APIValidator
2. **Check the matrix dashboard** for "Automation API Results" suite
3. **Verify API responses** match expectations
4. **Monitor performance** with timing data
5. **Track failures** with full error details

**Everything is now connected!** 🚀
