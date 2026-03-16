# tests/conftest.py
"""
Original conftest.py with one change:
  - Removed direct create_jira_issue() call on test failure
  - Instead: builds full payload and POSTs to /api/jira/payload
  - Also prints JIRA_PAYLOAD_JSON: for console visibility
  - User clicks "Create" in IssuePanel to create the Jira ticket
"""

import os
import sys
import json
import time
import datetime
import requests as http_requests
from pathlib import Path

import pytest
import allure
from appium import webdriver
from appium.options.android import UiAutomator2Options

# sys.path fix — must come before local imports
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from jira_integration.jira_attachment import attach_screenshot
from jira_integration.jira_config import config

sys.dont_write_bytecode = True

# Backend URL — where /api/jira/payload lives
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Session-level IDs
_ticket_id:      str = ""
_issue_counter:  int = 0
_session_issues: list[dict] = []


def _make_ticket_id() -> str:
    return "RUN-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def _make_issue_id() -> str:
    global _issue_counter
    _issue_counter += 1
    return f"ISS-{_issue_counter:03d}"


# ─── CLI options (unchanged) ──────────────────────────────────────────────────
def pytest_addoption(parser):
    parser.addoption("--apk",            action="store", default=None,
                     help="Path to the APK file under test")
    parser.addoption("--app-name",       action="store", default="Unknown App",
                     help="App name for Jira context")
    parser.addoption("--app-version",    action="store", default="Unknown Version",
                     help="App version for Jira context")
    parser.addoption("--developer-name", action="store", default="Unknown Developer",
                     help="Developer name for Jira context")


# ─── Session start ────────────────────────────────────────────────────────────
def pytest_sessionstart(session):
    global _ticket_id, _issue_counter
    _ticket_id     = _make_ticket_id()
    _issue_counter = 0
    print(f"\n[TICKET] Session ticket_id: {_ticket_id}")


# ─── Driver fixture (unchanged) ───────────────────────────────────────────────
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
    options.device_name   = "AndroidDevice"
    options.app           = apk_path
    options.set_capability("appium:ignoreHiddenApiPolicyError", True)

    drv = webdriver.Remote("http://127.0.0.1:4723", options=options)
    try:
        drv.get_log("logcat")
    except Exception:
        pass

    yield drv
    drv.quit()


# ─── Metadata helpers (unchanged) ─────────────────────────────────────────────
def _cfg(item, option: str, fallback: str) -> str:
    try:
        val = item.config.getoption(option)
        return val if val else fallback
    except Exception:
        return fallback


def _extract_feature(item) -> str:
    for marker in item.iter_markers(name="allure_label"):
        if marker.kwargs.get("label_type") == "feature":
            if marker.kwargs.get("value"):
                return str(marker.kwargs["value"])
            if marker.args:
                return str(marker.args[0])
    return "Unknown Feature"


def _extract_module(item) -> str:
    name   = item.name.lower()
    nodeid = item.nodeid.lower()
    if "login"       in name or "login"       in nodeid: return "Login"
    if "onboarding"  in name or "onboarding"  in nodeid: return "Onboarding"
    if "addfarm"     in name or "addfarm"     in nodeid: return "Onboarding"
    if "marketplace" in name or "marketplace" in nodeid: return "Marketplace"
    if "cart"        in name or "cart"        in nodeid: return "Cart"
    if item.cls is not None:
        return item.cls.__name__
    return "Unknown Module"


def _steps_file_for_test(item) -> Path | None:
    test_name = item.name.lower()
    if "login"      in test_name: return Path("test-flows/login_flow_success.json")
    if "onboarding" in test_name: return Path("test-flows/onboarding_flow_success.json")
    if "addfarm"    in test_name: return Path("test-flows/onboarding_flow_success.json")
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
        print(f"Failed to parse flow steps: {e}")
        return []


# ─── Crash detection (unchanged) ──────────────────────────────────────────────
def check_for_crashes(driver):
    try:
        logs = driver.get_log("logcat")
        crash_signatures = [
            "fatal exception", "force removing activity", "androidruntime",
            "beginning of crash", "system.err", "am_crash", "anr in",
            "vm aborting", "com.facebook.react.bridge", "jsapplicationillegalargumentexception",
        ]
        crash_lines = []
        capture = False
        for entry in logs:
            message = entry.get("message", "")
            lower   = message.lower()
            if not capture:
                if any(sig in lower for sig in crash_signatures):
                    capture = True
                    crash_lines.append(f"CRASH START: {message}")
            else:
                if len(crash_lines) < 80:
                    crash_lines.append(message)
        return "\n".join(crash_lines) if crash_lines else None
    except Exception as e:
        print("Logcat crash detection failed:", e)
        return None


# ─── Send payload to backend ──────────────────────────────────────────────────
def _send_payload_to_backend(payload: dict) -> None:
    """
    POST to /api/jira/payload — server stores it and broadcasts JIRA_PAYLOAD
    via WebSocket so IssuePanel auto-populates.
    Also print JIRA_PAYLOAD_JSON: so test_runner.send_log() picks it up too.
    """
    # Print for console + test_runner log pipeline fallback
    print("JIRA_PAYLOAD_JSON:" + json.dumps(payload, ensure_ascii=False))

    # Direct HTTP POST — primary path
    try:
        resp = http_requests.post(
            f"{BACKEND_URL}/api/jira/payload",
            json=payload,
            timeout=5,
        )
        if resp.status_code == 200:
            print(f"[PAYLOAD SENT] {payload.get('issue_id')} → {payload.get('module')}")
        else:
            print(f"[WARN] Payload POST returned {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"[WARN] Could not POST payload to backend: {e}")


# ─── Failure hook ─────────────────────────────────────────────────────────────
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()

    if report.when != "call":
        return

    driver = item.funcargs.get("driver")
    if not driver:
        return

    time.sleep(2)

    # 1. Detect App Crash
    crash_log = check_for_crashes(driver)

    if crash_log:
        print(f"CRASH DETECTED in {item.nodeid}")
        allure.attach(crash_log, name="Crash Logs",
                      attachment_type=allure.attachment_type.TEXT)
        if report.outcome != "failed":
            report.outcome  = "failed"
            report.longrepr = "Application crash detected in logcat"

    # Only proceed for failed tests
    if report.outcome != "failed":
        return

    # 2. Capture Screenshot
    screenshot_path = None
    try:
        os.makedirs("screenshots", exist_ok=True)
        screenshot_path = f"screenshots/{item.name}.png"
        driver.save_screenshot(screenshot_path)
        allure.attach.file(screenshot_path, name="Failure Screenshot",
                           attachment_type=allure.attachment_type.PNG)
    except Exception as e:
        print("Screenshot capture failed:", e)

    # 3. Collect metadata
    app_name       = _cfg(item, "--app-name",       "Unknown App")
    app_version    = _cfg(item, "--app-version",    "Unknown Version")
    developer_name = _cfg(item, "--developer-name", "Unknown Developer")
    module         = _extract_module(item)
    feature        = _extract_feature(item)
    test_name      = item.name
    test_id        = item.nodeid
    issue_summary  = f"Automation Failure: {test_name}"
    steps_executed = _read_steps(item)
    error_text     = str(report.longrepr or "No error details")
    issue_id       = _make_issue_id()

    # 4. Build payload
    payload = {
        "ticket_id":       _ticket_id,
        "issue_id":        issue_id,
        "app_name":        app_name,
        "app_version":     app_version,
        "module":          module,
        "feature":         feature,
        "issue_summary":   issue_summary,
        "title":           issue_summary,
        "test_name":       test_name,
        "test_id":         test_id,
        "steps_executed":  steps_executed,
        "developer_name":  developer_name,
        "description": (
            f"Automation Test Failure\n\n"
            f"Run ID: {_ticket_id}\n"
            f"Issue ID: {issue_id}\n\n"
            f"App: {app_name}\n"
            f"App Version: {app_version}\n"
            f"Module: {module}\n"
            f"Feature: {feature}\n"
            f"Developer: {developer_name}\n"
            f"Test: {test_name}\n"
            f"Test ID: {test_id}\n\n"
            f"Error:\n{error_text}\n\n"
            f"Environment:\n{app_name} APK"
        ),
    }

    # 5. Attach to Allure
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name=f"Automation Payload [{issue_id}]",
        attachment_type=allure.attachment_type.JSON,
    )

    # 6. Send to backend → IssuePanel auto-populates
    #    NO automatic Jira ticket creation — user clicks "Create" in IssuePanel
    _send_payload_to_backend(payload)

    _session_issues.append({
        "issue_id":  issue_id,
        "test_name": test_name,
        "module":    module,
    })


# ─── Session finish summary (unchanged) ───────────────────────────────────────
def pytest_sessionfinish(session, exitstatus):
    print(f"\n{'='*50}")
    print(f"TEST SESSION FINISHED  |  Run ID: {_ticket_id}")
    if _session_issues:
        print(f"Failures ({len(_session_issues)}):")
        for iss in _session_issues:
            print(f"  [{iss['issue_id']}] {iss['module']} — {iss['test_name']}")
    print("Review failures in IssuePanel and click 'Create' to file Jira tickets.")
    print(f"{'='*50}\n")


# ─── Utility (unchanged) ──────────────────────────────────────────────────────
def notReportFailed(report):
    return report.outcome != "failed"