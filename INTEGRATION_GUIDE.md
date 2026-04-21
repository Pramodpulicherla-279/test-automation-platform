"""
Integration Guide: Adding Performance Monitoring to Existing Tests
Shows how to modify your existing test code to use performance tracking
"""

# ============================================================================
# BEFORE: Original API Test Code
# ============================================================================

"""
Original code using basic APITestRunner:

from tests.api_test_runner import APITestRunner

def run_my_tests():
    runner = APITestRunner(base_url="https://api.example.com")
    
    api_configs = [
        {
            "api_name": "Get Users",
            "method": "GET",
            "endpoint": "/api/users",
            "expected_status": [200]
        }
    ]
    
    results = runner.run_tests_sync(api_configs)
    runner.export_results("results/output.csv")
"""


# ============================================================================
# AFTER: Updated Code with Performance Monitoring
# ============================================================================

"""
New code using PerformanceTrackingAPIRunner:
"""

from backend.performance_api_runner import PerformanceTrackingAPIRunner

def run_my_tests_with_monitoring():
    # Only change: Use PerformanceTrackingAPIRunner instead of APITestRunner
    runner = PerformanceTrackingAPIRunner(
        base_url="https://api.example.com",
        environment="production",  # Add environment name
        enable_monitoring=True      # Enable performance collection
    )
    
    api_configs = [
        {
            "api_name": "Get Users",
            "endpoint_id": "get_users",  # Add endpoint ID for tracking
            "method": "GET",
            "endpoint": "/api/users",
            "expected_status": [200]
        }
    ]
    
    # Run tests (same as before)
    results = runner.run_tests_sync(api_configs)
    
    # Export results with performance metrics
    runner.export_results_json("results/output.json", include_performance=True)
    
    # NEW: Get performance metrics
    perf_summary = runner.get_performance_summary()
    print(f"Success Rate: {perf_summary['overall_success_rate']:.1f}%")
    print(f"Avg Response Time: {perf_summary['avg_response_time_ms']:.0f}ms")


# ============================================================================
# INTEGRATION PATTERN 1: Pytest Integration
# ============================================================================

import pytest

@pytest.fixture
def performance_runner():
    """Fixture that provides a performance-tracking API runner"""
    return PerformanceTrackingAPIRunner(
        base_url="https://api.example.com",
        environment="staging"
    )

def test_user_management_apis(performance_runner):
    """Test with automatic performance tracking"""
    apis = [
        {
            "api_name": "Create User",
            "endpoint_id": "create_user",
            "method": "POST",
            "endpoint": "/api/users",
            "body": {"name": "Test User", "email": "test@example.com"},
            "expected_status": [201]
        },
        {
            "api_name": "Get User",
            "endpoint_id": "get_user",
            "method": "GET",
            "endpoint": "/api/users/1",
            "expected_status": [200]
        },
        {
            "api_name": "Delete User",
            "endpoint_id": "delete_user",
            "method": "DELETE",
            "endpoint": "/api/users/1",
            "expected_status": [204]
        }
    ]
    
    results = performance_runner.run_tests_sync(apis)
    
    # Performance assertions
    assert results['success_rate'] >= 90, "Less than 90% success rate"
    
    perf = performance_runner.get_performance_summary()
    assert perf['avg_response_time_ms'] < 1000, "Average response time exceeds 1 second"


# ============================================================================
# INTEGRATION PATTERN 2: Multi-Environment Testing
# ============================================================================

def test_across_environments():
    """Run same tests across multiple environments"""
    
    environments = {
        "dev": "https://dev-api.example.com",
        "staging": "https://staging-api.example.com",
        "production": "https://api.example.com"
    }
    
    api_configs = [
        {
            "api_name": "Health Check",
            "endpoint_id": "health",
            "method": "GET",
            "endpoint": "/health",
            "expected_status": [200]
        }
    ]
    
    for env_name, base_url in environments.items():
        print(f"\nTesting {env_name}...")
        
        runner = PerformanceTrackingAPIRunner(
            base_url=base_url,
            environment=env_name
        )
        
        results = runner.run_tests_sync(api_configs)
        print(f"  Success Rate: {results['success_rate']:.1f}%")
        
        # Export per environment
        runner.export_results_json(f"results/{env_name}_report.json", include_performance=True)


# ============================================================================
# INTEGRATION PATTERN 3: Continuous Performance Thresholds
# ============================================================================

def test_with_performance_thresholds():
    """Test with strict performance requirements"""
    
    runner = PerformanceTrackingAPIRunner(
        base_url="https://api.example.com",
        environment="production"
    )
    
    apis = [
        {"api_name": "List API", "endpoint_id": "list", "method": "GET", "endpoint": "/api/items", "expected_status": [200]},
        {"api_name": "Get API", "endpoint_id": "get", "method": "GET", "endpoint": "/api/items/1", "expected_status": [200]},
    ]
    
    results = runner.run_tests_sync(apis)
    
    # Performance SLAs
    SLA_SUCCESS_RATE = 99  # 99% minimum
    SLA_P95_RESPONSE = 500  # 500ms max for 95th percentile
    SLA_MAX_RESPONSE = 2000  # 2 second max
    
    perf = runner.get_performance_summary()
    
    # Assertions with meaningful error messages
    assert perf['overall_success_rate'] >= SLA_SUCCESS_RATE, \
        f"Success rate {perf['overall_success_rate']:.1f}% below SLA {SLA_SUCCESS_RATE}%"
    
    for endpoint in perf['endpoint_metrics']:
        assert endpoint['max_response_time_ms'] <= SLA_MAX_RESPONSE, \
            f"{endpoint['endpoint_name']} max response {endpoint['max_response_time_ms']:.0f}ms exceeds SLA {SLA_MAX_RESPONSE}ms"
        
        assert endpoint['p95_response_time_ms'] <= SLA_P95_RESPONSE, \
            f"{endpoint['endpoint_name']} P95 response {endpoint['p95_response_time_ms']:.0f}ms exceeds SLA {SLA_P95_RESPONSE}ms"


# ============================================================================
# INTEGRATION PATTERN 4: Batch Test Execution with Reporting
# ============================================================================

def run_comprehensive_test_suite():
    """Run comprehensive test suite with detailed reporting"""
    
    test_suites = {
        "User Management": [
            {"api_name": "Create User", "endpoint_id": "create_user", "method": "POST", "endpoint": "/users", "expected_status": [201]},
            {"api_name": "Get User", "endpoint_id": "get_user", "method": "GET", "endpoint": "/users/1", "expected_status": [200]},
            {"api_name": "List Users", "endpoint_id": "list_users", "method": "GET", "endpoint": "/users", "expected_status": [200]},
            {"api_name": "Update User", "endpoint_id": "update_user", "method": "PUT", "endpoint": "/users/1", "expected_status": [200]},
            {"api_name": "Delete User", "endpoint_id": "delete_user", "method": "DELETE", "endpoint": "/users/1", "expected_status": [204]},
        ],
        "Product Management": [
            {"api_name": "List Products", "endpoint_id": "list_products", "method": "GET", "endpoint": "/products", "expected_status": [200]},
            {"api_name": "Get Product", "endpoint_id": "get_product", "method": "GET", "endpoint": "/products/1", "expected_status": [200]},
            {"api_name": "Create Product", "endpoint_id": "create_product", "method": "POST", "endpoint": "/products", "expected_status": [201]},
        ]
    }
    
    all_results = {}
    
    for suite_name, apis in test_suites.items():
        print(f"\nRunning test suite: {suite_name}")
        
        runner = PerformanceTrackingAPIRunner(
            base_url="https://api.example.com",
            environment="staging"
        )
        
        results = runner.run_tests_sync(apis)
        all_results[suite_name] = results
        
        # Export suite results
        runner.export_results_json(f"results/suite_{suite_name.replace(' ', '_').lower()}.json")
        
        print(f"  ✓ {results['passed']}/{results['total']} tests passed")
        print(f"  ✓ Success rate: {results['success_rate']:.1f}%")
    
    # Generate summary report
    print("\n" + "="*60)
    print("Test Suite Summary Report")
    print("="*60)
    
    for suite_name, results in all_results.items():
        print(f"\n{suite_name}:")
        print(f"  Total: {results['total']}")
        print(f"  Passed: {results['passed']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Success Rate: {results['success_rate']:.1f}%")
        print(f"  Avg Duration: {results['avg_duration_ms']:.0f}ms")


# ============================================================================
# MIGRATION CHECKLIST
# ============================================================================

"""
Checklist for migrating existing tests to use performance monitoring:

□ 1. Install updated requirements.txt
    pip install -r requirements.txt

□ 2. Start Docker containers (for Grafana + InfluxDB)
    docker-compose up -d

□ 3. Replace import statements
    FROM: from tests.api_test_runner import APITestRunner
    TO:   from backend.performance_api_runner import PerformanceTrackingAPIRunner

□ 4. Update runner initialization
    Add: environment="production"  (or dev/staging)
    Add: enable_monitoring=True

□ 5. Add endpoint_id to API configs
    Add: "endpoint_id": "unique_endpoint_id" to each API config

□ 6. Update export calls
    FROM: runner.export_results("output.csv")
    TO:   runner.export_results_json("output.json", include_performance=True)

□ 7. Add performance assertions (optional)
    perf = runner.get_performance_summary()
    assert perf['overall_success_rate'] >= 90

□ 8. Run tests and verify metrics in Grafana
    Open http://localhost:3000 and check dashboards

□ 9. Create custom dashboards for your needs
    Use Grafana UI to create project-specific dashboards

□ 10. Set up alerts (optional)
    Configure Grafana alerts for SLA violations
"""


# ============================================================================
# QUICK REFERENCE: Module Imports
# ============================================================================

"""
Available imports from performance modules:

from backend.performance_api_runner import PerformanceTrackingAPIRunner
  - Main runner class with performance tracking

from backend.performance_monitor import PerformanceMonitor, get_performance_monitor
  - Direct access to performance monitor
  - Manually record metrics

from backend.performance_metrics import PerformanceMetricsAnalyzer, get_analyzer
  - Analyze collected metrics
  - Generate reports
  - Export data


Classes and Methods:

PerformanceTrackingAPIRunner:
  - __init__(base_url, environment, enable_monitoring)
  - run_tests_sync(api_configs, timeout)
  - run_test()
  - export_results_json(path, include_performance)
  - export_metrics_influxdb_format(path)
  - get_performance_summary()

PerformanceMetricsAnalyzer:
  - add_metric(endpoint_id, endpoint_name, method, path, environment, response_time, status_code, success)
  - get_endpoint_metrics(endpoint_id, environment)
  - get_environment_metrics(environment)
  - get_summary_report()
  - export_report(filepath)
  - reset()
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nFor full examples, see: examples/performance_monitoring_examples.py")
    print("For setup guide, see: GRAFANA_SETUP_GUIDE.md")
