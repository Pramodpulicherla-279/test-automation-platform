import os
import sys
import shutil
# Disable auto-loading of 3rd-party pytest plugins (like browserstack)
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

# FIX: use get_servers() from appium_state (reads shared JSON file) instead of
# directly importing appium_servers from manager (stale list binding).
# Direct import: `from manager import appium_servers` captures the list object
# at import time. If manager.py later does `appium_servers = [...]`, this
# module's reference still points to the old empty list → workers = 1 always.
from new_backend.modules.appium_grid.appium_state import (
    get_servers,
    get_device_for_port,  # NEW: Get device name for a port
    get_device_mapping    # NEW: Get all device->port mappings
)

import sys
import pytest
import allure_pytest  # pip install allure-pytest
import requests
import subprocess
from dotenv import load_dotenv
from typing import Optional, List, Dict
import threading
import queue
sys.dont_write_bytecode = True

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CURRENT_PROC: Optional[subprocess.Popen] = None
STOP_FLAG = False

RESULTS_DIR = "allure-results"
REPORT_DIR = "allure-report"


# --- Log queue + worker ---
_LOG_Q: "queue.Queue[tuple[str, str]]" = queue.Queue(maxsize=5000)
_LOG_WORKER_STARTED = False

# FIX: Track which device is running which test
_DEVICE_MAPPING: Dict[int, str] = {}  # port -> device_id mapping


def _start_log_worker() -> None:
    """Start background worker to send logs to backend."""
    global _LOG_WORKER_STARTED
    if _LOG_WORKER_STARTED:
        return
    _LOG_WORKER_STARTED = True

    def _worker() -> None:
        session = requests.Session()
        while True:
            message, status = _LOG_Q.get()
            try:
                session.post(
                    f"{BACKEND_URL}/test/log-step",
                    json={"message": message, "status": status},
                    timeout=1,
                )
            except Exception:
                pass
            finally:
                _LOG_Q.task_done()

    t = threading.Thread(target=_worker, name="log-step-worker", daemon=True)
    t.start()


def _ensure_clean_allure_dirs(project_root: str) -> None:
    """Ensure Allure results directories are clean."""
    os.makedirs(os.path.join(project_root, RESULTS_DIR), exist_ok=True)
    report_path = os.path.join(project_root, REPORT_DIR)
    if os.path.isdir(report_path):
        shutil.rmtree(report_path, ignore_errors=True)


def generate_report(project_root: Optional[str] = None) -> None:
    """Generates and opens Allure HTML report."""
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(__file__))

    allure_cmd = "allure"
    scoop_path = r"C:\Users\Pramo\scoop\shims\allure.cmd"
    if os.path.exists(scoop_path):
        allure_cmd = scoop_path
    elif shutil.which("allure.cmd"):
        allure_cmd = "allure.cmd"

    try:
        send_log("Generating Allure HTML report...", "INFO")
        subprocess.run(
            [allure_cmd, "generate", RESULTS_DIR, "-o", REPORT_DIR, "--clean"],
            cwd=project_root,
            check=True,
            shell=True
        )
        send_log("Allure HTML report generated.", "SUCCESS")

        send_log("Opening Allure report in browser...", "INFO")
        subprocess.Popen(
            [allure_cmd, "open", REPORT_DIR],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )
    except Exception as e:
        send_log(f"Failed to generate/open report: {e}", "FAILED")
        print(f"Report Generation Error: {e}")


def notify_allure_open() -> None:
    """Ask backend to start Allure server and broadcast RUN_COMPLETE."""
    try:
        requests.post(f"{BACKEND_URL}/api/allure/start", timeout=10)
    except Exception:
        pass


def send_log(message: str, status: str = "INFO") -> None:
    """Queue one log line for the frontend via /api/log-step (non-blocking)."""
    try:
        _start_log_worker()
        _LOG_Q.put_nowait((message, status))
    except queue.Full:
        pass
    except Exception:
        pass


def send_module_status(module: str, status: str, message: str = ""):
    """Notify backend which module is running/completed."""
    try:
        requests.post(
            f"{BACKEND_URL}/test/module-status",
            json={"module": module, "status": status, "message": message},
            timeout=3,
        )
    except Exception:
        pass


def stop_current_tests() -> bool:
    """Stop the currently running test process."""
    global CURRENT_PROC, STOP_FLAG
    STOP_FLAG = True

    if CURRENT_PROC is None:
        return False

    try:
        send_log("Stopping tests on user request...", "FAILED")
        CURRENT_PROC.terminate()
        try:
            CURRENT_PROC.wait(timeout=2)
        except subprocess.TimeoutExpired:
            CURRENT_PROC.kill()
        send_log("Test process terminated.", "FAILED")
    except Exception as e:
        send_log(f"Error while stopping tests: {e}", "FAILED")
    finally:
        CURRENT_PROC = None

    return True


# ════════════════════════════════════════════════════════════════════════════
#  PER-DEVICE ALLURE ENVIRONMENT FILE (NEW)
# ════════════════════════════════════════════════════════════════════════════
def _write_allure_environment(project_root: str, current_servers: list,
                               app_name: str = "", app_version: str = "") -> None:
    """
    NEW: Write allure environment.properties so the report shows which devices
    were used. This makes the Allure Overview tab display device/port info
    and allows comparing results across devices.

    File format (allure-results/environment.properties):
      device.0=emulator-5554
      port.0=4723
      device.1=emulator-5556
      port.1=4725
      app.name=Krishivaas Farmer
      app.version=1.3.96
    """
    env_file = os.path.join(project_root, RESULTS_DIR, "environment.properties")
    try:
        lines = []
        for i, srv in enumerate(current_servers):
            device = srv.get("device", f"device-{i}")
            port = srv.get("port", "")
            lines.append(f"device.{i}={device}")
            lines.append(f"port.{i}={port}")
        if app_name:
            lines.append(f"app.name={app_name}")
        if app_version:
            lines.append(f"app.version={app_version}")

        with open(env_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[ALLURE] environment.properties written → {env_file}")
    except Exception as e:
        print(f"[ALLURE] Failed to write environment.properties: {e}")


def run_tests_and_get_suggestions(
    apk_path: str,
    tests_to_run: Optional[List[Dict[str, str]]] = None,
    app_type: Optional[str] = None,
    module_names: Optional[List[str]] = None,
    app_name: Optional[str] = None,
    app_version: Optional[str] = None,
    developer_name: Optional[str] = None,
) -> None:
    """
    Runs all tests in a single session to keep the app open,
    while tracking individual module statuses in real-time.
    
    FIXES:
    - Device validation before running tests
    - Per-device allure environment file
    - Better device mapping and logging
    - W3C swipe safety via driver health checks in conftest
    """
    global STOP_FLAG, _DEVICE_MAPPING
    STOP_FLAG = False

    project_root = os.path.dirname(os.path.dirname(__file__))

    # Inject backend dir into PYTHONPATH so jira_integration is importable by pytest
    backend_dir = os.path.join(project_root, "backend")
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = (
        backend_dir + os.pathsep + existing_pythonpath
        if existing_pythonpath
        else backend_dir
    )

    if not os.path.exists(apk_path):
        send_log(f"❌ APK not found at {apk_path}", "FAILED")
        return

    # DEVICE VALIDATION - Check if Appium servers are running with devices
    current_servers = get_servers()
    if not current_servers:
        send_log(
            "❌ NO APPIUM SERVERS RUNNING - Start Appium with devices first! "
            "Run /appium/start endpoint to start servers.",
            "FAILED"
        )
        return

    # Build device mapping for tracking which device runs which test
    _DEVICE_MAPPING = {}
    for srv in current_servers:
        port = srv.get("port")
        device = srv.get("device", "unknown")
        if port and device:
            _DEVICE_MAPPING[port] = device

    _ensure_clean_allure_dirs(project_root)

    # NEW: Write allure environment file with device info before tests run
    _write_allure_environment(project_root, current_servers, app_name or "", app_version or "")

    # 1. Resolve and Validate Tests
    final_test_list = []
    if tests_to_run:
        final_test_list = tests_to_run

    if not final_test_list:
        send_log("⚠️  No valid test modules found. Aborting.", "FAILED")
        return

    # 2. Prepare Path-to-Name Mapping for Status Tracking
    valid_paths = []
    path_to_name_map = {}
    
    from pathlib import Path
    
    BASE_DIR = Path(project_root).resolve()
    
    print("\n📂 TEST PATH DEBUG")
    print(f"Project root: {BASE_DIR}")
    print(f"Current working dir: {os.getcwd()}\n")
    
    for t in final_test_list:
        path = t.get("path")
        name = t.get("name", path)
    
        if not path:
            continue
    
        p = Path(path)
        if p.is_absolute():
            full_path = p.resolve()
        else:
            full_path = (BASE_DIR / path).resolve()
    
        print(f"Checking path:")
        print(f"   Input: {path}")
        print(f"   Full : {full_path}")
        print(f"   Exists: {full_path.exists()}\n")
    
        if full_path.exists():
            valid_paths.append(str(full_path))
            path_to_name_map[str(full_path)] = name
            send_module_status(name, "pending", "Waiting in queue...")
        else:
            send_log(f"❌ Script not found: {path}", "FAILED")

    if not valid_paths:
        send_log("❌ No valid scripts to execute. Check that test file paths are correct.", "FAILED")
        send_log(f"Working directory: {os.getcwd()}", "DEBUG")
        send_log(f"Project root: {project_root}", "DEBUG")
        return

    # Tell frontend a new run is starting
    try:
        import requests as _req
        _req.post(
            f"{BACKEND_URL}/test/module-status",
            json={"module": "__RUN_START__", "status": "start", "message": ""},
            timeout=2,
        )
    except Exception:
        pass

    # Enhanced logging with device info
    device_mapping = get_device_mapping()
    workers = max(1, len(current_servers))
    
    print(f"\n{'='*70}")
    print(f"🚀 TEST EXECUTION STARTING")
    print(f"{'='*70}")
    print(f"   📦 APK: {os.path.basename(apk_path)}")
    print(f"   📱 Connected Devices: {len(current_servers)}")
    for device, port in device_mapping.items():
        print(f"      • {device:20} → Appium port {port}")
    print(f"   ⚙️  Parallel Workers: {workers}")
    print(f"   📋 Test Modules: {len(valid_paths)}")
    print(f"{'='*70}\n")
    
    send_log(
        f"[Parallel] Running with {workers} worker(s) across {len(current_servers)} device(s)",
        "INFO"
    )
    
    for device, port in device_mapping.items():
        send_log(f"   📱 {device} → Appium server on port {port}", "INFO")

    try:
        import xdist  # check if installed
        use_parallel = True
    except ImportError:
        use_parallel = False
    
    pytest_args = valid_paths + [
        f"--apk={apk_path}",
        "-v"
    ]
    
    if use_parallel and workers > 1:
        pytest_args += ["-n", str(workers)]
        send_log(f"🚀 Running in PARALLEL with {workers} workers", "INFO")
    else:
        send_log("⚠️ Running in SEQUENTIAL mode (xdist not installed)", "WARN")
        
    send_log(f"APK PASSED TO PYTEST: {apk_path}", "INFO")
    
    if app_name:
        pytest_args.append(f"--app-name={app_name}")
    if app_version:
        pytest_args.append(f"--app-version={app_version}")
    if developer_name:
        pytest_args.append(f"--developer-name={developer_name}")

    overall_ok = run_pytest_streaming_with_tracking(
        pytest_args,
        path_to_name_map,
        clean_allure=True
    )

    # Final Cleanup
    if not STOP_FLAG:
        if overall_ok:
            send_log("✅ Full test suite execution completed successfully.", "SUCCESS")
        else:
            send_log("⚠️  Suite execution finished with errors.", "FAILED")

        generate_report(project_root)

        try:
            import requests as _req
            _req.post(
                f"{BACKEND_URL}/test/run-complete",
                json={"report_url": "http://localhost:8000/allure-report/index.html"},
                timeout=3,
            )
        except Exception:
            pass


def run_pytest_streaming_with_tracking(
    pytest_args: list,
    path_mapping: dict,
    clean_allure: bool
) -> bool:
    """
    Execute pytest and parse lines for UI status updates.
    Ensures that if any test in a module fails, the module status is 'failed'.

    FIXES:
    - Set UTF-8 encoding for subprocess
    - Load both allure_pytest and xdist explicitly
    - Enhanced environment with UTF-8 settings
    - W3C swipe fix: driver health check in conftest prevents crashes here
    
    FIX: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 suppresses all auto-loaded plugins,
    including pytest-xdist. We load allure_pytest and xdist explicitly via
    '-p allure_pytest' and '-p xdist' so that the '-n <workers>' flag is
    recognised by the subprocess.
    """
    global CURRENT_PROC, STOP_FLAG
    project_root = os.path.dirname(os.path.dirname(__file__))

    # Pass PYTHONPATH through to the subprocess so jira_integration is found
    backend_dir = os.path.join(project_root, "backend")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = backend_dir + os.pathsep + existing if existing else backend_dir
    
    # Enhanced UTF-8 configuration for proper encoding
    env.update({
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG": "en_US.UTF-8" if os.name != 'nt' else "",
        "LC_ALL": "en_US.UTF-8" if os.name != 'nt' else "",
    })
    
    # Remove empty values on Windows
    if os.name == 'nt':
        env = {k: v for k, v in env.items() if v}

    cmd = [
        sys.executable, "-u", "-m", "pytest",
        # Explicitly load both allure_pytest AND xdist
        "-p", "allure_pytest",
        "-p", "xdist",
        "-s", "-v", "--tb=short", f"--alluredir={RESULTS_DIR}",
        "-o", "log_cli=true",
        "-o", "log_cli_level=INFO",
    ]
    if clean_allure:
        cmd.append("--clean-alluredir")
    cmd += pytest_args

    print(f"\n[pytest] Starting with command:")
    print(f"   {' '.join(cmd[:5])}...")
    print(f"   {' '.join(cmd[-5:])}")
    print()

    CURRENT_PROC = subprocess.Popen(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        encoding='utf-8',
        errors='replace'
    )

    active_module_name = None
    failed_modules = set()

    assert CURRENT_PROC.stdout is not None
    try:
        for line in CURRENT_PROC.stdout:
            if STOP_FLAG:
                break

            try:
                raw_line = line.rstrip("\n")
            except Exception as e:
                print(f"[ERROR] Line decode failed: {e}")
                raw_line = str(line)

            send_log(raw_line, "INFO")

            normalized_line = raw_line.replace("\\", "/")

            for path, name in path_mapping.items():
                normalized_path = path.replace("\\", "/")
                if normalized_path in normalized_line and "::" in normalized_line:
                    if active_module_name != name:
                        if active_module_name and active_module_name not in failed_modules:
                            send_module_status(active_module_name, "completed", "Module passed")
                        active_module_name = name
                        send_module_status(name, "running", "Executing tests...")

            parts = raw_line.split()
            if "FAILED" in parts or " ERROR " in raw_line or "Application Crash Detected" in raw_line:
                if active_module_name:
                    failed_modules.add(active_module_name)
                    send_module_status(active_module_name, "failed", "Failure detected in module")

    except UnicodeDecodeError as e:
        print(f"❌ Unicode decode error in test output: {e}")
        send_log(f"⚠️  Unicode error in output (likely special characters): {e}", "WARNING")
    except Exception as e:
        print(f"❌ Error reading test output: {e}")
        send_log(f"⚠️  Error reading test output: {e}", "WARNING")

    # Final wrap-up for the last module
    if active_module_name:
        if active_module_name in failed_modules:
            send_module_status(active_module_name, "failed", "Module execution failed")
        else:
            send_module_status(active_module_name, "completed", "Module execution finished")

    if STOP_FLAG:
        if CURRENT_PROC.poll() is None:
            CURRENT_PROC.kill()
        return False

    CURRENT_PROC.wait()
    return CURRENT_PROC.returncode == 0


# ════════════════════════════════════════════════════════════════════════════
#  CLI ENTRYPOINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/test_runner.py <apk_path> [app_type] [module_names...]")
        sys.exit(1)

    apk_arg = sys.argv[1]
    app_type_arg = sys.argv[2] if len(sys.argv) > 2 else None
    modules_arg = sys.argv[3:] if len(sys.argv) > 3 else None

    run_tests_and_get_suggestions(
        apk_path=apk_arg,
        app_type=app_type_arg,
        module_names=modules_arg,
    )