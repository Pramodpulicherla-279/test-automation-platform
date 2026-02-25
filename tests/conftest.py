import os
import pytest
import allure
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options

# Import the Jira utility you created
try:
    from tests.utils.jira_utils import create_jira_bug
except ImportError:
    create_jira_bug = None
    print("Warning: tests.utils.jira_utils not found. Jira tickets will not be generated.")

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
    options.set_capability("appium:ignoreHiddenApiPolicyError", True)

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

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add Allure attachments on test failure and Create Jira Tickets"""
    outcome = yield
    report = outcome.get_result()

    # Check execution phase is 'call' (the actual test run)
    if report.when == "call":
        driver = item.funcargs.get('driver')
        crash_log = None
        local_screenshot_path = None

        if driver:
            # This is critical for React Native crashes that happen right at the end of a test
            time.sleep(2)
            # 1. Always check for crashes, even if test passed so far
            crash_log = check_for_crashes(driver)
            
            # 2. If crash found, attach logs and force failure
            if crash_log:
                print(f"CRASH DETECTED in {item.nodeid}")
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
                    # Attach to Allure
                    allure.attach(
                        screenshot,
                        name="Failure Screenshot",
                        attachment_type=allure.attachment_type.PNG
                    )
                    
                    # Save locally so the Jira API can upload it as an attachment
                    os.makedirs("screenshots", exist_ok=True)
                    local_screenshot_path = f"screenshots/{item.name}_failure.png"
                    with open(local_screenshot_path, "wb") as f:
                        f.write(screenshot)
                        
                except Exception as e:
                    print(f"Failed to capture screenshot: {str(e)}")

        # 4. Trigger Jira Automation on Failure
        if report.outcome == "failed" and create_jira_bug:
            print(f"\n--- TEST FAILED: Triggering Jira Creation for {item.name} ---")
            
            # Format the error message for Jira
            if call.excinfo:
                error_message = str(call.excinfo.getrepr(style="short"))
            else:
                error_message = str(getattr(report, "longrepr", "Unknown Application Crash/Failure"))
            
            # Append logcat crash details to the Jira description if they exist
            if crash_log:
                error_message += f"\n\n*Logcat Crash Details:*\n{crash_log}"
                
            # Create the ticket
            create_jira_bug(item.name, error_message, local_screenshot_path)

def notReportFailed(report):
    return report.outcome != "failed"