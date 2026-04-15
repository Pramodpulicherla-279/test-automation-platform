import os
import pytest
import allure
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
import sys
import json
from datetime import datetime
sys.dont_write_bytecode = True

# Global storage for API results across all tests in session
_api_results_session = []

# 1. Register the custom command-line option
def pytest_addoption(parser):
    """
    Define a single CLI option: --apk
    """
    parser.addoption(
        "--apk",
        action="store",
        default=None,
        help="Path to the APK file under test",
    )

# 2. Capture API validation results from APIValidator fixture
def pytest_runtest_teardown(item):
    """
    Hook called after each test runs.
    Captures API validation results from APIValidator fixture.
    """
    try:
        if hasattr(item, 'funcargs'):
            # Check for api_validator fixture with captured responses
            if 'api_validator' in item.funcargs:
                validator = item.funcargs.get('api_validator')
                if validator and hasattr(validator, 'captured_responses'):
                    responses = validator.captured_responses
                    if responses:
                        # Add test context
                        for response in responses:
                            response['test_name'] = item.name
                            response['test_file'] = item.fspath.basename if hasattr(item, 'fspath') else 'unknown'
                        
                        _api_results_session.extend(responses)
                        print(f"✓ Captured {len(responses)} API results from {item.name}")
    except Exception as e:
        pass


def pytest_sessionfinish(session, exitstatus):
    """
    Hook called when pytest session finishes.
    Saves all captured API results to JSON for test_runner to read.
    """
    if not _api_results_session:
        return
    
    try:
        # Get project root
        project_root = session.config.rootdir.strpath if hasattr(session.config, 'rootdir') else os.path.dirname(__file__)
        
        # Save to file
        output_file = os.path.join(project_root, "tests", ".api_results_captured.json")
        
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_results": len(_api_results_session),
                "results": _api_results_session
            }, f, indent=2, default=str)
        
        print(f"\n✓ Saved {len(_api_results_session)} API test results from device to matrix API")
        
    except Exception as e:
        print(f"Error saving API results: {e}")

@pytest.fixture(scope="session")
def driver(request):
    """Appium driver fixture with APK path passed via --apk."""
    # Get APK path from CLI
    apk_path = request.config.getoption("--apk")

    if not apk_path:
        pytest.fail("No APK path provided! Backend must call pytest with --apk=/path/to/app.apk")

    if not os.path.exists(apk_path):
        pytest.fail(f"APK file not found at: {apk_path}")

    print(f"Initializing Appium with APK: {apk_path}")

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "AndroidDevice"
    # options.no_reset = False
    # options.full_reset = True
    # options.auto_grant_permissions = False
    # options.dont_stop_app_on_reset = True
    options.app = apk_path   # ✅ use the same --apk value

    # TODO: adjust URL / capabilities to your setup
    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

    # Clear logs at start to ensure we capture fresh data
    try:
        driver.get_log('logcat')
    except Exception:
        pass

    yield driver

    driver.quit()
    

def check_for_crashes(driver):
    """
    Retrieves logcat logs and looks for crash signatures.
    If a crash is detected, it captures the surrounding log lines (stack trace) 
    to provide meaningful context.
    """
    try:
        # Get logcat logs
        logs = driver.get_log('logcat')
        
        # Enhanced crash signatures based on your React Native log
        crash_signatures = [
            "fatal exception", 
            "force removing activity", 
            "androidruntime",       # Java stacktrace hook
            "beginning of crash", 
            "system.err",
            "am_crash",             # Activity Manager crash event
            "anr in",               # Application Not Responding
            "vm aborting",          # Native code crash
            "com.facebook.react.bridge", # React Native Bridge errors
            "jsapplicationillegalargumentexception" # Specific RN error from your log
        ]
        
        crash_details = []
        crash_detected = False
        limit_stack_trace = 100 # How many lines to capture after a crash
        lines_captured = 0

        for entry in logs:
            message = entry.get('message', '')
            msg_lower = message.lower()
            
            # Logic: If we haven't found a crash yet, look for signatures.
            # If we HAVE found a crash, keep capturing lines (for the stack trace).
            
            if not crash_detected:
                # 1. Check for standard signatures
                if any(sig in msg_lower for sig in crash_signatures):
                    crash_detected = True
                    crash_details.append(f"🔴 CRASH START: {message}")
                    lines_captured += 1
                    continue # Skip to next loop to avoid double adding
                
                # 2. Check for process death
                if "process" in msg_lower and "has died" in msg_lower:
                    crash_detected = True
                    crash_details.append(f"💀 PROCESS DIED: {message}")
                    lines_captured += 1
            
            else:
                # We are in "Capture Mode" - grab the stack trace!
                if lines_captured < limit_stack_trace:
                    crash_details.append(message)
                    lines_captured += 1
        
        if crash_details:
            return "\n".join(crash_details)
            
    except Exception as e:
        print(f"Could not retrieve logs (Driver might be disconnected): {e}")
        
    return None

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add Allure attachments on test failure"""
    outcome = yield
    report = outcome.get_result()

    # Check execution phase is 'call' (the actual test run)
    if report.when == "call":
        driver = item.funcargs.get('driver')
        if driver:
            # This is critical for React Native crashes that happen right at the end of a test
            time.sleep(2)
            # 1. Always check for crashes, even if test passed so far
            crash_log = check_for_crashes(driver)
            
            # 2. If crash found, attach logs and force failure
            if crash_log:
                print(f"CRASH DETECTED in {item.nodeid}")
                # print(f"\n--- CRASH LOGS ---\n{crash_log}\n------------------\n")
                allure.attach(
                    crash_log, 
                    name="Crash Logs", 
                    attachment_type=allure.attachment_type.TEXT
                )
                # If test was passing, mark it failed now
                if report.outcome != "failed":
                     report.outcome = "failed"
                     # Set a failure reason so Pytest console shows it clearly
                     report.longrepr = "FAILURE: Application Crash Detected in Logcat"
            
            # 3. Take screenshot if the test is failed (either originally or due to crash)
            if report.outcome == "failed":
                try:
                    screenshot = driver.get_screenshot_as_png()
                    allure.attach(
                        screenshot,
                        name="Failure Screenshot",
                        attachment_type=allure.attachment_type.PNG
                    )
                except Exception as e:
                    print(f"Failed to capture screenshot: {str(e)}")

def notReportFailed(report):
    return report.outcome != "failed"