import os
import pytest
import allure
import time
import sys
from appium import webdriver
from appium.options.android import UiAutomator2Options
import json
from pathlib import Path
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
    parser.addoption("--apk", action="store", default=None, help="Path to the APK file under test")
    parser.addoption("--app-name", action="store", default="Unknown App", help="App name for Jira context")
    parser.addoption("--app-version", action="store", default="Unknown Version", help="App version for Jira context")
    parser.addoption("--developer-name", action="store", default="Unknown Developer", help="Developer name for Jira context")

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
def _extract_feature(item) -> str:
    # Allure decorators become pytest markers like allure_label
    for marker in item.iter_markers(name="allure_label"):
        if marker.kwargs.get("label_type") == "feature":
            if marker.kwargs.get("value"):
                return str(marker.kwargs["value"])
            if marker.args:
                return str(marker.args[0])
    return "Unknown Feature"


def _extract_module(item) -> str:
    name = item.name.lower()
    nodeid = item.nodeid.lower()
    if "login" in name or "login" in nodeid:
        return "Login"
    if "onboarding" in name or "onboarding" in nodeid or "addfarm" in name:
        return "Onboarding"
    if item.cls is not None:
        return item.cls.__name__
    return "Unknown Module"


def _steps_file_for_test(item) -> Path | None:
    test_name = item.name.lower()
    if "login" in test_name:
        return Path("test-flows/login_flow_success.json")
    if "onboarding" in test_name or "addfarm" in test_name:
        return Path("test-flows/onboarding_flow_success.json")
    return None


def _read_steps(item) -> list[str]:
    flow_file = _steps_file_for_test(item)
    if not flow_file or not flow_file.exists():
        return []

    try:
        with flow_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        steps = []
        for entry in data:
            if isinstance(entry, dict) and entry.get("step"):
                steps.append(str(entry["step"]))
            elif isinstance(entry, str):
                steps.append(entry)
        return steps
    except Exception as e:
        print(f"Failed to parse flow steps from {flow_file}: {e}")
        return []

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