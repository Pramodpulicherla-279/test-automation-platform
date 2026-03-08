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
    """Add Allure attachments on test failure + always save UI screenshots to disk."""
    outcome = yield
    report = outcome.get_result()

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