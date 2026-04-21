# Load Testing & Performance Monitoring Integration Guide

## Overview

This guide walks you through integrating the new Load Testing and Performance Monitoring system into your API Matrix test platform. This system provides:

- ✅ Real-time load testing with k6
- ✅ Live performance metrics visualization
- ✅ Loading animations during test runs
- ✅ Comprehensive performance graphs (line, bar, heatmap)
- ✅ Historical test result tracking
- ✅ WebSocket-based real-time metric streaming

## What's Been Added

### Backend Components

#### 1. **load_test_runner.py**
Orchestrates k6 load tests and collects metrics
- `K6LoadTestRunner` class: Executes k6 tests, parses results
- Creates dynamic k6 scripts from your test configuration
- Stores test results in `backend/api_matrix_data/load_test_results/`

#### 2. **performance_collector.py**
Analyzes performance data and generates analytics
- `PerformanceDataCollector` class: Tracks metrics, calculates statistics
- Generates timeline data, heatmaps, throughput analysis
- Computes percentiles (p95, p99), distribution histograms

#### 3. **server.py Updates**
New FastAPI endpoints for load testing:
```
POST   /api/load-test/start               - Start a load test
POST   /api/load-test/metrics             - Record a metric
GET    /api/load-test/{test_id}/summary   - Get test summary
GET    /api/load-test/{test_id}/details   - Get detailed results
GET    /api/load-test/list                - List all tests
WS     /ws/load-test/{test_id}            - Real-time metrics stream
```

### Frontend Components

#### LoadTestDashboard.jsx
React component with:
- Test control panel
- Loading animation during test execution
- Real-time performance charts
- Metrics summary cards
- Endpoint comparison table
- Response time distribution histograms

## Prerequisites

### 1. Install k6
k6 needs to be installed separately on your system.

**Windows (using Chocolatey):**
```bash
choco install k6
```

**Or download from:** https://k6.io/docs/get-started/installation/

Verify installation:
```bash
k6 version
```

### 2. Install Python Dependencies
The performance monitoring modules are already in the backend. Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Setup Instructions

### Step 1: Prepare Your Test Configuration

You need a k6-compatible test configuration. Here's the structure your tests should follow:

```javascript
export const options = {
  scenarios: {
    Scenario_1: {
      executor: 'ramping-vus',
      gracefulStop: '30s',
      stages: [
        { target: 1, duration: '10s' },
        { target: 1, duration: '1m' },
        { target: 0, duration: '10s' },
      ],
      exec: 'scenario_1',
    },
  },
};

const bearerToken = 'Bearer YOUR_TOKEN_HERE';

// Define your requests with tags for identification
const requests = [
  {
    method: 'POST',
    url: 'https://api.example.com/endpoint',
    body: null,
    params: {
      headers: { Authorization: bearerToken },
      tags: { name: 'endpoint-name' }
    },
  },
  // ... more requests
];

export function scenario_1() {
  let responses = http.batch(requests);
  sleep(1);
}
```

### Step 2: Start the Backend

From the `d:\test-automation-platform` directory:

```bash
cd backend
python server.py
```

The server will start on `http://localhost:8000`

### Step 3: Start the Frontend

In another terminal:

```bash
cd frontend/test-platform
npm install
npm run dev
```

Frontend will run on `http://localhost:5173` (or similar)

### Step 4: Access the Load Test Dashboard

1. Open your frontend application
2. Navigate to the Load Test Dashboard component
3. Enter your test name
4. Click "Start Load Test"

## Usage Example

### Via Frontend UI

1. **Prepare Test Configuration:** Have your k6 script ready with Bearer token and endpoints
2. **Enter Test Name:** e.g., "Active Farms API Load Test"
3. **Start Test:** Click the button - loading animation appears
4. **View Real-time Metrics:** Charts update as requests complete
5. **Review Results:** Summary stats and detailed endpoint breakdown shown

### Via API

```bash
# Start a load test
curl -X POST http://localhost:8000/api/load-test/start \
  -H "Content-Type: application/json" \
  -d '{
    "test_name": "Active Farms Test",
    "bearer_token": "Bearer YOUR_TOKEN",
    "requests": [
      {
        "method": "POST",
        "url": "https://api.telangana.krishivaas.in/api/v1/healthy-stress-farmer-farms-crops",
        "body": null,
        "params": {
          "headers": {"Authorization": "Bearer YOUR_TOKEN"},
          "tags": {"name": "active-farms"}
        }
      }
    ],
    "options": {
      "scenarios": {
        "default": {
          "executor": "ramping-vus",
          "stages": [
            {"target": 5, "duration": "10s"},
            {"target": 5, "duration": "30s"},
            {"target": 0, "duration": "10s"}
          ]
        }
      }
    }
  }'

# Get test summary
curl http://localhost:8000/api/load-test/20240415_120000/summary

# List all tests
curl http://localhost:8000/api/load-test/list
```

## Performance Metrics Explained

### Summary Metrics
- **Total Requests:** All HTTP requests executed
- **Successful:** Requests with expected status codes
- **Failed:** Requests with unexpected status codes
- **Avg Duration:** Average response time

### Endpoint Metrics
| Metric | Description |
|--------|-------------|
| Requests | Total API calls to this endpoint |
| Success | Calls with expected status code |
| Error Rate | % of failed requests |
| Avg (ms) | Average response time |
| P95 (ms) | 95th percentile response time |
| P99 (ms) | 99th percentile response time |
| Throughput | Requests per second |

### Graphs

1. **Response Time Trend:** Shows how response times change over the test duration
2. **Endpoint Comparison:** Bar chart comparing avg, P95, P99 across endpoints
3. **Throughput:** Requests/second for each endpoint
4. **Error Rate:** Percentage of failed requests per endpoint
5. **Distribution:** Histogram of response time ranges

## Advanced Configuration

### Custom Scenarios

Modify the test options to customize:

```javascript
{
  scenarios: {
    custom_load: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
      env: { MY_VAR: 'value' }
    }
  },
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2500']
  }
}
```

### Performance Thresholds

Define success criteria:
```javascript
thresholds: {
  http_req_duration: ['p(95)<500', 'p(99)<1000'],
  http_req_failed: ['rate<0.1']  // Less than 10% error rate
}
```

## Troubleshooting

### k6 Command Not Found

**Solution:** Ensure k6 is installed and in your system PATH
```bash
# Verify installation
k6 version

# If not in PATH, add k6 installation directory to PATH environment variable
```

### WebSocket Connection Failed

**Solution:** 
- Ensure backend is running on `http://localhost:8000`
- Check browser console for connection errors
- Verify CORS settings in `backend/server.py`

### Tests Not Running

**Solution:**
- Verify bearer token is valid
- Check API endpoints are accessible
- Review k6 script syntax
- Check backend logs for errors

### Charts Not Displaying

**Solution:**
- Ensure Recharts is installed: `npm install recharts`
- Check browser console for errors
- Verify metric data is being collected

## Integration with Existing Tests

### Convert Existing k6 Tests

If you have existing k6 scripts, convert them:

```javascript
// Before: Run with k6 CLI directly
// k6 run script.js

// After: Use with Load Test Dashboard
const requests = [
  {
    method: 'POST',
    url: 'https://api.example.com/endpoint',
    params: {
      headers: { Authorization: bearerToken },
      tags: { name: 'endpoint-name' }  // IMPORTANT: Add tags
    }
  }
];
```

### Key Requirements for Load Test Integration

1. ✅ Add `tags: { name: 'endpoint-name' }` to identify endpoints
2. ✅ Use Bearer token in headers
3. ✅ Include `scenarios` in options
4. ✅ Define VU stages and durations

## API Matrix Integration

To use load testing within your API Matrix:

1. **Create Load Test Suite:** Add load test type to API configuration
2. **Store k6 Scripts:** Save scripts in `backend/api_matrix_data/load_tests/`
3. **Schedule Tests:** Use existing test scheduler for load tests
4. **Compare Results:** Track performance metrics across test runs

Example API Matrix entry:
```json
{
  "id": "load_test_1",
  "name": "Active Farms Load Test",
  "type": "load-test",
  "script_path": "api_matrix_data/load_tests/active_farms.js",
  "config": {
    "load_profile": "ramping-vus",
    "duration": "2m",
    "target_vus": 20
  }
}
```

## Performance Tips

### Optimize Test Execution

1. **Use Appropriate VU Counts:** Start low (5-10) and scale up gradually
2. **Regular Baselines:** Run tests regularly to track trends
3. **Isolate Endpoints:** Test endpoints separately for clear metrics
4. **Monitor Resources:** Watch server-side CPU/Memory during tests

### Reduce Load on API

1. Set reasonable request durations
2. Use think time (sleep) between requests
3. Stagger test scenarios if testing multiple endpoints
4. Run during off-peak hours for production APIs

## Exporting Results

Results are automatically exported to JSON:
```
backend/api_matrix_data/load_test_results/{test_id}_analysis.json
```

Contents include:
- Summary statistics
- Timeline data (all requests)
- Heatmap data (status codes)
- Throughput over time
- Response time distribution

## Next Steps

1. **Configure Your First Test:** Prepare your k6 script with your API endpoints
2. **Run Dashboard:** Start backend and frontend
3. **Execute Load Test:** Use the UI to run your first test
4. **Review Results:** Analyze the comprehensive metrics and charts
5. **Iterate:** Refine test configurations and performance thresholds

## Support & Resources

- **k6 Documentation:** https://k6.io/docs/
- **Backend API:** Check `backend/server.py` for endpoint details
- **Frontend Component:** See `frontend/test-platform/src/components/LoadTestDashboard.jsx`

---

**Last Updated:** April 15, 2026
**Version:** 1.0
