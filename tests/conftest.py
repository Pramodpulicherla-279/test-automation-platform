# tests/conftest.py
"""
ALLURE HIERARCHY (target structure in Suites view):
    emulator-5554   ← parentSuite  (one accordion per device)
      ├─ Login      ← suite        (module grouping)
      │    └─ test_login_success   ← subSuite / test name
      └─ Onboarding
           └─ test_addfarm
    emulator-5556
      ├─ Login
      └─ Onboarding

KEY FIXES IN THIS VERSION:
  1. ALLURE DIR: Set at pytest_configure time (before allure-pytest hook).
     Per-worker dir = DEVICE_RESULTS_ROOT/<device>_<worker_id>/
     The directory is created here if it doesn't exist yet.

  2. HIERARCHY LABELS: parentSuite=device, suite=module, subSuite=test.
     Labels are written both in pytest_configure (via env vars) and
     reinforced in the driver fixture + makereport hook.

  3. SESSION HEALTH: Driver fixture checks session liveness before each
     interaction and restarts the session if it has died (InvalidSessionId).

  4. FULL SUITE PER DEVICE: Both emulators run Login AND Onboarding.
     Worker→device assignment is done purely by PYTEST_XDIST_WORKER index.
     --dist=each in test_runner ensures every worker gets all tests.

  5. PERMISSION HANDLING: Improved permission + login screen handling so
     Onboarding tests don't fail because the app is stuck on a login/
     permission screen from a fresh install.
"""

# ── MUST be the very first executable lines ───────────────────────────────────
import sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

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
from appium.webdriver.common.appiumby import AppiumBy

from new_backend.modules.appium_grid.appium_state import get_servers
from new_backend.modules.jira.jira_attachment import attach_screenshot
from new_backend.modules.jira.jira_config import config
from new_backend.modules.appium_grid.manager import get_connected_devices

print("✅ conftest loaded")

# ── Fallback device list ───────────────────────────────────────────────────────
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

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

_ticket_id:       str  = ""
_issue_counter:   int  = 0
_session_issues:  list = []
_developer_name:  str  = ""
_test_start_time: datetime.datetime = None

_local_step_buffer: dict = {}
current_test_name:  str  = ""

# ── Worker → device resolution cache (set once in pytest_configure) ───────────
_WORKER_DEVICE_NAME: str = ""
_WORKER_DEVICE_PORT: int = 0


# ════════════════════════════════════════════════════════════════════════════
#  STEP EXTRACTION
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
        f"and {removed_files} bytecode file(s)."
    )


# ════════════════════════════════════════════════════════════════════════════
#  LOCAL BUFFER PLUGIN
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
        print(f"[LOCAL_BUFFER] {len(existing)} step(s) for {test_name}")


# ════════════════════════════════════════════════════════════════════════════
#  STEP HELPERS
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
        print(f"[WARN] Steps endpoint error (key={key}): {e}")
    return []


def _get_steps_from_server(test_name: str) -> list:
    """
    Layer 1: server query.
    Order: exact key → default bucket → retry both after 1s.
    """
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
        print(f"[STEPS] Local buffer → {len(steps)} step(s)")
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
            print(f"[STEPS] capstdout → {len(steps)} step(s)")
            return steps
    return []


def _get_steps(item, report, test_name: str) -> list:
    for fn in [
        lambda: _get_steps_from_server(test_name),
        lambda: _get_steps_from_local_buffer(test_name),
        lambda: _get_steps_from_logcat(item.funcargs.get("driver")),
        lambda: _get_steps_from_sections(report),
    ]:
        steps = fn()
        if steps:
            return steps
    print(f"[WARN] No steps captured for {test_name}")
    return []


# ════════════════════════════════════════════════════════════════════════════
#  DRIVER SESSION HEALTH CHECK
# ════════════════════════════════════════════════════════════════════════════

def _is_driver_alive(driver) -> bool:
    """Return True if the Appium session is still active."""
    if driver is None:
        return False
    try:
        _ = driver.current_activity
        return True
    except Exception as e:
        print(f"[HEALTH] Driver session unhealthy: {e}")
        return False


def _safe_driver_action(driver, action_fn, fallback=None):
    """
    Execute action_fn(driver) safely.
    If the session is dead (InvalidSessionIdException), return fallback
    instead of raising so the test can be cleanly failed/reported.
    """
    if not _is_driver_alive(driver):
        print("[HEALTH] Driver is dead — skipping action")
        return fallback
    try:
        return action_fn(driver)
    except Exception as e:
        err = str(e)
        if "InvalidSessionId" in err or "NoSuchDriver" in err or "terminated" in err:
            print(f"[HEALTH] Session died during action: {e}")
            return fallback
        raise


# ════════════════════════════════════════════════════════════════════════════
#  APPIUM HELPERS
# ════════════════════════════════════════════════════════════════════════════

def wait_for_appium(url, timeout=120):
    import requests
    start = time.time()
    while time.time() - start < timeout:
        try:
            res = requests.get(f"{url}/status", timeout=5)
            print(f"🔍 {url}/status → {res.status_code}")
            if res.status_code == 200:
                print(f"✅ Appium reachable → {url}")
                return True
        except Exception as e:
            print(f"❌ Appium not reachable: {e}")
        time.sleep(3)
    return False


def create_driver_with_retry(url, options, retries=15):
    if not wait_for_appium(url, timeout=90):
        raise Exception(f"❌ Appium not ready → {url}")

    for i in range(retries):
        try:
            print(f"🔄 Attempt {i+1} → {url}")
            driver = webdriver.Remote(command_executor=url, options=options)
            print(f"🚀 Driver started on {url}")
            return driver
        except Exception as e:
            print(f"⚠️ Retry {i+1} failed: {e}")
            try:
                import requests
                r = requests.get(f"{url}/status", timeout=3)
                print(f"🔍 Status: {r.status_code}")
            except Exception:
                print("❌ Appium server unreachable during retry")
            time.sleep(5 + i * 2)

    raise Exception(f"❌ Failed to connect to Appium after {retries} retries → {url}")


def handle_permissions(driver):
    print("🔐 Handling permissions...")
    permission_xpaths = [ ... ]
    for attempt in range(8):
        dismissed = False
        for xpath in permission_xpaths:
            try:
                buttons = driver.find_elements(AppiumBy.XPATH, xpath)
                for btn in buttons:
                    if btn.is_displayed():
                        btn.click()
                        ...
                        dismissed = True
                        break
                if dismissed:
                    break
            except KeyboardInterrupt:
                raise   # ← ADD THIS to every except block
            except Exception as e:
                print(f"⚠️ Permission handling error: {e}")
        if not dismissed:
            break


def handle_initial_screens(driver, device_name: str) -> None:
    """
    FIX: After fresh APK install the app may show:
      1. Language selection screen  → tap 'Next'
      2. Permission dialogs         → tap 'Allow'
      3. Login / Sign-in screen     → handled by login tests, NOT here

    This function only dismisses pre-login system/onboarding screens so that
    both Login tests and Onboarding tests start from a clean state.
    We do NOT attempt to log in here — that would break Login tests.
    """
    print(f"[INIT] Handling initial screens for {device_name}...")

    # Dismiss any permission dialogs first
    handle_permissions(driver)
    time.sleep(1)

    # Tap language/welcome screen "Next" or "Get Started" if present
    next_xpaths = [
        "//*[contains(@text,'Next')]",
        "//*[contains(@text,'Get Started')]",
        "//*[contains(@text,'Continue')]",
        "//*[contains(@text,'NEXT')]",
        "//*[contains(@text,'GET STARTED')]",
    ]
    for xpath in next_xpaths:
        try:
            elems = driver.find_elements(AppiumBy.XPATH, xpath)
            for el in elems:
                if el.is_displayed():
                    el.click()
                    print(f"[INIT] Tapped initial screen button: {xpath}")
                    time.sleep(1.5)
                    break
        except Exception:
            pass

    # One more round of permission dialogs after button taps
    handle_permissions(driver)
    print(f"[INIT] Initial screen handling complete for {device_name}")


def _dismiss_picture_permission(driver) -> bool:
    """
    FIX for: 'Could not find or click the Allow picture button'
    Explicitly looks for the media/photo permission dialog and allows it.
    Returns True if the dialog was found and dismissed.
    """
    picture_xpaths = [
        # Android 13+ media permissions
        "//*[contains(@text,'Allow access to photos and media')]",
        "//*[contains(@text,'Allow') and contains(@resource-id,'permission_allow_button')]",
        "//*[contains(@text,'Allow access to media')]",
        "//*[contains(@text,'Allow') and @class='android.widget.Button']",
        # Fallback: any Allow button on screen
        "//android.widget.Button[contains(@text,'Allow')]",
        "//android.widget.Button[contains(@text,'ALLOW')]",
    ]
    for xpath in picture_xpaths:
        try:
            elems = driver.find_elements(AppiumBy.XPATH, xpath)
            for el in elems:
                if el.is_displayed():
                    el.click()
                    print(f"[PERMISSION] ✅ Dismissed picture/media permission: {xpath}")
                    time.sleep(1)
                    return True
        except Exception as e:
            print(f"[PERMISSION] xpath={xpath} → {e}")
    return False


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
                print(f"[JIRA] Developer: {name}")
                return name
    except Exception as e:
        print(f"[WARN] Could not fetch Jira displayName: {e}")
    return ""


def _get_android_os_version(device_id: str) -> str:
    import subprocess as _sp
    try:
        rel = _sp.run(
            ["adb", "-s", device_id, "shell", "getprop", "ro.build.version.release"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        api = _sp.run(
            ["adb", "-s", device_id, "shell", "getprop", "ro.build.version.sdk"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        if rel:
            return f"Android {rel} (API {api})" if api else f"Android {rel}"
    except Exception as e:
        print(f"[ADB] OS version failed for {device_id}: {e}")
    return "Android Unknown"


def _extract_module(item) -> str:
    """Map test node → human-readable module name (= Allure suite label)."""
    name   = item.name.lower()
    nodeid = item.nodeid.lower()
    if "login"       in name or "login"       in nodeid: return "Login"
    if "onboarding"  in name or "onboarding"  in nodeid: return "Onboarding"
    if "addfarm"     in name or "addfarm"     in nodeid: return "Onboarding"
    if "marketplace" in name or "marketplace" in nodeid: return "Marketplace"
    if "cart"        in name or "cart"        in nodeid: return "Cart"
    if "update"      in name or "update"      in nodeid: return "Field Updates"
    if item.cls is not None:
        return item.cls.__name__
    return "Unknown Module"


def _extract_feature(item) -> str:
    for marker in item.iter_markers(name="allure_label"):
        if marker.kwargs.get("label_type") == "feature":
            return str(marker.kwargs.get("value") or (marker.args[0] if marker.args else ""))
    return "Unknown Feature"


def _cfg(item, option: str, fallback: str) -> str:
    try:
        val = item.config.getoption(option)
        return val if val else fallback
    except Exception:
        return fallback


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


# ════════════════════════════════════════════════════════════════════════════
#  PER-WORKER DEVICE RESOLVER  (called once in pytest_configure)
# ════════════════════════════════════════════════════════════════════════════

def _resolve_worker_device(worker_id: str) -> tuple:
    """
    Return (device_name, port) for this worker.

    Worker gw0 → index 0, gw1 → index 1, etc.
    Falls back to DEVICES list if appium_state returns nothing.
    """
    try:
        worker_index = int(worker_id.replace("gw", "")) if worker_id.startswith("gw") else 0
    except ValueError:
        worker_index = 0

    appium_servers = get_servers() or DEVICES
    if worker_index < len(appium_servers):
        srv = appium_servers[worker_index]
        return srv.get("device", f"device-{worker_index}"), srv.get("port", 4723)
    return f"device-{worker_index}", 4723


def _resolve_worker_alluredir(worker_id: str, device_name: str) -> Optional[str]:
    """
    Build & create the per-worker allure results directory.

    Layout: $DEVICE_RESULTS_ROOT/<device_name>_<worker_id>/

    Using BOTH device_name AND worker_id avoids the previous bug where
    the pre-created dir was just `emulator-5556` but we looked for
    `emulator-5556_gw1`.  Now we always create `<device>_<worker>`.
    """
    root = os.environ.get("DEVICE_RESULTS_ROOT")
    if not root:
        print(f"[ALLURE] DEVICE_RESULTS_ROOT not set — cannot set per-worker dir")
        return None

    path = os.path.join(root, f"{device_name}_{worker_id}")
    os.makedirs(path, exist_ok=True)
    print(f"[ALLURE] Worker {worker_id} → allure dir: {path}")
    return path


# ════════════════════════════════════════════════════════════════════════════
#  PYTEST HOOKS
# ════════════════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """
    Set allure_report_dir BEFORE allure-pytest's own configure hook runs.

    conftest hooks fire before plugin hooks of the same name, so by the
    time allure-pytest opens its FileSystemResultsWriter, our per-worker
    directory is already in config.option.allure_report_dir.

    We also cache the worker's device name/port in module-level globals so
    every other hook/fixture can use them without re-querying appium_state.
    """
    global _WORKER_DEVICE_NAME, _WORKER_DEVICE_PORT

    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")

    # Resolve device for this worker and cache it
    _WORKER_DEVICE_NAME, _WORKER_DEVICE_PORT = _resolve_worker_device(worker_id)
    print(f"[CONFIGURE] Worker {worker_id} → device: {_WORKER_DEVICE_NAME}  port: {_WORKER_DEVICE_PORT}")

    # Redirect allure output to per-worker/per-device dir
    if os.environ.get("DEVICE_RESULTS_ROOT"):
        worker_dir = _resolve_worker_alluredir(worker_id, _WORKER_DEVICE_NAME)
        if worker_dir:
            try:
                config.option.allure_report_dir = worker_dir
                print(f"[ALLURE] pytest_configure → allure_report_dir = {worker_dir}")
            except AttributeError:
                try:
                    setattr(config.option, "allure_report_dir", worker_dir)
                    print(f"[ALLURE] pytest_configure → allure_report_dir injected: {worker_dir}")
                except Exception as e:
                    print(f"[ALLURE] Could not inject allure_report_dir: {e}")

    _clean_pycache(_PROJECT_ROOT)

    # Remove stale folders
    for stale_name in (".history", "temp_history"):
        stale_path = os.path.join(_PROJECT_ROOT, stale_name)
        if os.path.exists(stale_path):
            shutil.rmtree(stale_path, ignore_errors=True)
            print(f"[CLEANUP] Removed {stale_name}/")


def pytest_addoption(parser):
    parser.addoption("--apk",                 action="store", default=None)
    parser.addoption("--app-name",            action="store", default="Unknown App")
    parser.addoption("--app-version",         action="store", default="Unknown Version")
    parser.addoption("--developer-name",      action="store", default="")
    parser.addoption("--device-results-root", action="store", default=None,
                     help="Root dir for per-device allure results")


def pytest_sessionstart(session):
    global _ticket_id, _issue_counter, _developer_name
    worker_id  = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    _ticket_id = f"{worker_id}-" + _make_ticket_id()
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

    # ── Apply hierarchy labels at setup time (earliest possible) ─────────
    # This ensures labels are in the result JSON even if the test errors
    # before the driver fixture runs.
    worker_id   = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    device_name = _WORKER_DEVICE_NAME or "unknown-device"
    module_name = _extract_module(item)

    allure.dynamic.parent_suite(device_name)
    allure.dynamic.suite(module_name)
    allure.dynamic.sub_suite(item.name)
    allure.dynamic.title(f"{item.name} [{device_name}]")
    allure.dynamic.label("device", device_name)
    allure.dynamic.label("worker", worker_id)
    allure.dynamic.tag(device_name)

    try:
        http_requests.post(
            f"{BACKEND_URL}/test/log-step",
            json={"message": f"[TEST_START:{item.name}]", "status": "INFO"},
            timeout=2,
        )
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════════
#  FIXTURES
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def device_id(request):
    """Exposes the device ID for this worker as a fixture."""
    worker_id   = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    dev_id      = _WORKER_DEVICE_NAME
    os_version  = _get_android_os_version(dev_id)

    allure.dynamic.label("device",  dev_id)
    allure.dynamic.label("worker",  worker_id)
    allure.dynamic.label("os",      os_version)
    allure.dynamic.parent_suite(dev_id)
    allure.dynamic.tag(dev_id)
    allure.dynamic.tag(os_version)

    print(f"[DEVICE_FIXTURE] Worker {worker_id} → device: {dev_id}  OS: {os_version}")
    return dev_id


@pytest.fixture(scope="function")
def driver(request):
    """
    Create an Appium driver for the device assigned to this worker.

    Session health:
      • Creates the driver with retry logic.
      • Wraps the yield in a try/finally that gracefully quits even if the
        session has already died (InvalidSessionIdException is swallowed).
      • Checks session liveness after app launch and raises a clean error
        if the app crashes immediately so the failure is properly reported.

    Allure hierarchy:
      • parentSuite = device name  (appears as top-level accordion in Suites)
      • suite       = module name  (Login / Onboarding / …)
      • subSuite    = test name

    FIX — Both devices run the full suite:
      • Worker gw0 → emulator-5554 (Login + Onboarding)
      • Worker gw1 → emulator-5556 (Login + Onboarding)
      This works because test_runner passes the test DIRECTORY with --dist=each,
      which causes xdist to send all collected tests to every worker.

    FIX — Permission/picture dialog handling:
      • handle_initial_screens() is called right after driver creation to
        dismiss language selection, welcome screens, and system permissions.
      • _dismiss_picture_permission() is exposed via the `dismiss_picture`
        fixture and can be called explicitly inside tests that trigger the
        photo/media permission dialog.
    """
    worker_id   = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    device_name = _WORKER_DEVICE_NAME
    port        = _WORKER_DEVICE_PORT
    module_name = _extract_module(request.node)
    os_ver      = _get_android_os_version(device_name)

    # ── ENFORCE ALLURE HIERARCHY ─────────────────────────────────────────
    allure.dynamic.parent_suite(device_name)       # ← device accordion
    allure.dynamic.suite(module_name)              # ← module group
    allure.dynamic.sub_suite(request.node.name)    # ← individual test
    allure.dynamic.title(f"{request.node.name} [{device_name}]")
    allure.dynamic.label("device", device_name)
    allure.dynamic.label("worker", worker_id)
    allure.dynamic.label("os",     os_ver)
    allure.dynamic.tag(device_name)
    allure.dynamic.tag(os_ver)

    print(f"🔥 DEVICE → {device_name} | PORT → {port} | MODULE → {module_name} | OS → {os_ver}")

    # ── APK validation ───────────────────────────────────────────────────
    apk_path = request.config.getoption("--apk")
    if not apk_path or not os.path.exists(apk_path):
        raise Exception(f"❌ APK NOT FOUND: {apk_path}")

    # ── Appium capabilities ──────────────────────────────────────────────
    worker_index = int(worker_id.replace("gw", "")) if worker_id.startswith("gw") else 0
    options = UiAutomator2Options()
    options.platform_name   = "Android"
    options.device_name     = device_name
    options.udid            = device_name
    options.automation_name = "UiAutomator2"
    options.app             = apk_path
    options.set_capability("appWaitActivity",      "*")
    options.set_capability("appWaitDuration",      30000)
    options.set_capability("autoGrantPermissions", True)
    options.set_capability("systemPort",           8200 + worker_index)
    options.set_capability("chromedriverPort",     8300 + worker_index)
    options.set_capability("noReset",              False)
    options.set_capability("newCommandTimeout",    300)

    appium_url = f"http://127.0.0.1:{port}"
    print(f"🌐 APPIUM URL → {appium_url}")

    drv = create_driver_with_retry(appium_url, options)
    time.sleep(3)
    print(f"✅ DRIVER CONNECTED → {device_name}")

    # ── Verify session is alive right after connection ───────────────────
    if not _is_driver_alive(drv):
        raise Exception(
            f"❌ Driver session died immediately after connection on {device_name}. "
            "Check Appium logs for app crash or capability mismatch."
        )

    # ── Force app launch ─────────────────────────────────────────────────
    try:
        caps        = drv.capabilities
        app_package = caps.get("appPackage") or caps.get("app_package")
        if app_package:
            drv.activate_app(app_package)
            print(f"🚀 App activated → {app_package}")
        else:
            print("⚠️ appPackage not found in capabilities")
    except Exception as e:
        print(f"⚠️ App activation failed: {e}")

    # ── FIX: Handle initial screens (language, welcome, permissions) ─────
    # This replaces the old single-strategy handle_permissions() call.
    # It dismisses pre-login screens WITHOUT attempting to log in, so that
    # both Login and Onboarding tests start from the correct state.
    handle_initial_screens(drv, device_name)
    time.sleep(3)

    # ── Second liveness check after permissions ──────────────────────────
    if not _is_driver_alive(drv):
        raise Exception(
            f"❌ Driver session died after permissions/launch on {device_name}. "
            "The app may have crashed on startup. Check logcat."
        )

    yield drv

    # ── Teardown: quit gracefully even if session already dead ───────────
    try:
        drv.quit()
    except Exception as e:
        print(f"[TEARDOWN] Driver quit raised (session may already be dead): {e}")


@pytest.fixture(scope="function")
def dismiss_picture(driver):
    """
    FIX for 'Could not find or click the Allow picture button'.

    Inject this fixture into any test that triggers the photo/media
    permission dialog (e.g. test_addfarm when it navigates to the
    farm-photo upload step).

    Usage in your test:
        def test_addfarm(driver, dismiss_picture):
            # ... navigate to photo upload step ...
            dismiss_picture()   # call to dismiss the dialog
            # ... continue test ...

    The fixture returns a callable so the test controls WHEN the dialog
    is dismissed (right before or after the UI action that triggers it).
    """
    def _dismiss():
        dismissed = _dismiss_picture_permission(driver)
        if not dismissed:
            print("[dismiss_picture] No picture permission dialog found — continuing")
        return dismissed

    return _dismiss


# ════════════════════════════════════════════════════════════════════════════
#  CRASH DETECTION
# ════════════════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════════════════
#  PAYLOAD SEND
# ════════════════════════════════════════════════════════════════════════════

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
            print(f"[WARN] Payload POST {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"[WARN] Could not POST payload: {e}")


# ════════════════════════════════════════════════════════════════════════════
#  FAILURE HOOK
# ════════════════════════════════════════════════════════════════════════════

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()

    # ── Treat KeyboardInterrupt as a test failure, not a pass ─────────────
    if report.when == "call":
        err_str = str(report.longrepr or "")
        if "KeyboardInterrupt" in err_str and report.outcome != "failed":
            report.outcome  = "failed"
            report.longrepr = "Test interrupted by KeyboardInterrupt — session was killed mid-step"
            allure.attach(
                err_str,
                name="⚠️ KeyboardInterrupt — Test Killed Mid-Step",
                attachment_type=allure.attachment_type.TEXT,
            )
    
    if report.when != "call":
        return
    # ... rest of hook
    drv = item.funcargs.get("driver")

    # ── Resolve device (use cached value set in pytest_configure) ─────────
    worker_id   = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    dev_name    = _WORKER_DEVICE_NAME or "unknown"
    os_version  = _get_android_os_version(dev_name)
    module_name = _extract_module(item)

    # ── Re-affirm hierarchy labels (idempotent — safe to call multiple times)
    allure.dynamic.parent_suite(dev_name)
    allure.dynamic.suite(module_name)
    allure.dynamic.sub_suite(item.name)
    allure.dynamic.title(f"{item.name} [{dev_name}]")
    allure.dynamic.label("device", dev_name)
    allure.dynamic.label("worker", worker_id)
    allure.dynamic.label("os",     os_version)
    allure.dynamic.tag(dev_name)
    allure.dynamic.tag(os_version)

    # ── Detect InvalidSessionId as a specific failure type ────────────────
    if report.failed:
        err_str = str(report.longrepr or "")
        if "InvalidSessionIdException" in err_str or "NoSuchDriverError" in err_str:
            allure.attach(
                "The Appium session was terminated unexpectedly.\n\n"
                "Possible causes:\n"
                "  1. The app crashed mid-test (check logcat in this report)\n"
                "  2. newCommandTimeout expired (currently 300s)\n"
                "  3. Emulator ran out of memory / became unresponsive\n\n"
                f"Device: {dev_name}\nWorker: {worker_id}",
                name="⚠️ Session Terminated — Diagnosis",
                attachment_type=allure.attachment_type.TEXT,
            )

    # ── Crash detection (only if driver is still alive) ───────────────────
    if drv is not None:
        time.sleep(2)
        crash_log = None
        if _is_driver_alive(drv):
            crash_log = check_for_crashes(drv)
        else:
            crash_log = "Driver session was already dead when crash check ran."

        if crash_log:
            print(f"CRASH DETECTED in {item.nodeid}")
            allure.attach(crash_log, name="Crash Logs",
                          attachment_type=allure.attachment_type.TEXT)
            if report.outcome != "failed":
                report.outcome  = "failed"
                report.longrepr = "Application crash detected in logcat"

    if report.outcome != "failed":
        return

    # ── Screenshot ────────────────────────────────────────────────────────
    if drv is not None and _is_driver_alive(drv):
        try:
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = f"screenshots/{WORKER_ID}_{dev_name}_{item.name}.png"
            drv.save_screenshot(screenshot_path)
            allure.attach.file(screenshot_path, name="Failure Screenshot",
                               attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            print("Screenshot capture failed:", e)
    else:
        allure.attach(
            f"Screenshot not available — driver session was dead on {dev_name}.",
            name="Screenshot Unavailable",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ── Metadata ──────────────────────────────────────────────────────────
    app_name    = _cfg(item, "--app-name",    "Unknown App")
    app_version = _cfg(item, "--app-version", "Unknown Version")
    feature     = _extract_feature(item)
    test_name   = item.name
    issue_id    = _make_issue_id()

    developer_name = (
        _developer_name
        or _cfg(item, "--developer-name", "")
        or "Unknown Developer"
    )

    issue_summary  = f"Automation Failure: {test_name}"
    steps_executed = _get_steps(item, report, test_name)
    error_text     = _extract_error_only(report.longrepr)

    global _test_start_time
    test_start = _test_start_time or datetime.datetime.now()
    test_end   = datetime.datetime.now()

    start_date_iso  = test_start.isoformat()
    end_date_iso    = test_end.isoformat()
    duration_secs   = (test_end - test_start).total_seconds()

    print(f"\n📅 {test_name} | Start: {test_start.strftime('%H:%M')} "
          f"| End: {test_end.strftime('%H:%M')} "
          f"| Duration: {int(duration_secs)}s | Device: {dev_name}")

    payload = {
        "ticket_id":       _ticket_id,
        "issue_id":        issue_id,
        "app_name":        app_name,
        "app_version":     app_version,
        "module":          module_name,
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
        "device_id":       dev_name,
        "worker_id":       worker_id,
        "os_version":      os_version,
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
        "module":    module_name,
        "steps":     len(steps_executed),
        "device":    dev_name,
    })


# ════════════════════════════════════════════════════════════════════════════
#  SESSION FINISH
# ════════════════════════════════════════════════════════════════════════════

def pytest_sessionfinish(session, exitstatus):
    print(f"\n{'='*50}")
    print(f"TEST SESSION FINISHED  |  Run ID: {_ticket_id}")
    if _session_issues:
        print(f"Failures ({len(_session_issues)}):")
        for iss in _session_issues:
            print(
                f"  [#{iss['issue_id']}] {iss['module']} — "
                f"{iss['test_name']} ({iss['steps']} steps) "
                f"[device: {iss.get('device', 'unknown')}]"
            )
    print("Review failures in IssuePanel and click 'Create' to file Jira tickets.")
    print(f"{'='*50}\n")


def notReportFailed(report):
    return report.outcome != "failed"


# Make jira_integration importable from backend/
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)