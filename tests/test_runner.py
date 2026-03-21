import os
import shutil
# Disable auto-loading of 3rd-party pytest plugins (like browserstack)
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
import sys
import pytest
import allure_pytest  # pip install allure-pytest
import requests
import subprocess
from dotenv import load_dotenv
from typing import Optional, List, Dict
import threading
import queue
<<<<<<< HEAD
=======
sys.dont_write_bytecode = True
>>>>>>> 70f383605087ad6b424caa5b697a86d4ba48cf55

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CURRENT_PROC: Optional[subprocess.Popen] = None
STOP_FLAG = False  # New global flag to control execution flow

RESULTS_DIR = "allure-results"
REPORT_DIR = "allure-report"

# --- NEW: log queue + worker ---
_LOG_Q: "queue.Queue[tuple[str, str]]" = queue.Queue(maxsize=5000)
_LOG_WORKER_STARTED = False

def _start_log_worker() -> None:
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
                    f"{BACKEND_URL}/api/log-step",
                    json={"message": message, "status": status},
                    timeout=1,  # keep small; don't stall the worker either
                )
            except Exception:
                pass
            finally:
                _LOG_Q.task_done()

    t = threading.Thread(target=_worker, name="log-step-worker", daemon=True)
    t.start()

def _ensure_clean_allure_dirs(project_root: str) -> None:
    os.makedirs(os.path.join(project_root, RESULTS_DIR), exist_ok=True)
    # Clean report dir (html) so you don’t open an old report
    report_path = os.path.join(project_root, REPORT_DIR)
    if os.path.isdir(report_path):
        shutil.rmtree(report_path, ignore_errors=True)

def generate_report(project_root: Optional[str] = None) -> None:
    """
    Generates and opens Allure HTML report.
    Can be called manually or automatically.
    """
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(__file__))

    # improved command resolution
    allure_cmd = "allure"
    # specific check for user's scoop path if regular allure isn't found
    scoop_path = r"C:\Users\ram\scoop\shims\allure.cmd" 
    if os.path.exists(scoop_path):
        allure_cmd = scoop_path
    elif shutil.which("allure.cmd"):
        allure_cmd = "allure.cmd"
    
    try:
        send_log("Generating Allure HTML report...", "INFO")
        # 1. Generate
        subprocess.run(
            [allure_cmd, "generate", RESULTS_DIR, "-o", REPORT_DIR, "--clean"],
            cwd=project_root,
            check=True,
            shell=True 
        )
        send_log("Allure HTML report generated.", "SUCCESS")
        
        # 2. Open
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
        
def _generate_and_open_allure_report(project_root: str) -> None:
    """
    Generates and opens Allure HTML report.
    """
    allure_cmd = r"C:\Users\ram\scoop\shims\allure"

    # Fallback to system 'allure' if the hardcoded path doesn't exist
    if not os.path.exists(allure_cmd) and shutil.which("allure"):
        allure_cmd = "allure" 

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
        send_log(f"Allure CLI not found or failed: {e}", "FAILED")

def notify_allure_open() -> None:
    """
    Ask backend to start Allure server (allure open/serve) and broadcast RUN_COMPLETE.
    Backend should implement POST /api/allure/start.
    """
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
        # If logs are too noisy, drop instead of blocking the test run.
        pass
    except Exception:
        pass

def run_pytest_with_logs(pytest_args, module_name: str) -> bool:
  """
  Run pytest in a subprocess and stream all stdout lines
  into the WebSocket log console.
  """
  send_module_status(module_name, "running", f"Starting {module_name} tests")
  send_log(f"==== Running {module_name} tests ====", "INFO")

  # Build command: python -m pytest <args>
  cmd = [
        os.sys.executable, "-u", "-m", "pytest",
        "-s", "--capture=no", "-v", "--tb=short",
        "-o", "log_cli=true",
        "-o", "log_cli_level=INFO",
    ] + pytest_args
  env = os.environ.copy()
  env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"})

  proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    cwd=os.path.dirname(os.path.dirname(__file__)),  # project root
    env=env
  )

  # Stream each line to frontend
  assert proc.stdout is not None
  for line in proc.stdout:
    send_log(line.rstrip("\n"), "INFO")

  proc.wait()
  success = (proc.returncode == 0)

  if success:
    send_module_status(module_name, "completed", f"{module_name} tests passed")
    send_log(f"{module_name} tests passed", "SUCCESS")
  else:
    send_module_status(module_name, "failed", f"{module_name} tests failed")
    send_log(f"{module_name} tests failed", "FAILED")

  return success

def send_module_status(module: str, status: str, message: str = ""):
    """Notify backend which module is running/completed."""
    try:
        requests.post(
            f"{BACKEND_URL}/api/module-status",
            json={"module": module, "status": status, "message": message},
            timeout=3,
        )
    except Exception:
        # Do not break tests if backend is down
        pass

def stop_current_tests() -> bool:
    global CURRENT_PROC, STOP_FLAG
    STOP_FLAG = True  # Signal the runner loop to stop

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

def run_pytest_streaming(pytest_args: list[str], module_mapping: Dict[str, str], clean_allure: bool = False) -> bool:
    """
    Run pytest and parse logs in real-time to update individual module statuses.
    module_mapping: { "path/to/test.py": "Module Name" }
    """
    global CURRENT_PROC, STOP_FLAG
    if STOP_FLAG: return False

    project_root = os.path.dirname(os.path.dirname(__file__))
    send_log("==== Starting Sequential Test Suite ====", "INFO")

    cmd = [
        sys.executable, "-u", "-m", "pytest", "-p", "allure_pytest", 
        "-s", "-v", "--tb=short", f"--alluredir={RESULTS_DIR}",
    ]
    if clean_allure: cmd.append("--clean-alluredir")
    cmd += pytest_args

    env = os.environ.copy()
    env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"})

    CURRENT_PROC = subprocess.Popen(
        cmd, cwd=project_root, stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, text=True, bufsize=1, env=env
    )

    proc = CURRENT_PROC
    assert proc.stdout is not None
    
    current_active_module = None

    for line in proc.stdout:
        if STOP_FLAG: break
        clean_line = line.strip()
        send_log(clean_line, "INFO")

        # --- Dynamic Status Logic ---
        # Detect which file pytest is currently running
        for path, name in module_mapping.items():
            if path in clean_line and ("collecting" in clean_line.lower() or "::" in clean_line):
                if current_active_module != name:
                    current_active_module = name
                    send_module_status(name, "running", f"Executing {name}")

        # Detect individual test failures to mark module as failed early
        if " FAILED " in line and current_active_module:
            send_module_status(current_active_module, "failed", "Test failed")

    if STOP_FLAG:
        if proc.poll() is None: proc.kill()
        return False
    
    proc.wait()
    return proc.returncode == 0
# def resolve_test_modules(app_type: str, module_names: Optional[List[str]] = None) -> List[Dict[str, str]]:
#     """
#     Helper to resolve a list of runnable test configs based on the app type and selected modules.
    
#     :param app_type: One of 'regular_farmer', 'regular_client', 'state_farmer', 'state_client'
#     :param module_names: List of keys (e.g. ['login', 'dashboard']). If None/Empty, runs ALL for that app.
#     :return: List of dicts suitable for 'tests_to_run'
#     """
#     app_config = TEST_REGISTRY.get(app_type.lower())
#     if not app_config:
#         send_log(f"Unknown App Type: {app_type}. Available: {list(TEST_REGISTRY.keys())}", "FAILED")
#         return []

#     resolved_tests = []
    
#     # If no specific modules selected, select ALL for this app
#     target_keys = module_names if module_names else list(app_config.keys())

#     for key in target_keys:
#         script_path = app_config.get(key.lower())
#         if script_path:
#             resolved_tests.append({"name": key.capitalize(), "path": script_path})
#         else:
#             send_log(f"Warning: Module '{key}' not found for app '{app_type}'", "WARNING")
            
#     return resolved_tests

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
    """
    global STOP_FLAG
    STOP_FLAG = False 

    project_root = os.path.dirname(os.path.dirname(__file__))

    if not os.path.exists(apk_path):
        send_log(f"APK not found at {apk_path}", "FAILED")
        return

    _ensure_clean_allure_dirs(project_root)

    # 1. Resolve and Validate Tests
    final_test_list = []
    if tests_to_run:
        final_test_list = tests_to_run
    # elif app_type: ... (your resolve_test_modules logic)
    
    if not final_test_list:
        send_log("No valid test modules found. Aborting.", "FAILED")
        return

    # 2. Prepare Path-to-Name Mapping for Status Tracking
    valid_paths = []
    # This map helps us know which 'path' corresponds to which 'UI name'
    path_to_name_map = {}
    
    for t in final_test_list:
        path = t.get("path")
        name = t.get("name", path)
        if path and os.path.exists(os.path.join(project_root, path)):
            valid_paths.append(path)
            path_to_name_map[path] = name
            # Set initial status to pending in UI
            send_module_status(name, "pending", "Waiting in queue...")
        else:
            send_log(f"Script not found: {path}", "WARNING")

    if not valid_paths:
        send_log("No valid scripts to execute.", "FAILED")
        return

    # 3. Run the Suite and Track Statuses
    send_log(f"Starting sequential suite for: {list(path_to_name_map.values())}", "INFO")
    
    # We pass the path_to_name_map to the streaming function so it can update the UI
    pytest_args = valid_paths + [f"--apk={apk_path}", "-v"]

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

    # 4. Final Cleanup
    if not STOP_FLAG:
        if overall_ok:
            send_log("Full test suite execution completed successfully.", "SUCCESS")
        else:
            send_log("Suite execution finished with errors.", "FAILED")
        
        generate_report(project_root)

def run_pytest_streaming_with_tracking(pytest_args: list[str], path_mapping: dict, clean_allure: bool) -> bool:
    """
    Sub-function to execute pytest and parse lines for UI status updates.
    Ensures that if any test in a module fails, the module status is 'failed'.
    """
    global CURRENT_PROC, STOP_FLAG
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    cmd = [
        sys.executable, "-u", "-m", "pytest", "-p", "allure_pytest",
        "-s", "-v", "--tb=short", f"--alluredir={RESULTS_DIR}",
        "-o", "log_cli=true",
        "-o", "log_cli_level=INFO",
    ]    
    if clean_allure: cmd.append("--clean-alluredir")
    cmd += pytest_args

    env = os.environ.copy()
    env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"})

    CURRENT_PROC = subprocess.Popen(
        cmd, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, env=env
    )

    active_module_name = None
    # We use this to track which modules specifically encountered a failure
    failed_modules = set()

    assert CURRENT_PROC.stdout is not None
    for line in CURRENT_PROC.stdout:
        if STOP_FLAG: break
        
        raw_line = line.rstrip("\n")
        send_log(raw_line, "INFO")
        
        # Normalize line for path matching (Windows uses backslashes)
        normalized_line = raw_line.replace("\\", "/")

        # LOGIC: Identify which module is currently executing
        for path, name in path_mapping.items():
            # Normalize config path as well
            normalized_path = path.replace("\\", "/")
            
            if normalized_path in normalized_line and "::" in normalized_line:
                if active_module_name != name:
                    # Before switching, if the previous module wasn't marked failed, mark it completed/passed
                    if active_module_name and active_module_name not in failed_modules:
                        send_module_status(active_module_name, "completed", "Module passed")
                    
                    active_module_name = name
                    send_module_status(name, "running", "Executing tests...")

        # CRITICAL FIX: Detect app crashes or assertion failures
        # 1. "FAILED" appearing as a standalone word (e.g. at end of line)
        # 2. " ERROR " for errors outside of test functions
        # 3. Crash detection
        parts = raw_line.split()
        if "FAILED" in parts or " ERROR " in raw_line or "Application Crash Detected" in raw_line:
            if active_module_name:
                failed_modules.add(active_module_name)
                # Immediately notify frontend of the failure
                send_module_status(active_module_name, "failed", "Failure detected in module")

    # Final wrap-up for the last module in the sequence
    if active_module_name:
        if active_module_name in failed_modules:
            send_module_status(active_module_name, "failed", "Module execution failed")
        else:
            send_module_status(active_module_name, "completed", "Module execution finished")

    CURRENT_PROC.wait()
    return CURRENT_PROC.returncode == 0

if __name__ == "__main__":
    # CLI Usage: 
    # python tests/test_runner.py <apk_path> <app_type> [module1] [module2] ...
    # Example: python tests/test_runner.py app.apk regular_farmer login dashboard

    import sys

    if len(sys.argv) < 2:
        print("Usage: python tests/test_runner.py <apk_path> [app_type] [module_names...]")
        sys.exit(1)

    apk_arg = sys.argv[1]
    app_type_arg = sys.argv[2] if len(sys.argv) > 2 else None
    modules_arg = sys.argv[3:] if len(sys.argv) > 3 else None

    run_tests_and_get_suggestions(
        apk_path=apk_arg,
        app_type=app_type_arg,
        module_names=modules_arg
    )