"""
Shared pytest fixtures for all test cases
Provides API validation and other utilities
"""

import pytest
from utils.api_validator import APIValidator


@pytest.fixture
def api_validator():
    """
    Provides APIValidator fixture for all test cases.
    Usage in test:
        def test_something(self, api_validator):
            api_validator.assert_endpoint(...)
    """
    return APIValidator(base_url="http://localhost:3000")


@pytest.fixture(scope="function")
def api_endpoints():
    """
    Provides pre-configured common API endpoints for validation.
    """
    return {
        "auth": {
            "health": {"method": "GET", "endpoint": "/api/auth/health", "expected_status": 200},
            "status": {"method": "GET", "endpoint": "/api/auth/status", "expected_status": 200},
        },
        "user": {
            "me": {"method": "GET", "endpoint": "/api/user/me", "expected_status": 200},
            "profile": {"method": "GET", "endpoint": "/api/user/profile", "expected_status": 200},
        },
        "dashboard": {
            "stats": {"method": "GET", "endpoint": "/api/dashboard/stats", "expected_status": 200},
            "activities": {"method": "GET", "endpoint": "/api/dashboard/recent-activities", "expected_status": 200},
        }
    }


@pytest.fixture
def api_validator_with_results(api_validator):
    """
    APIValidator fixture that captures and returns results after test.
    """
    yield api_validator
    # Results are accessible via api_validator.get_results()
    # or api_validator.get_summary()


@pytest.fixture(params=["http://localhost:3000", "http://staging-api.example.com"])
def api_validator_multi_env(request):
    """
    APIValidator fixture that runs tests against multiple environments.
    
    Usage:
        def test_api_multi_env(self, api_validator_multi_env):
            api_validator_multi_env.validate_endpoint(...)
    """
    return APIValidator(base_url=request.param)
