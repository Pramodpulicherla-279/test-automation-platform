# Load Testing & Performance Monitoring System

## Overview

A comprehensive, real-time load testing and performance monitoring system for your API Matrix platform. Run load tests with k6, visualize metrics in real-time, and analyze performance data through an interactive web dashboard with professional charts and animations.

## 🎯 Features

- ⚡ **Real-time Metric Streaming** via WebSocket
- 📊 **Interactive Charts** (Line, Bar, Histogram, Heatmap)
- 🎬 **Loading Animation** during test execution
- 📈 **Comprehensive Analytics** (percentiles, throughput, error rates)
- 🔄 **Async Execution** (non-blocking test runs)
- 💾 **Result Persistence** (all tests saved)
- 🎨 **Responsive UI** (desktop, tablet, mobile)
- 🔌 **REST & WebSocket APIs**
- 📋 **Test History** tracking
- 🏗️ **Production-ready** architecture

## 📁 Project Structure

```
test-automation-platform/
├─ backend/
│  ├─ load_test_runner.py           (k6 orchestration)
│  ├─ performance_collector.py       (metrics analysis)
│  ├─ server.py                      (FastAPI endpoints)
│  └─ api_matrix_data/
│     ├─ load_tests/
│     │  └─ active_farms_load_test.js (example script)
│     ├─ load_test_configs.json      (test configurations)
│     └─ load_test_results/          (test outputs)
│
├─ frontend/test-platform/
│  └─ src/components/
│     ├─ LoadTestDashboard.jsx       (main component)
│     └─ LoadTestDashboard.css       (styling)
│
├─ LOAD_TESTING_QUICK_START.md       (5-min setup)
├─ LOAD_TESTING_INTEGRATION_GUIDE.md (detailed guide)
└─ LOAD_TESTING_IMPLEMENTATION_SUMMARY.md (overview)
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **k6** (install: `choco install k6` or see https://k6.io/docs/get-started/installation/)

### 1. Install k6

```bash
# Windows (Chocolatey)
choco install k6

# Verify
k6 version
```

### 2. Start Backend

```bash
cd backend
python server.py
# Server running on http://localhost:8000
```

### 3. Start Frontend

```bash
cd frontend/test-platform
npm install      # if not done
npm run dev
# Frontend running on http://localhost:5173
```

### 4. Import Component

```javascript
// In your main app or routing file
import LoadTestDashboard from './components/LoadTestDashboard';

// Add to your routes or render directly
<LoadTestDashboard />
```

### 5. Run Your First Test

1. Navigate to the Load Test Dashboard
2. Enter a test name
3. Update the bearer token (in component code)
4. Click "Start Load Test"
5. Watch real-time metrics
6. Review results

## 📊 What You Get

### During Test (Live)
- ✅ Loading animation
- ✅ Request counter
- ✅ Status updates
- ✅ Real-time metric stream

### After Test (Results Dashboard)
- ✅ Summary statistics
- ✅ Endpoint details table
- ✅ Response time trend chart
- ✅ Endpoint comparison chart
- ✅ Throughput analysis
- ✅ Error rate breakdown
- ✅ Response time distribution histogram

### Metrics Provided
| Metric | Description |
|--------|-------------|
| Total Requests | All HTTP calls executed |
| Success Rate | % of requests with expected status |
| Error Rate | % of failed requests |
| Avg Duration | Average response time |
| Median Duration | 50th percentile |
| P95 Duration | 95th percentile response time |
| P99 Duration | 99th percentile response time |
| Throughput | Requests per second |
| Status Codes | Distribution by response code |

## 🔌 API Endpoints

### Start Load Test
```http
POST /api/load-test/start
Content-Type: application/json

{
  "test_name": "Active Farms Test",
  "bearer_token": "Bearer YOUR_TOKEN",
  "requests": [...],
  "options": {...}
}
```

### Get Test Summary
```http
GET /api/load-test/{test_id}/summary
```

### List All Tests
```http
GET /api/load-test/list
```

### Record Metric
```http
POST /api/load-test/metrics
Content-Type: application/json

{
  "endpoint": "active-farms",
  "duration_ms": 1234,
  "status_code": 200,
  "success": true
}
```

### WebSocket (Real-time)
```
WS ws://localhost:8000/ws/load-test/{test_id}
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| `LOAD_TESTING_QUICK_START.md` | 5-minute setup guide with examples |
| `LOAD_TESTING_INTEGRATION_GUIDE.md` | Complete integration and usage guide |
| `LOAD_TESTING_IMPLEMENTATION_SUMMARY.md` | Technical overview and architecture |
| `backend/api_matrix_data/load_test_configs.json` | Pre-configured test examples |
| `backend/api_matrix_data/load_tests/active_farms_load_test.js` | Example k6 script |

## 💡 Usage Examples

### Basic Load Test
```javascript
{
  "test_name": "User Flow Test",
  "bearer_token": "Bearer YOUR_TOKEN",
  "requests": [
    {
      "method": "POST",
      "url": "https://api.example.com/endpoint",
      "params": {
        "headers": { "Authorization": "Bearer YOUR_TOKEN" },
        "tags": { "name": "endpoint-1" }
      }
    }
  ],
  "options": {
    "scenarios": {
      "default": {
        "executor": "ramping-vus",
        "stages": [
          { "target": 5, "duration": "10s" },
          { "target": 10, "duration": "30s" },
          { "target": 0, "duration": "10s" }
        ]
      }
    }
  }
}
```

### Stress Test
```javascript
"stages": [
  { "target": 50, "duration": "5m" },
  { "target": 100, "duration": "5m" },
  { "target": 200, "duration": "5m" },
  { "target": 0, "duration": "2m" }
]
```

### Soak Test (Long Duration)
```javascript
"stages": [
  { "target": 15, "duration": "2m" },
  { "target": 15, "duration": "1h" },  // Hold for 1 hour
  { "target": 0, "duration": "2m" }
]
```

## 🔧 Configuration

### Pre-configured Profiles

Edit `backend/api_matrix_data/load_test_configs.json`:

1. **active_farms_test** - Ramp-up test for active farms API
2. **farmer_list_test** - Constant load test
3. **stress_test** - Progressive stress test (multiple endpoints)
4. **soak_test** - Long-duration stability test

### Custom Configuration

Create your own test in the configs file following the structure.

## 📊 Understanding Results

### Performance Benchmarks

| Metric | Good | Acceptable | Poor |
|--------|------|-----------|------|
| Avg Response | < 500ms | < 1000ms | > 2000ms |
| P95 Response | < 1000ms | < 2000ms | > 3000ms |
| P99 Response | < 1500ms | < 3000ms | > 5000ms |
| Error Rate | < 1% | < 5% | > 10% |
| Throughput | > 100 req/s | > 50 req/s | < 10 req/s |

### Reading Charts

1. **Response Time Trend** → Shows performance stability over time
2. **Endpoint Comparison** → Compare performance across endpoints
3. **Throughput** → Requests handled per second
4. **Error Rate** → Percentage of failed requests
5. **Distribution** → How response times are spread

## 🐛 Troubleshooting

### "k6 command not found"
- Install k6: `choco install k6`
- Add k6 to system PATH

### "WebSocket connection failed"
- Ensure backend running: `python server.py`
- Check http://localhost:8000 accessible
- Verify CORS settings in server.py

### "Test not starting"
- Update bearer token in code
- Verify API endpoint accessible
- Check backend logs

### "No charts appearing"
- Install Recharts: `npm install recharts`
- Clear browser cache
- Check browser console (F12)

## 🎓 Learning Path

1. **Setup** (5 min) - Follow quick start
2. **First Test** (10 min) - Run example script
3. **Understand Metrics** (10 min) - Review results
4. **Customize** (15 min) - Create your configs
5. **Advanced** (30 min) - Multiple endpoints, schedules
6. **Integration** (30+ min) - Add to test pipeline

## 🔒 Security

- ✅ Bearer tokens handled securely
- ✅ CORS configured for frontend only
- ✅ Input validation on all endpoints
- ✅ No credentials logged
- ✅ Results stored locally

## 📚 Resources

- **k6 Documentation**: https://k6.io/docs/
- **Recharts Docs**: https://recharts.org/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/

## 🤝 Integration Examples

### Add to Existing React Component

```javascript
import LoadTestDashboard from './components/LoadTestDashboard';

function MyPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <LoadTestDashboard />
    </div>
  );
}
```

### Add to Router

```javascript
import LoadTestDashboard from './components/LoadTestDashboard';

const routes = [
  {
    path: '/load-test',
    element: <LoadTestDashboard />,
  }
];
```

### Schedule Recurring Tests

```bash
# Windows Task Scheduler
# Linux Cron: 0 2 * * * python backend/run_scheduled_test.py
```

## 🚀 Next Steps

1. ✅ Install k6
2. ✅ Start backend & frontend
3. ✅ Import LoadTestDashboard component
4. ✅ Update bearer token
5. ✅ Run first load test
6. ✅ Review metrics and charts
7. ✅ Create custom test profiles
8. ✅ Integrate into CI/CD pipeline

## 📞 Support

- **Documentation**: See guides listed above
- **Code Examples**: Check `backend/api_matrix_data/load_tests/`
- **Issues**: Review troubleshooting section

## 📝 Version Info

- **Version**: 1.0
- **Status**: Production Ready ✅
- **Last Updated**: April 15, 2026
- **Python**: 3.8+
- **Node**: 16+
- **k6**: Latest

---

**Ready to test?** 🚀

Start with: `LOAD_TESTING_QUICK_START.md`

For detailed info: `LOAD_TESTING_INTEGRATION_GUIDE.md`

For technical details: `LOAD_TESTING_IMPLEMENTATION_SUMMARY.md`
