"""
API Test Validation utility for pytest integration
Allows test cases to validate both UI and API behavior
"""

import requests
import pytest
import allure
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import os


class APIValidator:
    """Validates API endpoints during test execution"""
    
    def __init__(self, base_url: str = "http://localhost:3000", timeout: int = 10, matrix_url: str = "http://localhost:8000"):
        """
        Initialize API validator
        
        Args:
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
            matrix_url: Matrix API backend URL for sending results
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.matrix_url = matrix_url.rstrip('/')
        self.session = requests.Session()
        self.test_results = []
        self.captured_responses = []
    
    def validate_endpoint(
        self,
        method: str,
        endpoint: str,
        expected_status: int = 200,
        headers: Optional[Dict] = None,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        description: str = ""
    ) -> bool:
        """
        Validate a single API endpoint and capture full response data
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path
            expected_status: Expected HTTP status code
            headers: Request headers
            data: Request body data
            params: Query parameters
            description: Description of the test
        
        Returns:
            True if validation passed, False otherwise
        """
        start_time = datetime.now()
        try:
            url = self.base_url + endpoint
            
            # Make request
            response = None
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, params=params, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data, params=params, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, headers=headers, json=data, params=params, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check status
            passed = response.status_code == expected_status
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Parse response body
            response_body = None
            try:
                response_body = response.json() if response.text else None
            except:
                response_body = response.text[:500] if response.text else None
            
            # Log result with full response data
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "actual_status": response.status_code,
                "expected_status": expected_status,
                "passed": passed,
                "description": description,
                "response_size": len(response.text) if response.text else 0,
                "duration_ms": duration_ms,
                "timestamp": start_time.isoformat(),
                "response_body": response_body,
                "response_headers": dict(response.headers) if response.headers else {},
                "url": url
            }
            self.test_results.append(result)
            self.captured_responses.append(result)
            
            # Add to Allure report with response data
            with allure.step(f"API: {method.upper()} {endpoint}"):
                response_text = f"""
Status: {response.status_code} (Expected: {expected_status})
URL: {url}
Description: {description}
Duration: {duration_ms}ms
Response Size: {result['response_size']} bytes

Response Body:
{json.dumps(response_body, indent=2) if response_body else 'Empty'}
"""
                allure.attach(
                    response_text,
                    name="API Response",
                    attachment_type=allure.attachment_type.TEXT
                )
            
            return passed
        
        except requests.Timeout:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "actual_status": None,
                "expected_status": expected_status,
                "passed": False,
                "description": description,
                "error": "Request timeout",
                "duration_ms": duration_ms,
                "timestamp": start_time.isoformat(),
                "url": self.base_url + endpoint
            }
            self.test_results.append(result)
            self.captured_responses.append(result)
            return False
        
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "actual_status": None,
                "expected_status": expected_status,
                "passed": False,
                "description": description,
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": start_time.isoformat(),
                "url": self.base_url + endpoint
            }
            self.test_results.append(result)
            self.captured_responses.append(result)
            return False
    
    def validate_endpoints(self, endpoints: List[Dict]) -> bool:
        """
        Validate multiple endpoints
        
        Args:
            endpoints: List of endpoint configs with keys:
                - method: HTTP method
                - endpoint: API path
                - expected_status: Expected status code (default: 200)
                - headers: Request headers (optional)
                - data: Request body (optional)
                - params: Query params (optional)
                - description: Test description (optional)
        
        Returns:
            True if all validations passed, False otherwise
        """
        all_passed = True
        
        for ep_config in endpoints:
            passed = self.validate_endpoint(
                method=ep_config.get("method", "GET"),
                endpoint=ep_config.get("endpoint", ""),
                expected_status=ep_config.get("expected_status", 200),
                headers=ep_config.get("headers"),
                data=ep_config.get("data"),
                params=ep_config.get("params"),
                description=ep_config.get("description", "")
            )
            
            if not passed:
                all_passed = False
        
        return all_passed
    
    def assert_endpoint(
        self,
        method: str,
        endpoint: str,
        expected_status: int = 200,
        headers: Optional[Dict] = None,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        description: str = ""
    ) -> None:
        """
        Validate endpoint and raise AssertionError if validation fails
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            expected_status: Expected status code
            headers: Request headers
            data: Request body
            params: Query parameters
            description: Test description
        
        Raises:
            AssertionError: If validation fails
        """
        passed = self.validate_endpoint(
            method=method,
            endpoint=endpoint,
            expected_status=expected_status,
            headers=headers,
            data=data,
            params=params,
            description=description
        )
        
        if not passed:
            last_result = self.test_results[-1] if self.test_results else {}
            pytest.fail(
                f"API validation failed: {method} {endpoint}\n"
                f"Expected: {expected_status}, Got: {last_result.get('status')}\n"
                f"Error: {last_result.get('error', 'Status mismatch')}"
            )
    
    def get_results(self) -> List[Dict]:
        """Get all test results with captured response data"""
        return self.test_results
    
    def get_captured_responses(self) -> List[Dict]:
        """Get all captured API responses"""
        return self.captured_responses
    
    def get_summary(self) -> Dict:
        """Get summary of all tests"""
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r.get("passed")])
        failed = total - passed
        total_duration = sum(r.get("duration_ms", 0) for r in self.test_results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "total_duration_ms": total_duration
        }
    
    def send_results_to_matrix(self) -> bool:
        """
        Send API test results to matrix API backend
        
        Returns:
            True if successful, False otherwise
        """
        if not self.captured_responses:
            return True
        
        try:
            response = requests.post(
                f"{self.matrix_url}/api/matrix/automation-results",
                json=self.captured_responses,
                timeout=10
            )
            
            success = response.status_code in [200, 201]
            if success:
                print(f"✓ Sent {len(self.captured_responses)} API results to matrix")
            else:
                print(f"✗ Matrix API returned {response.status_code}: {response.text}")
            
            return success
        
        except requests.ConnectionError:
            print(f"✗ Cannot connect to matrix API at {self.matrix_url}")
            return False
        except Exception as e:
            print(f"✗ Error sending API results to matrix: {str(e)}")
            return False


# Pytest fixtures
@pytest.fixture
def api_validator():
    """Pytest fixture for API validator"""
    return APIValidator()


@pytest.fixture
def api_validator_custom(request):
    """Pytest fixture with custom base URL from parametrize"""
    base_url = getattr(request, 'param', 'http://localhost:3000')
    return APIValidator(base_url=base_url)
