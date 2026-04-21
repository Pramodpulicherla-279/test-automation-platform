# API Matrix Tester - Backend Integration Guide

## Overview
The API Matrix Tester has been integrated into your FastAPI backend with full CRUD operations, test execution, persistent storage, and real-time WebSocket updates.

## Backend Architecture

### 1. Core Module: `api_matrix.py`
Located at: `backend/api_matrix.py`

#### Models
```python
- Endpoint: HTTP endpoint configuration  
- Environment: Test environment with base URL, auth, headers
- TestResult: Single test execution result
- ExecutionSummary: Batch test statistics
- TestSuite: Named collection of endpoints & environments
```

#### Storage (APIMatrixStorage)
- **File-based storage** in `api_matrix_data/` directory
- `endpoints.json` - List of all endpoints
- `environments.json` - List of all environments  
- `results/` - Individual test results
- `suites/` - Complete test suite definitions

#### Test Executor (APITestExecutor)
- Async HTTP client with configurable timeout
- Supports all HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Authentication: Bearer Token, Basic Auth, API Key
- Response parsing: JSON & raw text
- 8-second timeout per request

### 2. FastAPI Endpoints

#### Endpoints Management
```
GET    /api/matrix/endpoints              - List all endpoints
POST   /api/matrix/endpoints              - Create endpoint
PUT    /api/matrix/endpoints/{id}         - Update endpoint
DELETE /api/matrix/endpoints/{id}         - Delete endpoint
```

#### Environments Management
```
GET    /api/matrix/environments           - List all environments
POST   /api/matrix/environments           - Create environment
PUT    /api/matrix/environments/{id}      - Update environment
DELETE /api/matrix/environments/{id}      - Delete environment
```

#### Test Execution
```
POST   /api/matrix/run-single             - Run single test
       Query params: endpoint_id, env_id
       
POST   /api/matrix/run-all                - Run complete matrix
       Returns: results[], summary{}
```

#### Test Suites
```
GET    /api/matrix/suites                 - List saved suites
POST   /api/matrix/suites                 - Create suite
GET    /api/matrix/suites/{id}            - Get suite details
GET    /api/matrix/suites/{id}/results    - Get execution history
POST   /api/matrix/suites/{id}/run        - Execute suite
```

#### Health
```
GET    /api/matrix/health                 - Get API Matrix status
       Response: {status, endpoints_count, environments_count, suites_count}
```

## Request/Response Examples

### Create Endpoint
```bash
POST /api/matrix/endpoints
Content-Type: application/json

{
  "id": "ep-1",
  "method": "GET",
  "name": "List Users",
  "path": "/api/users",
  "auth": "bearer",
  "body": "",
  "expectedCodes": [200],
  "envIds": ["env-dev", "env-prod"]
}
```

### Create Environment
```bash
POST /api/matrix/environments
Content-Type: application/json

{
  "id": "env-dev",
  "name": "development",
  "baseUrl": "https://api.example.com",
  "color": "cyan",
  "token": "Bearer eyJhbGc...",
  "headers": {"X-API-Version": "2"}
}
```

### Run All Tests
```bash
POST /api/matrix/run-all

Response:
{
  "status": "ok",
  "results": [
    {
      "key": "ep-1::env-dev",
      "pass_": true,
      "status": 200,
      "duration": 245,
      "error": null,
      "url": "https://api.example.com/api/users",
      "body": {...},
      "timestamp": "2026-04-09T10:30:45.123Z",
      "envName": "development",
      "epName": "List Users",
      "method": "GET"
    }
  ],
  "summary": {
    "total": 6,
    "passed": 5,
    "failed": 1,
    "duration": 1500,
    "timestamp": "2026-04-09T10:30:45.123Z"
  }
}
```

## WebSocket Events

The backend broadcasts test updates via WebSocket at `ws://localhost:8000/ws/test-status`:

```javascript
// Test start
{
  type: "API_MATRIX",
  payload: { action: "test_start", endpoint_id, env_id }
}

// Test result
{
  type: "API_MATRIX",
  payload: { action: "test_result", result: {...} }
}

// Batch progress
{
  type: "API_MATRIX",
  payload: { 
    action: "batch_progress",
    progress: 0.5,
    current: 3,
    total: 6,
    result: {...}
  }
}

// Batch complete
{
  type: "API_MATRIX",
  payload: { 
    action: "batch_complete",
    summary: {...}
  }
}

// Suite operations
{
  type: "API_MATRIX",
  payload: { 
    action: "suite_created|suite_updated|suite_deleted",
    suite: {...}
  }
}
```

## Frontend Integration

The React frontend (`src/components/APIMatrixTester/APIMatrixTester.jsx`) automatically:

1. **Loads data from backend on mount**
   ```javascript
   useEffect(() => {
     fetch(`${API_URL}/api/matrix/endpoints`)
     fetch(`${API_URL}/api/matrix/environments`)
   }, [])
   ```

2. **Connects to WebSocket for live updates**
   ```javascript
   const ws = new WebSocket(WS_URL)
   ws.onmessage = (e) => {
     const msg = JSON.parse(e.data)
     if (msg.type === 'API_MATRIX') {
       // Handle test results & progress
     }
   }
   ```

3. **Saves operations to backend**
   - Add endpoint → `POST /api/matrix/endpoints`
   - Add environment → `POST /api/matrix/environments`
   - Run tests → `POST /api/matrix/run-all`
   - Import → Multiple `POST /api/matrix/endpoints`

4. **Config**
   ```javascript
   const API_URL = 'http://localhost:8000'
   const WS_URL = 'ws://localhost:8000/ws/test-status'
   ```

## Data Persistence

All data is automatically saved to disk:

```
test-automation-platform/
├── api_matrix_data/
│   ├── endpoints.json        (5-50 KB)
│   ├── environments.json     (2-10 KB)
│   ├── results/
│   │   ├── suite-id_20260409_101530.json
│   │   └── ...
│   └── suites/
│       ├── suite-1.json
│       └── ...
```

## Usage Examples

### Python/CLI
```python
import requests

API_URL = "http://localhost:8000"

# Create endpoint
endpoint = {
    "id": "ep-1",
    "method": "GET",
    "name": "Users",
    "path": "/users",
    "expectedCodes": [200],
    "envIds": ["env-prod"]
}
r = requests.post(f"{API_URL}/api/matrix/endpoints", json=endpoint)

# Run all tests
r = requests.post(f"{API_URL}/api/matrix/run-all")
results = r.json()

# Check health
r = requests.get(f"{API_URL}/api/matrix/health")
print(r.json())
```

### cURL
```bash
# List endpoints
curl http://localhost:8000/api/matrix/endpoints

# Create endpoint
curl -X POST http://localhost:8000/api/matrix/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "id": "ep-1",
    "method": "GET",
    "name": "Users",
    "path": "/api/users",
    "expectedCodes": [200],
    "envIds": ["env-prod"]
  }'

# Run all tests
curl -X POST http://localhost:8000/api/matrix/run-all

# Get health
curl http://localhost:8000/api/matrix/health
```

## Error Handling

All endpoints return standard HTTP status codes:

```
200 OK              - Success
201 Created         - Resource created
400 Bad Request     - Invalid input
404 Not Found       - Resource not found
500 Internal Error  - Server error
```

Error response format:
```json
{
  "detail": "Error message here"
}
```

## Performance Notes

- **Single test**: ~50-2000ms (depends on API)
- **Batch of 6×3**: ~1-5 seconds for 18 tests
- **WebSocket**: Real-time updates with minimal latency
- **Storage**: <1MB for typical configs, <100MB for large result histories

## Security Considerations

1. **Auth tokens** are stored in plain text in `environments.json`
   - Consider adding encryption in production
   
2. **CORS** enabled for frontend only
   - Update `allow_origins` in `server.py` for production

3. **No rate limiting** on test endpoints
   - Add in production to prevent abuse

## Troubleshooting

### Backend not responding
```bash
# Check if server is running
curl http://localhost:8000/api/matrix/health

# Check logs for errors
# Should see: "Connected to backend API"
```

### WebSocket connection fails
- Ensure backend is running
- Check `API_URL` and `WS_URL` match your setup
- Browser console will show connection error

### Tests timing out
- Increase timeout in `api_matrix.py`: `self.timeout = aiohttp.ClientTimeout(total=15)`
- Check if APIs are actually responding

### Data not persisting
- Check directory: `api_matrix_data/` exists
- Check write permissions
- Check JSON syntax in `.json` files

## Next Steps

1. **Deploy backend** to production server
2. **Add authentication** to backend endpoints
3. **Implement rate limiting** and caching
4. **Add test scheduling** with APScheduler
5. **Create admin dashboard** for data management
6. **Generate test reports** in HTML/PDF format
