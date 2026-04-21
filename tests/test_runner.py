import os
import sys, os
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
from datetime import datetime
import json
sys.dont_write_bytecode = True
import threading
import queue
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CURRENT_PROC: Optional[subprocess.Popen] = None
STOP_FLAG = False

RESULTS_DIR = "allure-results"
REPORT_DIR = "allure-report"

# --- Log queue + worker ---
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

def fetch_network_config(run_id):
    try:
        res = requests.get(f"{BACKEND_URL}/network-simulate/config/{run_id}", timeout=5)
        data = res.json()
        return data.get("network_config")
    except Exception as e:
        send_log(f"Failed to fetch network config: {e}", "WARNING")
        return None
    
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

# def apply_network_config_local(config):
#     if not config or not config.get("enabled"):
#         return

#     latency = config.get("latency", 0)
#     loss = config.get("packetLoss", 0)
#     download = config.get("download", 10)

#     send_log(f"📡 Applying Network → {latency}ms | {download}Mbps | loss {loss}%", "INFO")

#     try:
#         # clear existing
#         os.system("tc qdisc del dev eth0 root 2>/dev/null")

#         # apply latency + loss
#         os.system(f"tc qdisc add dev eth0 root netem delay {latency}ms loss {loss}%")

#         # bandwidth control
#         os.system(f"tc qdisc add dev eth0 parent 1:1 handle 10: tbf rate {download}mbit burst 32kbit latency 400ms")

#     except Exception as e:
#         send_log(f"Network simulation failed: {e}", "FAILED")
PROXY_PROCESS = None

def start_proxy(latency):
    global PROXY_PROCESS

    PROXY_PROCESS = subprocess.Popen([
        "mitmdump",
        "-s", "network_proxy.py"
    ])

    send_log(f"🌐 Proxy started with latency {latency}s", "INFO")

def stop_proxy():
    global PROXY_PROCESS

    if PROXY_PROCESS:
        PROXY_PROCESS.terminate()
        PROXY_PROCESS = None
        send_log("🛑 Proxy stopped", "INFO")

def apply_network_config_local(config):
    if not config or not config.get("enabled"):
        return

    latency = config.get("latency", 0) / 1000  # ms → seconds

    send_log(f"📡 Applying Network via Proxy → {latency}s", "INFO")

    start_proxy(latency)
    
def run_tests_and_get_suggestions(
    apk_path: str,
    tests_to_run: Optional[List[Dict[str, str]]] = None,
    app_type: Optional[str] = None,
    module_names: Optional[List[str]] = None,
    app_name: Optional[str] = None,
    app_version: Optional[str] = None,
    developer_name: Optional[str] = None,
    run_id=None 
) -> None:
    """
    Runs all tests in a single session to keep the app open,
    while tracking individual module statuses in real-time.
    Captures API test results and sends them to matrix API.
    """
    global STOP_FLAG
    STOP_FLAG = False

    project_root = os.path.dirname(os.path.dirname(__file__))
    
    network_config = fetch_network_config(run_id)

    if network_config:
        apply_network_config_local(network_config)

    # Inject backend dir into PYTHONPATH so jira_integration is importable by pytest
    backend_dir = os.path.join(project_root, "backend")
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = (
        backend_dir + os.pathsep + existing_pythonpath
        if existing_pythonpath
        else backend_dir
    )

    if not os.path.exists(apk_path):
        send_log(f"APK not found at {apk_path}", "FAILED")
        return

    _ensure_clean_allure_dirs(project_root)

    # 1. Resolve and Validate Tests
    final_test_list = []
    if tests_to_run:
        final_test_list = tests_to_run

    if not final_test_list:
        send_log("No valid test modules found. Aborting.", "FAILED")
        return

    # 2. Prepare Path-to-Name Mapping for Status Tracking
    valid_paths = []
    path_to_name_map = {}

    for t in final_test_list:
        path = t.get("path")
        name = t.get("name", path)
        if path and os.path.exists(os.path.join(project_root, path)):
            valid_paths.append(path)
            path_to_name_map[path] = name
            send_module_status(name, "pending", "Waiting in queue...")
        else:
            send_log(f"Script not found: {path}", "WARNING")

    if not valid_paths:
        send_log("No valid scripts to execute.", "FAILED")
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
    
    stop_proxy()
    
    # Final Cleanup
    if not STOP_FLAG:
        if overall_ok:
            send_log("Full test suite execution completed successfully.", "SUCCESS")
        else:
            send_log("Suite execution finished with errors.", "FAILED")

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
    """
    global CURRENT_PROC, STOP_FLAG
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    # Pass PYTHONPATH through to the subprocess so jira_integration is found
    backend_dir = os.path.join(project_root, "backend")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = backend_dir + os.pathsep + existing if existing else backend_dir
    env.update({
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
    })

    cmd = [
        sys.executable, "-u", "-m", "pytest", "-p", "allure_pytest",
        "-s", "-v", "--tb=short", f"--alluredir={RESULTS_DIR}",
        "-o", "log_cli=true",
        "-o", "log_cli_level=INFO",
    ]

    # if "NETWORK_CHANGE" in raw_line:
    #     apply_network_config_local(step_config)

    if clean_allure:
        cmd.append("--clean-alluredir")
    cmd += pytest_args

    CURRENT_PROC = subprocess.Popen(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    active_module_name = None
    failed_modules = set()

    assert CURRENT_PROC.stdout is not None
    for line in CURRENT_PROC.stdout:
        if STOP_FLAG:
            break

        raw_line = line.rstrip("\n")
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