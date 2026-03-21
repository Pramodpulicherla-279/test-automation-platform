# tests/conftest.py
"""
Changes:
  1. test_id removed — replaced by sequential issue_id (ISS-001, ISS-002…)
  2. developer_name fetched from Jira API using JIRA_ASSIGNEE_ACCOUNT_ID
  3. description shows only the error text (not full metadata block)
  4. start_date, end_date, sprint, fix_version, affects_version included
"""

import os
import re
import pytest
import allure
import time
from pathlib import Path
from appium import webdriver
from appium.options.android import UiAutomator2Options
import sys
sys.dont_write_bytecode = True

RUN_ID_CACHE = None

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

    # NEW: where to store screenshots for UI parser (LLM)
    parser.addoption(
        "--ui-screenshots-dir",
        action="store",
        default=None,
        help="Directory to store UI screenshots for analysis (not Allure).",
    )

    # NEW: group screenshots by run id (backend should pass a unique id per run)
    parser.addoption(
        "--run-id",
        action="store",
        default=None,
        help="Run identifier used to group artifacts (screenshots/logs).",
    )


def _safe_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "_", s)
    return s[:160] if len(s) > 160 else s

def _get_test_id(nodeid: str) -> str:
    """
    Stable folder name for a test.
    Example nodeid: tests/test_cases/.../test_login_pytest.py::TestLogin::test_login_success
    """
    return _safe_name(nodeid)

def _get_run_ui_dir(config) -> Path:
    """
    Single folder for ALL screenshots of this run.
    artifacts/ui_screenshots/<run_id>/
    """
    run_id = _get_run_id(config)
    base = _get_ui_screenshots_root(config) / run_id
    base.mkdir(parents=True, exist_ok=True)
    return base

def _build_ui_screenshot_path(config, nodeid: str, name: str) -> Path:
    base_dir = _get_run_ui_dir(config)

    ts = time.strftime("%H%M%S")
    test_id = _get_test_id(nodeid)

    filename = f"{ts}__{test_id}__{_safe_name(name)}.png"

    return base_dir / filename

def _get_run_id(config) -> str:
    global RUN_ID_CACHE

    if RUN_ID_CACHE:
        return RUN_ID_CACHE

    rid = config.getoption("--run-id") or os.getenv("RUN_ID")

    if rid:
        RUN_ID_CACHE = _safe_name(rid)
    else:
        RUN_ID_CACHE = time.strftime("%Y%m%d-%H%M%S")

    return RUN_ID_CACHE

def _get_ui_screenshots_root(config) -> Path:
    # precedence: CLI > env > default under repo root
    custom = config.getoption("--ui-screenshots-dir") or os.getenv("UI_SCREENSHOTS_DIR")
    if custom:
        return Path(custom)

    # pytest root (repo root) + artifacts folder
    root = Path(getattr(config, "rootpath", Path.cwd()))
    return root / "artifacts" / "ui_screenshots"


def _save_ui_screenshot(driver, config, nodeid: str, name: str) -> str | None:
    """
    Save screenshot to disk (for UI parser), return absolute path (string) or None on failure.
    This does NOT attach to Allure.
    """
    try:
        path = _build_ui_screenshot_path(config, nodeid, name)
        ok = driver.get_screenshot_as_file(str(path))
        return str(path.resolve()) if ok else None
    except Exception as e:
        print(f"[ui_screenshots] Failed to save screenshot: {e}")
        return None
    
@pytest.fixture(autouse=True)
def _bind_ui_shot_to_driver(request):
    """
    Binds:
      - driver.ui_shot(name): takes screenshot into <run_id>/<test_id>/
      - driver.ui_shot_path(name): returns a file path inside <run_id>/<test_id>/ (no capture)
    """
    if "driver" not in request.fixturenames:
        yield
        return

    driver = request.getfixturevalue("driver")
    nodeid = request.node.nodeid
    config = request.config

    def _shot(name: str = "screen"):
        return _save_ui_screenshot(driver, config, nodeid, name)

    def _shot_path(name: str = "screen") -> str:
        return str(_build_ui_screenshot_path(config, nodeid, name))

    setattr(driver, "ui_shot", _shot)
    setattr(driver, "ui_shot_path", _shot_path)

    yield

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

    yield driver

    driver.quit()

# NEW: fixture for tests to capture screenshots at every screen/step
@pytest.fixture
def ui_shot(request, driver):
    """
    Usage in tests:
        def test_flow(driver, ui_shot):
            ui_shot("login_screen")
            ... navigate ...
            ui_shot("home_screen")
    """
    def _take(name: str = "screen"):
        return _save_ui_screenshot(driver, request.config, request.node.nodeid, name)
    return _take

def check_for_crashes(driver):
    """
    Retrieves logcat logs and looks for crash signatures.
    If a crash is detected, it captures the surrounding log lines (stack trace) 
    to provide meaningful context.
    """
    if not longrepr:
        return "No error details"
    text = str(longrepr)
    lines = text.splitlines()
    error_lines = []
    for line in lines:
        stripped = line.strip()
        # Keep lines starting with 'E ' (pytest error lines)
        if stripped.startswith("E "):
            error_lines.append(stripped[2:].strip())
        # Keep the last 'pytest.fail(...)' or assertion line
        elif "pytest.fail" in stripped or "assert" in stripped.lower():
            error_lines.append(stripped)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for l in error_lines:
        if l not in seen:
            seen.add(l)
            unique.append(l)
    return "\n".join(unique) if unique else text.split("\n")[-1].strip() or "Test failed"


# ─── Crash detection ──────────────────────────────────────────────────────────
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
    """Add Allure attachments on test failure + always save UI screenshots to disk."""
    outcome = yield
    report  = outcome.get_result()

    if report.when == "call":
        driver = item.funcargs.get("driver")
        if not driver:
            return

        # Give logcat a moment (helps with end-of-test RN crashes)
        time.sleep(2)

        # 1) Check for crashes (even if test was passing)
        crash_log = check_for_crashes(driver)

        if crash_log:
            print(f"CRASH DETECTED in {item.nodeid}")
            allure.attach(
                crash_log,
                name="Crash Logs",
                attachment_type=allure.attachment_type.TEXT,
            )
            if report.outcome != "failed":
                report.outcome = "failed"
                report.longrepr = "FAILURE: Application Crash Detected in Logcat"

        # 2) ALWAYS save an end-of-test screenshot to disk (for UI parser)
        _save_ui_screenshot(
            driver=driver,
            config=item.config,
            nodeid=item.nodeid,
            name=f"end__{report.outcome}",
        )

        # 3) If failed, also attach screenshot to Allure
        if report.outcome == "failed":
            try:
                screenshot = driver.get_screenshot_as_png()
                allure.attach(
                    screenshot,
                    name="Failure Screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception as e:
                print(f"Failed to capture screenshot: {str(e)}")

def notReportFailed(report):
    return report.outcome != "failed"