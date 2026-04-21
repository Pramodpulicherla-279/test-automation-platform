# Quick Start Guide - Load Testing Dashboard

## 5-Minute Setup

### Step 1: Install k6 (1 min)

**Windows (Recommended - using Chocolatey):**
```bash
choco install k6
```

**Or Manual Install:**
- Download from: https://k6.io/docs/get-started/installation/
- Add k6 to system PATH

Verify:
```bash
k6 version
```

### Step 2: Start Backend (2 min)

```bash
cd d:\test-automation-platform\backend
python server.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 3: Start Frontend (1 min)

In new terminal:
```bash
cd d:\test-automation-platform\frontend\test-platform
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### Step 4: Import Component (1 min)

Update your main app to include the Load Test Dashboard:

```javascript
// src/App.jsx
import LoadTestDashboard from './components/LoadTestDashboard';

export default function App() {
  return (
    <div className="app">
      {/* Your existing components */}
      <LoadTestDashboard />
    </div>
  );
}
```

Or add it to your routing:

```javascript
// src/router/index.js
import LoadTestDashboard from '../components/LoadTestDashboard';

const routes = [
  {
    path: '/load-test',
    component: LoadTestDashboard,
    meta: { title: 'Load Testing' }
  },
  // ... other routes
];
```

## First Test Run

1. **Open Dashboard:** Navigate to `http://localhost:5173/load-test` (or your dashboard route)

2. **Enter Test Name:** e.g., "Active Farms API Test"

3. **Update Token (Important!):**
   - Open `LoadTestDashboard.jsx`
   - Find line with `bearer_token: 'Bearer YOUR_TOKEN'`
   - Replace `YOUR_TOKEN` with your actual API token

4. **Click Start Load Test**

5. **Watch the Magic:**
   - Loading animation appears
   - Real-time metrics stream in
   - Charts populate as requests complete

6. **Review Results:**
   - Summary cards show totals
   - Table shows endpoint metrics
   - Graphs display performance trends

## Understanding the Results

### Key Metrics

| Metric | What It Means | Good Range |
|--------|---------------|-----------|
| **Avg Duration** | Average response time | < 1000ms |
| **P95 Duration** | 95% of requests faster than this | < 2000ms |
| **P99 Duration** | 99% of requests faster than this | < 3000ms |
| **Throughput** | Requests per second | > 10 req/s |
| **Error Rate** | % of failed requests | < 5% |

### Example Result Interpretation

```
Endpoint: active-farms
├─ Requests: 150
├─ Success: 147 (98%)
├─ Failure: 3 (2%)
├─ Avg: 845ms ✅ (< 1000ms)
├─ P95: 1250ms ✅ (< 2000ms)
├─ P99: 1890ms ✅ (< 3000ms)
└─ Throughput: 12.5 req/s ✅ (> 10 req/s)
```

**Status:** ✅ Performance is good!

## Customizing Your Tests

### Add More Endpoints

1. Open `LoadTestDashboard.jsx`
2. Find the `requests` array in `startLoadTest()` function
3. Add new endpoint:

```javascript
{
  method: 'GET',
  url: 'https://api.telangana.krishivaas.in/api/v1/get-active-crops-name?farm_type=current',
  params: { 
    headers: { 'Authorization': 'Bearer YOUR_TOKEN' },
    tags: { name: 'crops-filter' }
  }
}
```

### Adjust Load Profile

Modify the `options` to change VU (Virtual Users) and duration:

```javascript
options: {
  scenarios: {
    default: {
      executor: 'ramping-vus',
      stages: [
        { target: 10, duration: '30s' },  // Ramp to 10 VUs over 30 sec
        { target: 20, duration: '1m' },   // Ramp to 20 VUs over 1 min
        { target: 0, duration: '30s' },   // Ramp down
      ]
    }
  }
}
```

## Storing Configuration

### Save Test Configuration

Create a config file: `backend/api_matrix_data/load_test_configs.json`

```json
{
  "active_farms_test": {
    "name": "Active Farms API Test",
    "bearer_token": "Bearer YOUR_TOKEN",
    "requests": [
      {
        "method": "POST",
        "url": "https://api.telangana.krishivaas.in/api/v1/healthy-stress-farmer-farms-crops?draw=1&start=0&length=20&org_id=4&app_type=state",
        "params": {
          "tags": { "name": "active-farms" }
        }
      }
    ],
    "options": {
      "scenarios": {
        "default": {
          "executor": "ramping-vus",
          "stages": [
            { "target": 5, "duration": "10s" },
            { "target": 5, "duration": "1m" },
            { "target": 0, "duration": "10s" }
          ]
        }
      }
    }
  }
}
```

### Load Configuration in Dashboard

Update `LoadTestDashboard.jsx`:

```javascript
const loadTestConfig = testConfigs[testConfigName];

const config = {
  test_name: testName,
  bearer_token: loadTestConfig.bearer_token,
  requests: loadTestConfig.requests,
  options: loadTestConfig.options
};
```

## Troubleshooting

### "k6 command not found"
```bash
# Windows - verify k6 is in PATH
where k6

# If not found, add k6 installation to PATH:
# Environment Variables > System Variables > Path > Add k6 folder
```

### "WebSocket connection failed"
```bash
# Make sure backend is running
curl http://localhost:8000/api/load-test/list

# If error, restart backend:
cd backend
python server.py
```

### "No charts appearing"
1. Check browser console (F12) for errors
2. Verify npm dependencies: `npm install recharts`
3. Clear cache and reload

### "Test not starting"
1. Check bearer token is valid
2. Verify API endpoints are accessible
3. Check backend server logs

## Checking Test Results Files

Tests are saved automatically:

```
backend/api_matrix_data/load_test_results/
├─ 20240415_120000_metrics.json      (Raw k6 metrics)
└─ 20240415_120000_analysis.json     (Analysis & charts data)
```

View results:
```bash
# List all tests
curl http://localhost:8000/api/load-test/list

# Get specific test details
curl http://localhost:8000/api/load-test/20240415_120000/details
```

## Common Patterns

### Test Peak Hours
```javascript
stages: [
  { target: 50, duration: '5m' },   // Simulate peak
  { target: 50, duration: '10m' },  // Sustain peak
  { target: 0, duration: '2m' }     // Cool down
]
```

### Soak Test (Long Duration)
```javascript
stages: [
  { target: 10, duration: '1m' },
  { target: 10, duration: '1h' },   // Hold for 1 hour
  { target: 0, duration: '1m' }
]
```

### Stress Test (Until Failure)
```javascript
stages: [
  { target: 100, duration: '10m' },
  { target: 200, duration: '10m' },
  { target: 500, duration: '10m' }  // To failure
]
```

## Next Steps

1. ✅ Run your first load test
2. ✅ Review the metrics and understand performance
3. ✅ Create configurations for all critical endpoints
4. ✅ Set up scheduled tests
5. ✅ Create performance baselines
6. ✅ Monitor trends over time

## Pro Tips

💡 **Warm Up:** Run test twice - first to warm up app, second for real metrics  
💡 **Gradual Ramp:** Don't jump to high VUs too quickly - gives better data  
💡 **Think Time:** Keep 1-2 second sleep between requests for realistic load  
💡 **Multiple Runs:** Run tests 3+ times to verify consistency  
💡 **Off-Peak Testing:** Test during low-traffic times for clean results  

## Support Resources

- **k6 Docs:** https://k6.io/docs/
- **API Issues:** Check `backend/server.py` logs
- **Frontend Issues:** Check browser console (F12)

---

**Ready to test?** Let's go! 🚀
