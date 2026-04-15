# API Batch Testing - Complete Implementation

**Status:** ✅ Complete & Production Ready  
**Date:** April 10, 2026

## Overview

A complete API batch testing system has been integrated into the test automation platform, allowing you to:

- ✅ Run API tests from Excel configuration files
- ✅ Test multiple APIs with different HTTP methods
- ✅ Support authentication (Bearer, Basic)
- ✅ Real-time progress tracking via WebSocket
- ✅ Export results to CSV
- ✅ Integrate API tests with UI automation tests

---

## What Was Created

### 1. Backend Module: Excel API Loader (`backend/excel_api_loader.py`)
Handles reading and parsing Excel files with API configurations.

**Features:**
- Reads Excel files with API metadata
- Validates HTTP methods (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- Parses JSON in headers, params, and body columns
- Handles authentication (Bearer, Basic tokens)
- Creates sample Excel templates

**Excel Column Structure:**
```
| API Name | Method | Endpoint | Description | Headers | Params | Body | Expected Status | Auth Type | Auth Token |
|----------|--------|----------|-------------|---------|--------|------|-----------------|-----------|------------|
```

### 2. Backend API Routes (`backend/server.py`)
New FastAPI endpoints for batch testing:

**Endpoints:**
- `POST /api/batch/parse-excel` - Upload and parse Excel file
- `POST /api/batch/run-tests` - Execute batch API tests
- `GET /api/batch/sample-excel` - Download template

### 3. Test Integration Module (`tests/api_test_runner.py`)
Allows running API tests programmatically during test automation.

**Classes:**
- `APITestRunner` - Async API test executor
- Methods: `run_test()`, `run_tests()`, `run_tests_sync()`, `export_results()`

**Functions:**
- `load_apis_from_excel()` - Load configs from Excel
- `run_api_tests()` - Run tests from automation
- `run_api_tests_from_excel()` - Run tests from Excel file
- `run_ui_and_api_tests()` - Combined UI + API testing

### 4. Frontend Component (`frontend/test-platform/src/components/APIBatchTester/`)

**Component: `APIBatchTester.jsx`**
- Upload Excel files
- Preview parsed APIs
- Run batch tests
- View results in real-time
- Export results to CSV

**Pages:**
1. **Upload View** - Upload Excel file, configure base URL and timeout
2. **Preview View** - Preview APIs before testing
3. **Results View** - View test results with statistics

### 5. Frontend Routing
- New route: `/api-batch`
- New sidebar menu item: "API Batch"

---

## Quick Start

### Step 1: Prepare Excel File

Either download the template or create a file with these columns:

| API Name | Method | Endpoint | Expected Status | Auth Type |
|----------|--------|----------|-----------------|-----------|
| Get Users | GET | /api/users | 200 | none |
| Create User | POST | /api/users | 201 | bearer |
| Update User | PUT | /api/users/1 | 200 | none |

### Step 2: Access API Batch Tester

1. Start the test automation platform
2. Go to **API Batch** in the sidebar
3. Click **Download Sample Template** or upload your Excel file

### Step 3: Run Tests

1. Enter the **Base URL** (e.g., `http://localhost:3000`)
2. Adjust **Timeout** if needed (default: 10000ms)
3. Click **Upload API List** and select your Excel file
4. Click **Run Tests** on the preview screen
5. Watch real-time results and logs

### Step 4: Export Results

Click **Export CSV** to save results for analysis

---

## Excel Template Format

### Required Columns
- **API Name:** Descriptive name for the API
- **Method:** HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- **Endpoint:** API path (e.g., `/api/users` or `/api/users/123`)

### Optional Columns
- **Description:** Brief description of the API
- **Headers:** JSON string of custom headers
  ```json
  {"Authorization": "Bearer token", "X-Custom": "value"}
  ```
- **Params:** JSON string of query parameters
  ```json
  {"page": 1, "limit": 10}
  ```
- **Body:** JSON string of request body
  ```json
  {"name": "John", "email": "john@example.com"}
  ```
- **Expected Status:** Comma-separated HTTP status codes (default: 200)
  ```
  200,201
  ```
- **Auth Type:** Authentication method (`none`, `bearer`, `basic`)
- **Auth Token:** Authentication credentials

### Example Excel Data

```
API Name              Method  Endpoint               Expected Status  Auth Type  Auth Token
List All Users       GET     /api/users             200              none
Create User          POST    /api/users             201              none
Get User by ID       GET     /api/users/123         200              none
Update User          PUT     /api/users/123         200              bearer    token_here
Delete User          DELETE  /api/users/123        204              bearer    token_here
Search Users         GET     /api/users?search=john 200             none
Get User Profile     GET     /api/profile           200              bearer    token_here
```

---

## Using with Automation Tests

### Method 1: Run API Tests Only

```python
from tests.api_test_runner import run_api_tests

api_configs = [
    {
        'api_name': 'Get Users',
        'method': 'GET',
        'endpoint': '/api/users',
        'expected_status': [200]
    },
    {
        'api_name': 'Create User',
        'method': 'POST',
        'endpoint': '/api/users',
        'body': {'name': 'John', 'email': 'john@test.com'},
        'expected_status': [201]
    }
]

results = run_api_tests('http://localhost:3000', api_configs, timeout=10000)
```

### Method 2: Run API Tests from Excel

```python
from tests.api_test_runner import run_api_tests_from_excel

results = run_api_tests_from_excel(
    base_url='http://localhost:3000',
    excel_path='api_tests.xlsx',
    timeout=10000
)
```

### Method 3: Run UI + API Tests Together

```python
from tests.test_runner import run_ui_and_api_tests

results = run_ui_and_api_tests(
    app_type='regular_client',
    modules=['login', 'dashboard'],
    base_url='http://localhost:3000',
    api_configs=api_configs,
    api_timeout=10000
)
```

### Method 4: In pytest Test Cases

```python
import pytest
from tests.api_test_runner import APITestRunner

def test_api_and_ui():
    """Test that combines UI and API validation"""
    
    # First, do your UI test
    # ... UI test code ...
    
    # Then validate API endpoints
    runner = APITestRunner('http://localhost:3000')
    api_configs = [
        {
            'api_name': 'Verify User Data',
            'method': 'GET',
            'endpoint': '/api/user/me',
            'expected_status': [200]
        }
    ]
    
    summary = runner.run_tests_sync(api_configs)
    assert summary['failed'] == 0, f"API tests failed: {summary}"
```

---

## API Response Data

### Test Result Structure

```json
{
  "api_name": "Get Users",
  "method": "GET",
  "endpoint": "/api/users",
  "url": "http://localhost:3000/api/users",
  "status": 200,
  "expected_status": [200],
  "passed": true,
  "response": { "data": [...] },
  "duration": 125,
  "timestamp": "2026-04-10T10:30:45.123456"
}
```

### Summary Structure

```json
{
  "total": 10,
  "passed": 9,
  "failed": 1,
  "duration": 1250,
  "results": [...]
}
```

---

## WebSocket Events

The component broadcasts real-time updates via WebSocket:

### Test Start Event
```json
{
  "type": "BATCH_API_TEST",
  "payload": {
    "action": "test_start",
    "total": 10
  }
}
```

### Test Progress Event
```json
{
  "type": "BATCH_API_TEST",
  "payload": {
    "action": "test_progress",
    "index": 5,
    "total": 10,
    "result": { ... }
  }
}
```

### Test Complete Event
```json
{
  "type": "BATCH_API_TEST",
  "payload": {
    "action": "test_complete",
    "summary": { ... }
  }
}
```

---

## Export Format (CSV)

Exported CSV file contains:

| api_name | method | endpoint | status | expected_status | passed | duration | error | timestamp |
|----------|--------|----------|--------|-----------------|--------|----------|-------|-----------|
| Get Users | GET | /api/users | 200 | 200 | YES | 125 | | 2026-04-10T10:30:45 |

---

## Troubleshooting

### Issue: "uvicorn not found" when starting backend

**Solution:** Install missing dependencies
```bash
pip install -r requirements.txt
```

### Issue: Excel file fails to parse

**Solution:** Check that all required columns are present:
- API Name
- Method
- Endpoint

Ensure Method is one of: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS

### Issue: API tests timeout

**Solution:** Increase the timeout value in the UI or in code:
```python
run_api_tests(base_url, api_configs, timeout=30000)  # 30 seconds
```

### Issue: Authentication errors

**Solution:** Ensure auth token is correct and auth type is set:
- `none` - No authentication
- `bearer` - Bearer token authentication (Token: "Bearer {token}")
- `basic` - Basic authentication (Token: base64 encoded "username:password")

---

## Files Created/Modified

### Created Files
- `backend/excel_api_loader.py` - Excel parsing module
- `tests/api_test_runner.py` - API testing integration
- `frontend/test-platform/src/components/APIBatchTester/APIBatchTester.jsx` - React component
- `frontend/test-platform/src/components/APIBatchTester/APIBatchTester.css` - Styling

### Modified Files
- `backend/server.py` - Added batch testing endpoints
- `frontend/test-platform/src/App.jsx` - Added routing
- `frontend/test-platform/src/components/Sidebar/Sidebar.jsx` - Added navigation
- `tests/test_runner.py` - Added API testing functions
- `requirements.txt` - Added dependencies (pandas, openpyxl, fastapi, uvicorn)

---

## Next Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start backend:**
   ```bash
   cd backend
   python -m uvicorn server:app --reload
   ```

3. **Start frontend:**
   ```bash
   cd frontend/test-platform
   npm run dev
   ```

4. **Access the platform:**
   Open http://localhost:5173 and go to **API Batch** section

5. **Download sample template:**
   Click "Download Sample Template" button in the upload view

6. **Create your API test file** based on the template

7. **Run your first batch test!**

---

## Support

For issues or questions about API Batch Testing:
1. Check the logs in the UI
2. Review Excel file format
3. Verify API endpoints are accessible
4. Check authentication credentials

---

**Created:** April 10, 2026  
**Status:** Production Ready ✅
