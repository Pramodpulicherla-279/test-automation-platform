# tests/conftest.py
"""
Step capture strategy:
  - Use report.capstdout (pytest's own stdout capture of the test)
  - Parse every line that matches [FOUND] name='...' via ...
  - Deduplicate consecutive identical steps
  - No static JSON flow files needed
  - Falls back gracefully to empty list if nothing captured

Other features:
  - issue_id = ISS-001 format
  - developer_name from Jira API
  - description = error text + numbered steps (always)
"""

import os
import sys
import re
import json
import time
import datetime
import requests as http_requests

import re
import pytest
import allure
from pathlib import Path
from appium import webdriver
from appium.options.android import UiAutomator2Options
import sys
sys.dont_write_bytecode = True

RUN_ID_CACHE = None

_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from jira_integration.jira_attachment import attach_screenshot
from jira_integration.jira_config import config

sys.dont_write_bytecode = True

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

_ticket_id:      str  = ""
_issue_counter:  int  = 0
_session_issues: list = []
_developer_name: str  = ""


# ─── Regex patterns for step extraction from stdout ──────────────────────────
# Matches:  [FOUND] name='Next Button (Language)' via XPATH
# Matches:  [FOUND] name="Submit (button in add farm)" via XPATH
_FOUND_RE = re.compile(
    r"\[FOUND\]\s+name=['\"](.+?)['\"]",
    re.IGNORECASE
)
# Matches:  [CLICK] Some element name
_CLICK_RE = re.compile(
    r"\[(?:CLICK|TAP|PRESSED|TAPPED)\]\s+(.+)",
    re.IGNORECASE
)


def _extract_steps_from_stdout(capstdout: str) -> list[str]:
    """
    Parse pytest-captured stdout for [FOUND] and [CLICK] lines.
    Returns a clean, deduplicated list of step descriptions.

    Example input lines:
      [FOUND] name='Next Button (Language)' via XPATH
      [FOUND] name='While using the app (allow picture)' via XPATH
      [FOUND] name='Click Verify OTP' via XPATH   ← may repeat if retried

    Strategy:
      1. Extract label from every matching line
      2. Deduplicate CONSECUTIVE identical steps (retry loops)
      3. Keep non-consecutive repeats (same button clicked multiple screens)
    """
    if not capstdout:
        return []

    raw_steps = []
    for line in capstdout.splitlines():
        line = line.strip()
        m = _FOUND_RE.search(line)
        if m:
            raw_steps.append(m.group(1).strip())
            continue
        m = _CLICK_RE.search(line)
        if m:
            raw_steps.append(m.group(1).strip())

    # Deduplicate CONSECUTIVE identical steps only
    # e.g. ["Click Verify OTP", "Click Verify OTP", "Click Verify OTP", "Android back"]
    #   →  ["Click Verify OTP", "Android back"]
    deduped = []
    for step in raw_steps:
        if not deduped or step != deduped[-1]:
            deduped.append(step)

    return deduped


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _make_ticket_id() -> str:
    return "RUN-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def _make_issue_id() -> str:
    global _issue_counter
    _issue_counter += 1
    return f"ISS-{_issue_counter:03d}"


def _fetch_developer_name_from_jira() -> str:
    if not config.assignee_id:
        return ""
    if not config.url or not config.email or not config.api_token:
        return ""
    try:
        from requests.auth import HTTPBasicAuth
        resp = http_requests.get(
            f"{config.url}/rest/api/3/user",
            params={"accountId": config.assignee_id},
            auth=HTTPBasicAuth(config.email, config.api_token),
            headers={"Accept": "application/json"},
            timeout=8,
        )
        if resp.status_code == 200:
            name = (resp.json() or {}).get("displayName", "")
            if name:
                print(f"[JIRA] Developer name resolved: {name}")
                return name
    except Exception as e:
        print(f"[WARN] Could not fetch Jira user displayName: {e}")
    return ""


# ─── CLI options ──────────────────────────────────────────────────────────────
def pytest_addoption(parser):
    parser.addoption("--apk",            action="store", default=None)
    parser.addoption("--app-name",       action="store", default="Unknown App")
    parser.addoption("--app-version",    action="store", default="Unknown Version")
    parser.addoption("--developer-name", action="store", default="")


def pytest_sessionstart(session):
    global _ticket_id, _issue_counter, _developer_name
    _ticket_id      = _make_ticket_id()
    _issue_counter  = 0
    print(f"\n[TICKET] Session ticket_id: {_ticket_id}")
    _developer_name = _fetch_developer_name_from_jira()
    if _developer_name:
        print(f"[TICKET] Developer: {_developer_name}")


# ─── Driver fixture ───────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def driver(request):
    apk_path = request.config.getoption("--apk")
    if not apk_path:
        pytest.fail("No APK path provided!")
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


# ─── Metadata helpers ─────────────────────────────────────────────────────────
def _cfg(item, option: str, fallback: str) -> str:
    try:
        val = item.config.getoption(option)
        return val if val else fallback
    except Exception:
        return fallback


def _extract_feature(item) -> str:
    for marker in item.iter_markers(name="allure_label"):
        if marker.kwargs.get("label_type") == "feature":
            return str(marker.kwargs.get("value") or (marker.args[0] if marker.args else ""))
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


def _extract_error_only(longrepr) -> str:
    """
    Keeps only the meaningful error lines from pytest longrepr.
    Strips traceback frames — keeps 'E ...' lines and pytest.fail() assertions.
    """
    if not longrepr:
        return "No error details"
    text = str(longrepr)
    lines = text.splitlines()
    error_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("E "):
            error_lines.append(stripped[2:].strip())
        elif "pytest.fail" in stripped or (
            "assert" in stripped.lower()
            and not stripped.startswith("#")
            and not stripped.startswith("import")
        ):
            error_lines.append(stripped)
    # Deduplicate while preserving order
    seen, unique = set(), []
    for l in error_lines:
        if l not in seen:
            seen.add(l)
            unique.append(l)
    return "\n".join(unique) if unique else text.split("\n")[-1].strip() or "Test failed"


def _build_description(error_text: str, steps: list) -> str:
    """
    Final description = error text + numbered steps list.
    Both sections always present when data exists.
    """
    parts = []
    if error_text and error_text.strip() and error_text != "No error details":
        parts.append(error_text.strip())
    if steps:
        steps_block = "\nSteps Executed:\n" + "\n".join(
            f"{i + 1}. {s}" for i, s in enumerate(steps)
        )
        parts.append(steps_block)
    return "\n".join(parts) if parts else "Test failed"


# ─── Crash detection ──────────────────────────────────────────────────────────
def check_for_crashes(driver):
    try:
        logs = driver.get_log("logcat")
        crash_signatures = [
            "fatal exception", "force removing activity", "androidruntime",
            "beginning of crash", "system.err", "am_crash", "anr in",
            "vm aborting", "com.facebook.react.bridge", "jsapplicationillegalargumentexception",
        ]
        crash_lines, capture = [], False
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
    print("JIRA_PAYLOAD_JSON:" + json.dumps(payload, ensure_ascii=False))
    try:
        resp = http_requests.post(
            f"{BACKEND_URL}/api/jira/payload",
            json=payload, timeout=5,
        )
        if resp.status_code == 200:
            print(f"[PAYLOAD SENT] #{payload.get('issue_id')} → {payload.get('module')}")
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

    # 1. Crash detection
    crash_log = check_for_crashes(driver)
    if crash_log:
        print(f"CRASH DETECTED in {item.nodeid}")
        allure.attach(crash_log, name="Crash Logs",
                      attachment_type=allure.attachment_type.TEXT)
        if report.outcome != "failed":
            report.outcome  = "failed"
            report.longrepr = "Application crash detected in logcat"

    if report.outcome != "failed":
        return

    # 2. Screenshot
    try:
        os.makedirs("screenshots", exist_ok=True)
        screenshot_path = f"screenshots/{item.name}.png"
        driver.save_screenshot(screenshot_path)
        allure.attach.file(screenshot_path, name="Failure Screenshot",
                           attachment_type=allure.attachment_type.PNG)
    except Exception as e:
        print("Screenshot capture failed:", e)

    # 3. Metadata
    app_name    = _cfg(item, "--app-name",    "Unknown App")
    app_version = _cfg(item, "--app-version", "Unknown Version")
    module      = _extract_module(item)
    feature     = _extract_feature(item)
    test_name   = item.name
    issue_id    = _make_issue_id()

    developer_name = (
        _developer_name
        or _cfg(item, "--developer-name", "")
        or "Unknown Developer"
    )

    issue_summary = f"Automation Failure: {test_name}"

    # 4. ── STEP EXTRACTION ────────────────────────────────────────────────────
    # Use report.capstdout — pytest captures ALL stdout from the test automatically.
    # This is the most reliable source: no static files, no fixture injection needed.
    # It contains every [FOUND] name='...' line printed by smart_find_element().
    #
    # report.capstdout is set during the "call" phase (the actual test body).
    # If empty (e.g. pytest -s disables capture), fall back gracefully to [].
    steps_executed = _extract_steps_from_stdout(getattr(report, "capstdout", "") or "")

    # 5. Error text
    error_text = _extract_error_only(report.longrepr)

    today      = datetime.date.today()
    start_date = today.isoformat()
    end_date   = (today + datetime.timedelta(days=1)).isoformat()

    # 6. Payload
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
        "steps_executed":  steps_executed,
        "developer_name":  developer_name,
        "start_date":      start_date,
        "end_date":        end_date,
        "sprint":          "Automation",
        "fix_version":     ["Production"],
        "affects_version": [app_name] if app_name and app_name != "Unknown App" else [],
        "description":     _build_description(error_text, steps_executed),
    }

    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name=f"Automation Payload [#{issue_id}]",
        attachment_type=allure.attachment_type.JSON,
    )

    _send_payload_to_backend(payload)
    _session_issues.append({"issue_id": issue_id, "test_name": test_name, "module": module})


# ─── Session finish ───────────────────────────────────────────────────────────
def pytest_sessionfinish(session, exitstatus):
    print(f"\n{'='*50}")
    print(f"TEST SESSION FINISHED  |  Run ID: {_ticket_id}")
    if _session_issues:
        print(f"Failures ({len(_session_issues)}):")
        for iss in _session_issues:
            print(f"  [#{iss['issue_id']}] {iss['module']} — {iss['test_name']}")
    print("Review failures in IssuePanel and click 'Create' to file Jira tickets.")
    print(f"{'='*50}\n")


def notReportFailed(report):
    return report.outcome != "failed"