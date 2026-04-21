"""
Pytest plugin to capture API test results and forward to matrix API
This plugin hooks into pytest to extract APIValidator results after each test
"""

import pytest
import json
import os
from datetime import datetime
from typing import Dict, List


# Global storage for API results across all tests in session
_api_results_session = []


def pytest_runtest_teardown(item):
    """
    Hook called after each test runs (even if it fails).
    Captures API validation results from the test.
    """
    try:
        # Check if test has fixture instances
        if hasattr(item, 'fixturenames'):
            # Try to get api_validator fixture results
            if 'api_validator' in item.fixturenames:
                fixture_value = item.funcargs.get('api_validator')
                if fixture_value and hasattr(fixture_value, 'captured_responses'):
                    responses = fixture_value.captured_responses
                    if responses:
                        # Add test context to each response
                        for response in responses:
                            response['test_name'] = item.name
                            response['test_file'] = item.fspath.basename
                        
                        _api_results_session.extend(responses)
    except Exception as e:
        print(f"Error capturing API results: {e}")


def pytest_sessionfinish(session, exitstatus):
    """
    Hook called when pytest session finishes.
    Saves captured API results to a JSON file for test_runner to read.
    """
    if not _api_results_session:
        return
    
    try:
        # Save to a file that test_runner can read
        output_file = os.path.join(
            os.path.dirname(__file__),
            '.api_results_captured.json'
        )
        
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_results": len(_api_results_session),
                "results": _api_results_session
            }, f, indent=2, default=str)
        
        print(f"\n✓ Captured {len(_api_results_session)} API test results")
        print(f"  Saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving API results: {e}")
