/**
 * Example Load Test Script - Telagana Krishivaas API
 * 
 * This script demonstrates how to structure a load test for use with
 * the Load Testing Dashboard.
 * 
 * Usage:
 * 1. Update the bearerToken with your actual token
 * 2. Customize the requests array with your endpoints
 * 3. Adjust the scenarios stages as needed
 * 4. Use the frontend dashboard to run the test
 */

import { sleep, check } from 'k6';
import http from 'k6/http';

// ============================================================================
// Configuration
// ============================================================================

// Replace with your actual bearer token
const bearerToken = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS50ZWxhbmdhbmEua3Jpc2hpdmFhcy5pbi9hcGkvdjEvbG9naW4iLCJpYXQiOjE3NjIzMjIzMTQsImV4cCI6MTc2NDkxNDMxNCwibmJmIjoxNzYyMzIyMzE0LCJqdGkiOiJqMjJ4TDNjY01VWGtwd1ZDIiwic3ViIjoiMzMiLCJwcnYiOiJmZjY2ZDA3ZjZkNDYyNzMzYmIyOWMzN2QyYTU5YmViZjZiZDY2NjQwIn0.F1j8UggJFLHLXba-OdIyw66pn2f4wn1Fj7SJPWlN2wk';

const commonHeaders = {
  Authorization: bearerToken,
  'Content-Type': 'application/json',
};

// ============================================================================
// Test Configuration
// ============================================================================

export const options = {
  // Define load scenarios
  scenarios: {
    ramp_up: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { target: 5, duration: '10s' },    // Ramp up to 5 VUs over 10 seconds
        { target: 10, duration: '30s' },   // Ramp up to 10 VUs over 30 seconds
        { target: 10, duration: '1m' },    // Stay at 10 VUs for 1 minute
        { target: 0, duration: '10s' },    // Ramp down to 0 VUs
      ],
      gracefulStop: '30s',
      exec: 'active_farms_test',
    },
  },

  // Performance thresholds for SLA validation
  thresholds: {
    'http_req_duration': ['p(95)<2000', 'p(99)<3000'],  // 95% requests under 2s, 99% under 3s
    'http_req_failed': ['rate<0.1'],                      // Less than 10% failure rate
  },

  // System limits
  ext: {
    loadimpact: {
      projectID: 0,  // Set if using k6 Cloud
      name: 'Active Farms Load Test',
    }
  }
};

// ============================================================================
// Request Definitions
// ============================================================================

const requests = [
  // Active Farms Endpoint
  {
    method: 'POST',
    url: 'https://api.telangana.krishivaas.in/api/v1/healthy-stress-farmer-farms-crops?draw=1&start=0&length=20&org_id=4&app_type=state',
    body: null,
    params: {
      headers: commonHeaders,
      tags: { name: 'active-farms' },
      timeout: '10s',
    },
  },

  // Uncomment and customize additional endpoints as needed:
  
  // {
  //   method: 'GET',
  //   url: 'https://api.telangana.krishivaas.in/api/v1/get_farmers?orgid_=4&draw=1&start=0&length=24&msearch=&farm_type=current',
  //   params: {
  //     headers: commonHeaders,
  //     tags: { name: 'farmer-list' },
  //     timeout: '10s',
  //   },
  // },

  // {
  //   method: 'GET',
  //   url: 'https://api.telangana.krishivaas.in/api/v1/client-app/notification/list?group&cfa_id&limit&start',
  //   params: {
  //     headers: commonHeaders,
  //     tags: { name: 'notification-list' },
  //     timeout: '10s',
  //   },
  // },

  // {
  //   method: 'GET',
  //   url: 'https://api.telangana.krishivaas.in/api/v1/get-active-crops-name?farm_type=current',
  //   params: {
  //     headers: commonHeaders,
  //     tags: { name: 'crops-filter' },
  //     timeout: '10s',
  //   },
  // },

  // {
  //   method: 'GET',
  //   url: 'https://api.telangana.krishivaas.in/api/v1/get-role-level-user?farm_type=current',
  //   params: {
  //     headers: commonHeaders,
  //     tags: { name: 'role-level-filter' },
  //     timeout: '10s',
  //   },
  // },

  // {
  //   method: 'GET',
  //   url: 'https://api.telangana.krishivaas.in/api/v1/get-dashboard-summary?app_type=state&farm_type=current',
  //   params: {
  //     headers: commonHeaders,
  //     tags: { name: 'dashboard-summary' },
  //     timeout: '10s',
  //   },
  // },
];

// ============================================================================
// Test Functions
// ============================================================================

/**
 * Main test function for active farms endpoints
 * This function gets executed according to the scenario definition
 */
export function active_farms_test() {
  // Execute all requests in parallel (batch)
  let responses = http.batch(requests);

  // Perform checks on responses
  responses.forEach((response, index) => {
    const endpoint = requests[index].params?.tags?.name || 'unknown';
    
    check(response, {
      [`${endpoint} - status is 200`]: (r) => r.status === 200,
      [`${endpoint} - has content`]: (r) => r.body && r.body.length > 0,
      [`${endpoint} - response time < 2s`]: (r) => r.timings.duration < 2000,
    });

    // Log performance data
    __VU > 0 && console.log(
      `[${endpoint}] ${response.status} - ${response.timings.duration.toFixed(0)}ms`
    );
  });

  // Think time between iterations
  sleep(1);
}

// ============================================================================
// Setup and Teardown
// ============================================================================

/**
 * Setup function - runs once before test starts
 * Use this for initialization
 */
export function setup() {
  console.log('Load test starting...');
  return { startTime: new Date() };
}

/**
 * Teardown function - runs once after test completes
 * Use this for cleanup
 */
export function teardown(data) {
  console.log(`Load test completed. Duration: ${new Date() - data.startTime}ms`);
}
