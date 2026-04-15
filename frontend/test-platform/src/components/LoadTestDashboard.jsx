import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import './LoadTestDashboard.css';

export const LoadTestDashboard = () => {
  const [testName, setTestName] = useState('');
  const [testRunning, setTestRunning] = useState(false);
  const [testId, setTestId] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [timelineData, setTimelineData] = useState([]);
  const [endpointMetrics, setEndpointMetrics] = useState({});
  const [distribution, setDistribution] = useState({});
  const [heatmapData, setHeatmapData] = useState({});
  const [error, setError] = useState('');
  const wsRef = useRef(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (testRunning && testId) {
      wsRef.current = new WebSocket(`ws://localhost:8000/ws/load-test/${testId}`);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'METRIC_RECORDED') {
          setTimelineData(prev => [...prev, {
            time: new Date().toLocaleTimeString(),
            ...data.metric
          }]);
        } else if (data.type === 'LOAD_TEST_COMPLETED') {
          setTestRunning(false);
          setMetrics(data.summary);
          setEndpointMetrics(data.summary.endpoints || {});
          fetchTestDetails(testId);
        } else if (data.type === 'LOAD_TEST_ERROR') {
          setError(data.error);
          setTestRunning(false);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection failed');
      };
      
      return () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    }
  }, [testRunning, testId]);

  const startLoadTest = async () => {
    if (!testName.trim()) {
      setError('Please enter a test name');
      return;
    }

    try {
      setError('');
      setTestRunning(true);
      setMetrics(null);
      setTimelineData([]);
      
      // TODO: Get actual bearer token and requests from configuration
      const config = {
        test_name: testName,
        bearer_token: 'Bearer YOUR_TOKEN',
        headers: {
          'Authorization': 'Bearer YOUR_TOKEN'
        },
        requests: [
          {
            method: 'POST',
            url: 'https://api.telangana.krishivaas.in/api/v1/healthy-stress-farmer-farms-crops?draw=1&start=0&length=20&org_id=4&app_type=state',
            body: null,
            params: { 
              headers: { 'Authorization': 'Bearer YOUR_TOKEN' },
              tags: { name: 'active-farms' }
            }
          }
        ],
        options: {
          scenarios: {
            default: {
              executor: 'ramping-vus',
              stages: [
                { target: 5, duration: '10s' },
                { target: 5, duration: '30s' },
                { target: 0, duration: '10s' }
              ]
            }
          }
        }
      };

      const response = await fetch('http://localhost:8000/api/load-test/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      const data = await response.json();
      
      if (data.success) {
        setTestId(data.test_id);
      } else {
        setError('Failed to start test');
        setTestRunning(false);
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
      setTestRunning(false);
    }
  };

  const fetchTestDetails = async (id) => {
    try {
      const response = await fetch(`http://localhost:8000/api/load-test/${id}/summary`);
      const data = await response.json();
      
      setMetrics(data.summary);
      setEndpointMetrics(data.summary.endpoints || {});
      setTimelineData(data.timeline || []);
      setHeatmapData(data.heatmap || {});
      setDistribution(data.distribution || {});
    } catch (err) {
      console.error('Error fetching test details:', err);
    }
  };

  return (
    <div className="load-test-dashboard">
      <div className="dashboard-header">
        <h1>Load Testing & Performance Monitoring</h1>
      </div>

      {/* Test Controls */}
      <div className="test-controls">
        <div className="input-group">
          <input
            type="text"
            placeholder="Enter test name"
            value={testName}
            onChange={(e) => setTestName(e.target.value)}
            disabled={testRunning}
            className="test-input"
          />
          <button
            onClick={startLoadTest}
            disabled={testRunning}
            className={`start-button ${testRunning ? 'running' : ''}`}
          >
            {testRunning ? 'Test Running...' : 'Start Load Test'}
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}
      </div>

      {/* Loading Animation */}
      {testRunning && <LoadingAnimation />}

      {/* Metrics Summary */}
      {metrics && <MetricsSummary metrics={metrics} />}

      {/* Charts */}
      <div className="charts-container">
        
        {/* Response Time Trend */}
        {timelineData.length > 0 && (
          <div className="chart-box">
            <h3>Response Time Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="duration_ms" stroke="#8884d8" name="Duration (ms)" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Endpoint Comparison */}
        {Object.keys(endpointMetrics).length > 0 && (
          <div className="chart-box">
            <h3>Endpoints Performance Comparison</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={Object.entries(endpointMetrics).map(([name, metrics]) => ({
                  name,
                  avg: metrics.avg_duration,
                  p95: metrics.p95_duration,
                  p99: metrics.p99_duration
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="avg" fill="#8884d8" name="Avg (ms)" />
                <Bar dataKey="p95" fill="#82ca9d" name="P95 (ms)" />
                <Bar dataKey="p99" fill="#ffc658" name="P99 (ms)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Throughput */}
        {Object.keys(endpointMetrics).length > 0 && (
          <div className="chart-box">
            <h3>Throughput (Requests/sec)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={Object.entries(endpointMetrics).map(([name, metrics]) => ({
                  name,
                  throughput: metrics.throughput
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="throughput" fill="#82ca9d" name="Req/sec" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Error Rate */}
        {Object.keys(endpointMetrics).length > 0 && (
          <div className="chart-box">
            <h3>Error Rate by Endpoint</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={Object.entries(endpointMetrics).map(([name, metrics]) => ({
                  name,
                  error_rate: metrics.error_rate
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                <Bar dataKey="error_rate" fill="#ff8884" name="Error Rate (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Response Time Distribution */}
        {Object.keys(distribution).length > 0 && (
          <div className="chart-box">
            <h3>Response Time Distribution</h3>
            {Object.entries(distribution).map(([endpoint, data]) => (
              <div key={endpoint} className="distribution-chart">
                <h4>{endpoint}</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart
                    data={data.bins.map((count, idx) => ({
                      range: data.labels[idx],
                      count
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
};

// Loading Animation Component
const LoadingAnimation = () => {
  return (
    <div className="loading-container">
      <div className="loading-animation">
        <div className="spinner"></div>
        <p>Running Load Test...</p>
        <p className="loading-text">Sending requests and collecting metrics...</p>
      </div>
    </div>
  );
};

// Metrics Summary Component
const MetricsSummary = ({ metrics }) => {
  return (
    <div className="metrics-summary">
      <h2>Test Summary</h2>
      <div className="metrics-grid">
        <MetricCard
          label="Total Requests"
          value={metrics.total_requests}
          icon="📊"
        />
        <MetricCard
          label="Successful"
          value={metrics.successful_requests}
          icon="✅"
          color="#4CAF50"
        />
        <MetricCard
          label="Failed"
          value={metrics.failed_requests}
          icon="❌"
          color="#f44336"
        />
        <MetricCard
          label="Avg Duration"
          value={`${metrics.total_duration}ms`}
          icon="⏱️"
        />
      </div>

      {/* Detailed Endpoint Metrics */}
      {metrics.endpoints && (
        <div className="endpoints-details">
          <h3>Endpoint Details</h3>
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Requests</th>
                <th>Success</th>
                <th>Error Rate</th>
                <th>Avg (ms)</th>
                <th>P95 (ms)</th>
                <th>P99 (ms)</th>
                <th>Throughput</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics.endpoints).map(([name, data]) => (
                <tr key={name}>
                  <td className="endpoint-name">{name}</td>
                  <td>{data.total_requests}</td>
                  <td className="success">{data.successful}</td>
                  <td className={data.error_rate > 5 ? 'error' : 'normal'}>
                    {data.error_rate.toFixed(2)}%
                  </td>
                  <td>{data.avg_duration}</td>
                  <td>{data.p95_duration}</td>
                  <td>{data.p99_duration}</td>
                  <td>{data.throughput} req/s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ label, value, icon, color }) => {
  return (
    <div className="metric-card" style={{ borderLeftColor: color }}>
      <div className="metric-icon">{icon}</div>
      <div className="metric-content">
        <p className="metric-label">{label}</p>
        <p className="metric-value">{value}</p>
      </div>
    </div>
  );
};

export default LoadTestDashboard;
