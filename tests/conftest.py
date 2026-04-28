# tests/conftest.py
"""
Step capture — four-layer strategy (most reliable first):

  1. Query server GET /jira/steps/{test_name}  (exact key)
     Falls back to GET /jira/steps/default if test_name returns empty.
  2. Local in-process step buffer (_StepCapturingPlugin reads capstdout live)
  3. Live logcat scrape from device at failure time
  4. report.sections["Captured stdout call"] / capstdout
  (empty list if all fail)

─── STEP CAPTURE FIX ──────────────────────────────────────────────────────────
  Root cause:  _extract_steps_from_text only matched [FOUND] and [CLICK].
               Tests that use [STEP], [ACTION], [TAP], ✅ markers got 0 steps.
  Fix:  Expanded _STEP_PATTERNS to cover all common markers.

─── PYCACHE FIX ────────────────────────────────────────────────────────────────
  Root cause:  Python caches compiled .py → __pycache__/*.pyc.
               Stale .pyc loaded on next run → old Appium config → timeout.
  Fix (3 layers):
    1. sys.dont_write_bytecode = True   — set FIRST, before any import
    2. PYTHONDONTWRITEBYTECODE env var  — covers subprocesses
    3. _clean_pycache() in pytest_configure — wipes existing stale files
       before collection/import starts.

─── JIRA DATES FIX ────────────────────────────────────────────────────────────
  Root cause:  Dates and sprint captured locally but not sent to JIRA API.
  Fix:  Include start_date, end_date, sprint in payload to backend.

─── APPIUM STATE FIX (CRITICAL) ───────────────────────────────────────────────
  Root cause:  `from manager import appium_servers` binds to the list object
               at import time. When manager.py rebinds `appium_servers = servers`
               the conftest reference goes stale (still points to the old list).
               Worse: pytest runs in a SUBPROCESS — in-memory state from the
               parent FastAPI process is never visible to the child.
  Fix:  appium_state.py now writes server list to a temp JSON file via
        set_servers(). get_servers() reads from that file at fixture time,
        so any subprocess always sees the current state.

─── DRIVER FIXTURE FIX ─────────────────────────────────────────────────────────
  Root cause:  Placeholder appPackage/appActivity ("com.your.app") never
               replaced with real values. `app` capability missing → Appium
               can't install the APK. udid not set → wrong device on parallel run.
  Fix:  Use UiAutomator2Options. Set `app` from --apk CLI arg so Appium
        installs the APK automatically. Set `udid` per worker for parallel runs.
────────────────────────────────────────────────────────────────────────────────
"""

# ── MUST be the very first executable lines ───────────────────────────────────
import sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')         # Prevent Python writing NEW .pyc files
import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"   # Propagate to child processes

# ── Standard imports ──────────────────────────────────────────────────────────
import re
import json
import time
import shutil
import datetime
import requests as http_requests
from pathlib import Path
from typing import List, Optional

import pytest
import allure
from appium import webdriver
from appium.options.android import UiAutomator2Options

# FIX: get_servers() reads from a temp JSON file written by the main process,
# so this subprocess always sees the current Appium server list.
from new_backend.modules.appium_grid.appium_state import get_servers
print("✅ conftest loaded")
# ✅ PARALLEL DEVICE CONFIG (fallback if appium_state file is missing)
DEVICES = [
    {"device": "emulator-5554", "port": 4723},
    {"device": "emulator-5556", "port": 4725},
]

WORKER_ID = os.getenv("PYTEST_XDIST_WORKER", "gw0")

RUN_ID_CACHE = None
print("conftest loaded")
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from new_backend.modules.jira.jira_attachment import attach_screenshot
from new_backend.modules.jira.jira_config import config
from new_backend.modules.appium_grid.manager import get_connected_devices

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

_ticket_id:      str  = ""
_issue_counter:  int  = 0
_session_issues: list = []
_developer_name: str  = ""
_test_start_time: datetime.datetime = None  # Track test start time globally

# Per-test local step buffer — populated by _StepCapturingPlugin
_local_step_buffer: dict = {}   # { test_name: [step, ...] }
current_test_name: str  = ""


# ════════════════════════════════════════════════════════════════════════════
#  STEP EXTRACTION — expanded pattern set
# ════════════════════════════════════════════════════════════════════════════

_STEP_PATTERNS: List[tuple] = [
    (re.compile(r"\[FOUND\]\s+name='([^']+)'",   re.IGNORECASE), 1),
    (re.compile(r'\[FOUND\]\s+name="([^"]+)"',   re.IGNORECASE), 1),
    (re.compile(r'\[(?:CLICK|TAP|PRESSED|TAPPED)\]\s+(.+)', re.IGNORECASE), 1),
    (re.compile(r'\[STEP\]\s+(.+)',   re.IGNORECASE), 1),
    (re.compile(r'\[ACTION\]\s+(.+)', re.IGNORECASE), 1),
    (re.compile(r'✅\s+(?:Step\s+)?[–—-]?\s*(.+)', re.IGNORECASE), 1),
]


# ════════════════════════════════════════════════════════════════════════════
#  PYCACHE CLEANUP
# ════════════════════════════════════════════════════════════════════════════
def _clean_pycache(root: str = ".") -> None:
    removed_dirs = removed_files = 0
    for p in Path(root).rglob("__pycache__"):
        try:
            shutil.rmtree(p)
            removed_dirs += 1
        except Exception as exc:
            print(f"[PYCACHE] Could not remove {p}: {exc}")
    for ext in ("*.pyc", "*.pyo"):
        for p in Path(root).rglob(ext):
            try:
                p.unlink()
                removed_files += 1
            except Exception as exc:
                print(f"[PYCACHE] Could not remove {p}: {exc}")
    print(
        f"[PYCACHE] Cleaned {removed_dirs} __pycache__ dir(s) "
        f"and {removed_files} bytecode file(s) before session start."
    )


# ════════════════════════════════════════════════════════════════════════════
#  LOCAL BUFFER PLUGIN — captures steps live from pytest stdout
# ════════════════════════════════════════════════════════════════════════════
class _StepCapturingPlugin:
    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return
        test_name = report.nodeid.split("::")[-1]
        cap = getattr(report, "capstdout", "") or ""
        if not cap:
            return
        steps = _extract_steps_from_text(cap)
        if not steps:
            return
        existing = _local_step_buffer.get(test_name, [])
        for s in steps:
            if s not in existing:
                existing.append(s)
        _local_step_buffer[test_name] = existing
        print(f"[LOCAL_BUFFER] Stored {len(existing)} step(s) for {test_name}")


# ════════════════════════════════════════════════════════════════════════════
#  STEP EXTRACTION HELPERS
# ════════════════════════════════════════════════════════════════════════════
def _extract_steps_from_text(text: str) -> list:
    if not text:
        return []
    raw = []
    for line in text.splitlines():
        line = line.strip()
        for pattern, group in _STEP_PATTERNS:
            m = pattern.search(line)
            if m:
                step = m.group(group).strip()
                if step:
                    raw.append(step)
                break
    deduped = []
    for step in raw:
        if not deduped or step != deduped[-1]:
            deduped.append(step)
    return deduped


def _query_steps_endpoint(key: str) -> list:
    try:
        resp = http_requests.get(f"{BACKEND_URL}/jira/steps/{key}", timeout=4)
        if resp.status_code == 200:
            return resp.json().get("steps", [])
    except Exception as e:
        print(f"[WARN] Could not fetch steps from server (key={key}): {e}")
    return []


def wait_for_appium(url, timeout=60):
    import requests
    start = time.time()

    while time.time() - start < timeout:
        try:
            res = requests.get(f"{url}/status", timeout=3)
            data = res.json()

            # ✅ Check FULL readiness
            if (
                res.status_code == 200 and
                data.get("value", {}).get("ready", False)
            ):
                print(f"✅ Appium FULLY ready → {url}")
                return True

        except Exception:
            pass

        print(f"⏳ Waiting for FULL Appium readiness → {url}")
        time.sleep(3)

    return False


def create_driver_with_retry(url, options, retries=10):
    # ✅ NEW: wait before retry loop
    if not wait_for_appium(url):
        raise Exception(f"❌ Appium not ready after wait → {url}")

    for i in range(retries):
        try:
            print(f"🔄 Attempt {i+1} connecting to {url}")
            driver = webdriver.Remote(url, options=options, keep_alive=False)
            print(f"🚀 DRIVER STARTED on {url}")
            return driver
        except Exception as e:
            print(f"⚠️ Retry {i+1} failed: {e}")
            time.sleep(5 + i * 2)  # exponential backoff

    raise Exception(f"❌ Failed to connect to Appium after {retries} retries → {url}")


def _get_steps_from_server(test_name: str) -> list:
    if not test_name:
        return []
    steps = _query_steps_endpoint(test_name)
    if steps:
        print(f"[STEPS] Server exact → {len(steps)} step(s) for {test_name}")
        return steps
    steps = _query_steps_endpoint("default")
    if steps:
        print(f"[STEPS] Server default → {len(steps)} step(s) for {test_name}")
        return steps
    time.sleep(1)
    steps = _query_steps_endpoint(test_name)
    if steps:
        print(f"[STEPS] Server exact (retry) → {len(steps)} step(s) for {test_name}")
        return steps
    steps = _query_steps_endpoint("default")
    if steps:
        print(f"[STEPS] Server default (retry) → {len(steps)} step(s) for {test_name}")
        return steps
    return []


def _get_steps_from_local_buffer(test_name: str) -> list:
    steps = _local_step_buffer.get(test_name, [])
    if steps:
        print(f"[STEPS] Local buffer → {len(steps)} step(s) for {test_name}")
    return steps


def _get_steps_from_logcat(driver_obj) -> list:
    if not driver_obj:
        return []
    try:
        logs   = driver_obj.get_log("logcat")
        joined = "\n".join(entry.get("message", "") for entry in logs)
        steps  = _extract_steps_from_text(joined)
        if steps:
            print(f"[STEPS] Logcat → {len(steps)} step(s)")
        return steps
    except Exception as e:
        print(f"[STEPS] Logcat scrape failed: {e}")
        return []


def _get_steps_from_sections(report) -> list:
    for header, content in getattr(report, "sections", []):
        if "stdout" in header.lower() and content:
            steps = _extract_steps_from_text(content)
            if steps:
                print(f"[STEPS] report.sections → {len(steps)} step(s)")
                return steps
    cap = getattr(report, "capstdout", "") or ""
    if cap:
        steps = _extract_steps_from_text(cap)
        if steps:
            print(f"[STEPS] report.capstdout → {len(steps)} step(s)")
            return steps
    return []


def _get_steps(item, report, test_name: str) -> list:
    steps = _get_steps_from_server(test_name)
    if steps:
        return steps
    steps = _get_steps_from_local_buffer(test_name)
    if steps:
        return steps
    driver_obj = item.funcargs.get("driver")
    steps = _get_steps_from_logcat(driver_obj)
    if steps:
        return steps
    steps = _get_steps_from_sections(report)
    if steps:
        return steps
    print(f"[WARN] No steps captured for {test_name}")
    return []


# ════════════════════════════════════════════════════════════════════════════
#  GENERAL HELPERS
# ════════════════════════════════════════════════════════════════════════════
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


# ════════════════════════════════════════════════════════════════════════════
#  PYTEST HOOKS
# ════════════════════════════════════════════════════════════════════════════
def pytest_configure(config):
    _clean_pycache(_PROJECT_ROOT)
    print("[PYCACHE] sys.dont_write_bytecode =", sys.dont_write_bytecode)
    print("[PYCACHE] PYTHONDONTWRITEBYTECODE  =",
          os.environ.get("PYTHONDONTWRITEBYTECODE", "NOT SET"))
    config.pluginmanager.register(_StepCapturingPlugin(), "step_buffer_plugin")


def pytest_addoption(parser):
    parser.addoption("--apk",            action="store", default=None)
    parser.addoption("--app-name",       action="store", default="Unknown App")
    parser.addoption("--app-version",    action="store", default="Unknown Version")
    parser.addoption("--developer-name", action="store", default="")


def pytest_sessionstart(session):
    global _ticket_id, _issue_counter, _developer_name
    _ticket_id = f"{WORKER_ID}-" + _make_ticket_id()
    _issue_counter = 0
    print(f"\n[TICKET] Session ticket_id: {_ticket_id}")
    _developer_name = _fetch_developer_name_from_jira()
    if _developer_name:
        print(f"[TICKET] Developer: {_developer_name}")


def pytest_runtest_setup(item):
    global current_test_name, _test_start_time
    current_test_name = item.name
    _test_start_time  = datetime.datetime.now()
    _local_step_buffer.setdefault(item.name, [])

    try:
        http_requests.post(
            f"{BACKEND_URL}/test/log-step",
            json={"message": f"[TEST_START:{item.name}]", "status": "INFO"},
            timeout=2,
        )
    except Exception:
        pass


# ── Driver fixture ────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def driver(request):

    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    worker_index = int(worker_id.replace("gw", ""))
    # ✅ Prevent both workers hitting Appium at same time
    time.sleep(worker_index * 10)

    print(f"\n🧵 WORKER → {worker_id}")

    appium_servers = get_servers()

    if not appium_servers:
        print("⚠️ Using fallback DEVICES list")
        appium_servers = DEVICES

    print(f"📱 SERVERS → {appium_servers}")

    if worker_index >= len(appium_servers):
       raise Exception("❌ More workers than devices")

    device = appium_servers[worker_index]
    port = device["port"]

    print(f"🔥 DEVICE → {device['device']} | PORT → {port}")

    apk_path = request.config.getoption("--apk")

    if not apk_path or not os.path.exists(apk_path):
        raise Exception(f"❌ APK NOT FOUND: {apk_path}")

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = device["device"]
    options.udid = device["device"]
    options.automation_name = "UiAutomator2"

    options.app = apk_path
    options.no_reset = False
    options.auto_grant_permissions = True

    options.set_capability("systemPort", 8200 + worker_index)

    appium_url = f"http://127.0.0.1:{port}"

    print("\n" + "="*50)
    print(f"🌐 Connecting to Appium → {appium_url}")
    print(f"🧵 Worker → {worker_id}")
    print(f"📱 Device → {device['device']}")
    print(f"🔌 Port → {port}")
    print("="*50 + "\n")
    print(f"📱 Device → {device['device']}")
    print(f"📦 APK → {apk_path}")
    
    driver = create_driver_with_retry(appium_url, options)
    
    print(f"✅ DRIVER CONNECTED → {device['device']}")

    yield driver

    try:
        driver.quit()
    except:
        pass


# ── Metadata helpers ──────────────────────────────────────────────────────────
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
    error_lines, seen, unique = [], set(), []
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


# ── Crash detection ───────────────────────────────────────────────────────────
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


# ── Send payload to backend ───────────────────────────────────────────────────
def _send_payload_to_backend(payload: dict) -> None:
    print("JIRA_PAYLOAD_JSON:" + json.dumps(payload, ensure_ascii=False))
    try:
        resp = http_requests.post(
            f"{BACKEND_URL}/jira/payload",
            json=payload, timeout=5,
        )
        if resp.status_code == 200:
            print(f"[PAYLOAD SENT] #{payload.get('issue_id')} → {payload.get('module')}")
        else:
            print(f"[WARN] Payload POST returned {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"[WARN] Could not POST payload to backend: {e}")


# ── Failure hook ──────────────────────────────────────────────────────────────
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
        screenshot_path = f"screenshots/{WORKER_ID}_{item.name}.png"
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

    # 4. Step collection
    steps_executed = _get_steps(item, report, test_name)

    # 5. Error text
    error_text = _extract_error_only(report.longrepr)

    # ── Capture accurate test execution dates ──────────────────────────────
    global _test_start_time

    test_start = _test_start_time or datetime.datetime.now()
    test_end   = datetime.datetime.now()

    start_date_iso      = test_start.isoformat()
    end_date_iso        = test_end.isoformat()
    start_date_readable = test_start.strftime('%d/%m/%Y, %H:%M')
    end_date_readable   = test_end.strftime('%d/%m/%Y, %H:%M')
    duration_seconds    = (test_end - test_start).total_seconds()
    duration_readable   = f"{int(duration_seconds)} seconds"

    print(f"\n📅 Test Execution Timeline:")
    print(f"   Start:    {start_date_readable} (ISO: {start_date_iso})")
    print(f"   End:      {end_date_readable} (ISO: {end_date_iso})")
    print(f"   Duration: {duration_readable}")
    print(f"   Steps:    {len(steps_executed)}")

    # ── Build payload ──────────────────────────────────────────────────────
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
        "description":     _build_description(error_text, steps_executed),
        "start_date":      start_date_iso,
        "end_date":        end_date_iso,
        "sprint":          "Automation",
        "fix_version":     ["Production"],
        "affects_version": [app_name] if app_name and app_name != "Unknown App" else [],
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


# ── Session finish ────────────────────────────────────────────────────────────
def pytest_sessionfinish(session, exitstatus):
    print(f"\n{'='*50}")
    print(f"TEST SESSION FINISHED  |  Run ID: {_ticket_id}")
    if _session_issues:
        print(f"Failures ({len(_session_issues)}):")
        for iss in _session_issues:
            print(
                f"  [#{iss['issue_id']}] {iss['module']} — "
                f"{iss['test_name']} ({iss['steps']} steps)"
            )
    print("Review failures in IssuePanel and click 'Create' to file Jira tickets.")
    print(f"{'='*50}\n")


def notReportFailed(report):
    return report.outcome != "failed"


# Make jira_integration importable from backend/
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)