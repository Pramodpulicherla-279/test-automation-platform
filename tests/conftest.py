import os
import pytest
import allure
import time
import sys
from appium import webdriver
from appium.options.android import UiAutomator2Options

from jira_integration.jira_service import create_jira_issue
from jira_integration.jira_attachment import attach_screenshot
from jira_integration.jira_config import config

sys.dont_write_bytecode = True


# -----------------------------------------------------------
# Global Jira Ticket Tracker
# -----------------------------------------------------------

created_jira_tickets = []


# -----------------------------------------------------------
# Pytest CLI option
# -----------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--apk",
        action="store",
        default=None,
        help="Path to the APK file under test",
    )


# -----------------------------------------------------------
# Driver Fixture
# -----------------------------------------------------------

@pytest.fixture(scope="session")
def driver(request):

    apk_path = request.config.getoption("--apk")

    if not apk_path:
        pytest.fail("No APK path provided! Backend must call pytest with --apk=/path/to/app.apk")

    if not os.path.exists(apk_path):
        pytest.fail(f"APK file not found at: {apk_path}")

    print(f"Initializing Appium with APK: {apk_path}")

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "AndroidDevice"
    options.app = apk_path
    options.set_capability("appium:ignoreHiddenApiPolicyError", True)

    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

    try:
        driver.get_log("logcat")
    except Exception:
        pass

    yield driver

    driver.quit()


# -----------------------------------------------------------
# Crash Detection
# -----------------------------------------------------------

def check_for_crashes(driver):

    try:

        logs = driver.get_log("logcat")

        crash_signatures = [
            "fatal exception",
            "force removing activity",
            "androidruntime",
            "beginning of crash",
            "system.err",
            "am_crash",
            "anr in",
            "vm aborting",
            "com.facebook.react.bridge",
            "jsapplicationillegalargumentexception",
        ]

        crash_lines = []
        capture = False
        limit = 80

        for entry in logs:

            message = entry.get("message", "")
            lower = message.lower()

            if not capture:
                if any(sig in lower for sig in crash_signatures):
                    capture = True
                    crash_lines.append(f"CRASH START: {message}")
                    continue

            else:
                if len(crash_lines) < limit:
                    crash_lines.append(message)

        if crash_lines:
            return "\n".join(crash_lines)

    except Exception as e:
        print("Logcat crash detection failed:", e)

    return None


# -----------------------------------------------------------
# Pytest Failure Hook
# -----------------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    driver = item.funcargs.get("driver")

    if not driver:
        return

    time.sleep(2)

    # -------------------------------------------------------
    # 1️⃣ Detect App Crash
    # -------------------------------------------------------

    crash_log = check_for_crashes(driver)

    if crash_log:

        print(f"CRASH DETECTED in {item.nodeid}")

        allure.attach(
            crash_log,
            name="Crash Logs",
            attachment_type=allure.attachment_type.TEXT
        )

        if report.outcome != "failed":
            report.outcome = "failed"
            report.longrepr = "Application crash detected in logcat"


    # -------------------------------------------------------
    # 2️⃣ If Test Failed → Capture Screenshot
    # -------------------------------------------------------

    if report.outcome == "failed":

        screenshot_path = None

        try:

            os.makedirs("screenshots", exist_ok=True)

            screenshot_path = f"screenshots/{item.name}.png"

            driver.save_screenshot(screenshot_path)

            allure.attach.file(
                screenshot_path,
                name="Failure Screenshot",
                attachment_type=allure.attachment_type.PNG
            )

        except Exception as e:
            print("Screenshot capture failed:", e)


        # ---------------------------------------------------
        # 3️⃣ Create Jira Bug
        # ---------------------------------------------------

        if config.enabled:

            try:

                issue_key = create_jira_issue(
                    summary=f"Automation Failure: {item.name}",
                    description=f"""
Automation Test Failure

Test Case:
{item.nodeid}

Error:
{report.longrepr}

Environment:
Krishivaas Farmer APK
"""
                )

                if issue_key:

                    print(f"JIRA ISSUE CREATED: {issue_key}")

                    created_jira_tickets.append(issue_key)

                    # attach jira link to allure
                    allure.attach(
                        f"{config.url}/browse/{issue_key}",
                        name="Jira Ticket",
                        attachment_type=allure.attachment_type.URI_LIST
                    )

                    if screenshot_path:
                        attach_screenshot(issue_key, screenshot_path)

            except Exception as e:
                print("Jira integration error:", e)


# -----------------------------------------------------------
# Print Jira Links After Test Execution
# -----------------------------------------------------------

def pytest_sessionfinish(session, exitstatus):

    if created_jira_tickets:

        print("\n====================================")
        print("JIRA TICKETS CREATED DURING TEST RUN")
        print("====================================")

        for key in created_jira_tickets:
            print(f"{key} → {config.url}/browse/{key}")

        print("\nView all automation bugs:")
        print(f"{config.url}/issues/?jql=project={config.project_key}+AND+labels=automation")

        print("====================================")


# -----------------------------------------------------------
# Helper
# -----------------------------------------------------------

def notReportFailed(report):
    return report.outcome != "failed"