# tests/conftest.py
"""
Step capture — three-layer strategy (most reliable first):

  1. Query server GET /api/jira/steps/{test_name}
     Falls back to GET /api/jira/steps/default if test_name returns empty.
     Server accumulates [FOUND] lines via /api/log-step in real-time.

  2. report.sections["Captured stdout call"]
     Available when pytest captures stdout internally (non-subprocess mode).

  3. Empty list (steps shown as none)
"""

import os
import sys
import re
import json
import time
import datetime
import requests as http_requests

import pytest
import allure
from appium import webdriver
from appium.options.android import UiAutomator2Options

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


# ─── Regex for parsing [FOUND] lines ─────────────────────────────────────────
_FOUND_RE = re.compile(r"\[FOUND\]\s+name='([^']+)'|\[FOUND\]\s+name=\"([^\"]+)\"", re.IGNORECASE)
_CLICK_RE = re.compile(r"\[(?:CLICK|TAP|PRESSED|TAPPED)\]\s+(.+)", re.IGNORECASE)


def _extract_steps_from_text(text: str) -> list:
    if not text:
        return []
    raw = []
    for line in text.splitlines():
        line = line.strip()
        m = _FOUND_RE.search(line)
        if m:
            step = (m.group(1) or m.group(2) or "").strip()
            if step:
                raw.append(step)
            continue
        m = _CLICK_RE.search(line)
        if m:
            raw.append(m.group(1).strip())
    deduped = []
    for step in raw:
        if not deduped or step != deduped[-1]:
            deduped.append(step)
    return deduped


def _query_steps_endpoint(key: str) -> list:
    """
    Query GET /api/jira/steps/{key} and return the steps list.
    Returns [] on any error or if response has no steps.
    """
    try:
        resp = http_requests.get(
            f"{BACKEND_URL}/api/jira/steps/{key}",
            timeout=4,
        )
        if resp.status_code == 200:
            return resp.json().get("steps", [])
    except Exception as e:
        print(f"[WARN] Could not fetch steps from server (key={key}): {e}")
    return []


def _get_steps_from_server(test_name: str) -> list:
    """
    PRIMARY step source.

    Resolution order:
      1. GET /api/jira/steps/{test_name}   — exact match
      2. GET /api/jira/steps/default       — fallback bucket
         (used when conftest sends no [TEST_START:] tag, so server
          stores all steps under "default")

    Each attempt is retried once with a 1-second delay if empty.
    """
    if not test_name:
        return []

    # ── Attempt 1: exact test_name key ────────────────────────────────────────
    steps = _query_steps_endpoint(test_name)
    if steps:
        print(f"[STEPS] Fetched {len(steps)} steps from server (exact key) for {test_name}")
        return steps

    # ── Attempt 2: "default" fallback bucket ──────────────────────────────────
    steps = _query_steps_endpoint("default")
    if steps:
        print(f"[STEPS] Fetched {len(steps)} steps from server (default bucket) for {test_name}")
        # Tell the server we consumed this bucket so next test starts clean.
        # We do this by posting a dummy step with test_name so the server
        # knows to associate and clear the default bucket via /api/jira/payload.
        # (The actual clear happens server-side in _resolve_steps_for_test.)
        return steps

    # ── Retry both after 1s (handles log-step async queue lag) ────────────────
    time.sleep(1)

    steps = _query_steps_endpoint(test_name)
    if steps:
        print(f"[STEPS] Fetched {len(steps)} steps (exact, retry) for {test_name}")
        return steps

    steps = _query_steps_endpoint("default")
    if steps:
        print(f"[STEPS] Fetched {len(steps)} steps (default, retry) for {test_name}")
        return steps

    return []


def _get_steps_from_sections(report) -> list:
    for header, content in getattr(report, "sections", []):
        if "stdout" in header.lower() and content:
            steps = _extract_steps_from_text(content)
            if steps:
                print(f"[STEPS] Got {len(steps)} steps from report.sections")
                return steps
    cap = getattr(report, "capstdout", "") or ""
    if cap:
        steps = _extract_steps_from_text(cap)
        if steps:
            print(f"[STEPS] Got {len(steps)} steps from report.capstdout")
            return steps
    return []


def _get_steps(item, report, test_name: str) -> list:
    """
    Full step collection pipeline:
    1. Server (exact key + default fallback, with retry)
    2. report.sections / capstdout
    3. Empty list
    """
    steps = _get_steps_from_server(test_name)
    if steps:
        return steps

    steps = _get_steps_from_sections(report)
    if steps:
        return steps

    print(f"[WARN] No steps captured for {test_name}")
    return []


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
    _ticket_id     = _make_ticket_id()
    _issue_counter = 0
    print(f"\n[TICKET] Session ticket_id: {_ticket_id}")
    _developer_name = _fetch_developer_name_from_jira()
    if _developer_name:
        print(f"[TICKET] Developer: {_developer_name}")


# ─── Notify server which test is starting ────────────────────────────────────
# This causes server to bucket subsequent [FOUND] steps under the right key
# instead of "default". Requires new server.py with [TEST_START:] support.
def pytest_runtest_setup(item):
    try:
        http_requests.post(
            f"{BACKEND_URL}/api/log-step",
            json={"message": f"[TEST_START:{item.name}]", "status": "INFO"},
            timeout=2,
        )
    except Exception:
        pass


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
    if not longrepr:
        return "No error details"
    text = str(longrepr)
    error_lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("E "):
            error_lines.append(s[2:].strip())
        elif "pytest.fail" in s or (
            "assert" in s.lower()
            and not s.startswith("#")
            and not s.startswith("import")
        ):
            error_lines.append(s)
    seen, unique = set(), []
    for l in error_lines:
        if l not in seen:
            seen.add(l)
            unique.append(l)
    return "\n".join(unique) if unique else text.split("\n")[-1].strip() or "Test failed"


def _build_description(error_text: str, steps: list) -> str:
    parts = []
    if error_text and error_text.strip() and error_text != "No error details":
        parts.append(error_text.strip())
    if steps:
        parts.append(
            "\nSteps Executed:\n" +
            "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        )
    return "\n".join(parts) if parts else "Test failed"


# ─── Crash detection ──────────────────────────────────────────────────────────
def check_for_crashes(driver):
    try:
        logs = driver.get_log("logcat")
        sigs = [
            "fatal exception", "force removing activity", "androidruntime",
            "beginning of crash", "am_crash", "anr in", "vm aborting",
        ]
        crash_lines, capture = [], False
        for entry in logs:
            msg   = entry.get("message", "")
            lower = msg.lower()
            if not capture:
                if any(s in lower for s in sigs):
                    capture = True
                    crash_lines.append(f"CRASH START: {msg}")
            else:
                if len(crash_lines) < 80:
                    crash_lines.append(msg)
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

    # 4. ── STEP COLLECTION ────────────────────────────────────────────────────
    # Primary:  server exact key → server default bucket (with retry)
    # Fallback: report.sections / capstdout
    steps_executed = _get_steps(item, report, test_name)

    # 5. Error text
    error_text = _extract_error_only(report.longrepr)

    today      = datetime.date.today()
    start_date = today.isoformat()
    end_date   = (today + datetime.timedelta(days=1)).isoformat()

    # 6. Build payload
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
    _session_issues.append({
        "issue_id":  issue_id,
        "test_name": test_name,
        "module":    module,
        "steps":     len(steps_executed),
    })


# ─── Session finish ───────────────────────────────────────────────────────────
def pytest_sessionfinish(session, exitstatus):
    print(f"\n{'='*50}")
    print(f"TEST SESSION FINISHED  |  Run ID: {_ticket_id}")
    if _session_issues:
        print(f"Failures ({len(_session_issues)}):")
        for iss in _session_issues:
            print(f"  [#{iss['issue_id']}] {iss['module']} — {iss['test_name']} ({iss['steps']} steps)")
    print("Review failures in IssuePanel and click 'Create' to file Jira tickets.")
    print(f"{'='*50}\n")


def notReportFailed(report):
    return report.outcome != "failed"