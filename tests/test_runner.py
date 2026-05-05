import os
import sys
import shutil

os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

from new_backend.modules.appium_grid.appium_state import (
    get_servers,
    get_device_for_port,
    get_device_mapping
)
import glob
import pytest
import allure_pytest
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

# ── Directory constants ────────────────────────────────────────────────────────
# FIX: Single shared results dir — both workers write here, allure generate reads here.
# Previously RESULTS_DIR ("allure-results") and DEVICE_RESULTS_ROOT ("allure-results-device")
# were different paths, so allure generate found 0 results.
RESULTS_DIR = "allure-results"   # ← THE only results dir now (workers + generate both use this)
REPORT_DIR  = "allure-report"

# --- Log queue + worker -------------------------------------------------------
_LOG_Q: "queue.Queue[tuple[str, str]]" = queue.Queue(maxsize=5000)
_LOG_WORKER_STARTED = False

_DEVICE_MAPPING: Dict[int, str] = {}


# ════════════════════════════════════════════════════════════════════════════
#  LOG WORKER
# ════════════════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════════════════
#  ALLURE DIR HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _ensure_clean_allure_dir(project_root: str) -> None:
    """
    FIX: Single shared dir approach.

    Previously: created per-worker subdirs under allure-results-device/ then
    tried to merge them.  The merge step ran BEFORE tests, allure-results/ was
    empty, and generate_report found 0 items.

    Now: wipe allure-results/ (preserving history), all workers write directly
    to it, generate_report reads the same dir.  No merge step needed.
    """
    merged      = os.path.join(project_root, RESULTS_DIR)
    history_path = os.path.join(merged, "history")
    temp_history = os.path.join(project_root, "temp_history")

    # Preserve trend history across runs
    if os.path.exists(temp_history):
        shutil.rmtree(temp_history, ignore_errors=True)
    if os.path.isdir(history_path):
        shutil.copytree(history_path, temp_history)
    if os.path.isdir(merged):
        shutil.rmtree(merged, ignore_errors=True)
    os.makedirs(merged, exist_ok=True)
    if os.path.exists(temp_history):
        shutil.copytree(temp_history, os.path.join(merged, "history"))
        shutil.rmtree(temp_history, ignore_errors=True)

    # Wipe old HTML report
    report_path = os.path.join(project_root, REPORT_DIR)
    if os.path.isdir(report_path):
        shutil.rmtree(report_path, ignore_errors=True)

    print(f"[ALLURE] Shared results dir ready: {merged}")


def _write_allure_environment(
    project_root: str,
    current_servers: list,
    app_name: str = "",
    app_version: str = "",
) -> None:
    env_file = os.path.join(project_root, RESULTS_DIR, "environment.properties")
    try:
        lines = [f"device.count={len(current_servers)}"]
        for i, srv in enumerate(current_servers):
            device  = srv.get("device", f"device-{i}")
            port    = srv.get("port", "")
            os_ver  = _get_android_os_version(device)
            lines += [
                f"device.{i}.id={device}",
                f"device.{i}.port={port}",
                f"device.{i}.os={os_ver}",
            ]
        if app_name:
            lines.append(f"app.name={app_name}")
        if app_version:
            lines.append(f"app.version={app_version}")

        with open(env_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[ALLURE] environment.properties written → {env_file}")
    except Exception as e:
        print(f"[ALLURE] Failed to write environment.properties: {e}")


def _get_android_os_version(device_id: str) -> str:
    try:
        result = subprocess.run(
            ["adb", "-s", device_id, "shell", "getprop", "ro.build.version.release"],
            capture_output=True, text=True, timeout=5
        )
        release = result.stdout.strip()
        api_result = subprocess.run(
            ["adb", "-s", device_id, "shell", "getprop", "ro.build.version.sdk"],
            capture_output=True, text=True, timeout=5
        )
        api = api_result.stdout.strip()
        if release:
            return f"Android {release} (API {api})" if api else f"Android {release}"
    except Exception as e:
        print(f"[ADB] Could not get OS version for {device_id}: {e}")
    return "Android Unknown"


# ════════════════════════════════════════════════════════════════════════════
#  LOGGING HELPERS
# ════════════════════════════════════════════════════════════════════════════

def send_log(message: str, status: str = "INFO") -> None:
    try:
        _start_log_worker()
        _LOG_Q.put_nowait((message, status))
    except queue.Full:
        pass
    except Exception:
        pass


def send_module_status(module: str, status: str, message: str = ""):
    try:
        requests.post(
            f"{BACKEND_URL}/test/module-status",
            json={"module": module, "status": status, "message": message},
            timeout=3,
        )
    except Exception:
        pass


def notify_allure_open() -> None:
    try:
        requests.post(f"{BACKEND_URL}/api/allure/start", timeout=10)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════════
#  STOP
# ════════════════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════════════════
#  REPORT GENERATION
# ════════════════════════════════════════════════════════════════════════════

def generate_report(project_root: Optional[str] = None) -> None:
    """
    Generate Allure HTML report from RESULTS_DIR.

    FIX: No merge step needed — all workers already wrote directly to RESULTS_DIR.
    Previously the merge ran before tests finished (race condition) or
    pointed at the wrong directory entirely.
    """
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(__file__))

    allure_cmd = "allure"
    scoop_path = r"C:\Users\Pramo\scoop\shims\allure.cmd"
    if os.path.exists(scoop_path):
        allure_cmd = scoop_path
    elif shutil.which("allure.cmd"):
        allure_cmd = "allure.cmd"

    results_abs = os.path.join(project_root, RESULTS_DIR)
    report_abs  = os.path.join(project_root, REPORT_DIR)

    # Verify results exist before generating
    json_files = glob.glob(os.path.join(results_abs, "*.json"))
    print(f"[Report] Found {len(json_files)} result file(s) in {results_abs}")
    if not json_files:
        send_log(
            f"⚠️  No result JSON files found in {results_abs}. "
            "Report will be empty. Check ALLURE_RESULTS_DIR env var.",
            "WARN"
        )

    try:
        send_log("Generating Allure HTML report...", "INFO")
        subprocess.run(
            [allure_cmd, "generate", results_abs, "-o", report_abs, "--clean"],
            cwd=project_root,
            check=True,
            shell=True,
        )
        send_log("✅ Allure HTML report generated.", "SUCCESS")

        send_log("Opening Allure report in browser...", "INFO")
        subprocess.Popen(
            [allure_cmd, "open", report_abs],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
    except Exception as e:
        send_log(f"Failed to generate/open report: {e}", "FAILED")
        print(f"Report Generation Error: {e}")


# ════════════════════════════════════════════════════════════════════════════
#  MAIN TEST RUNNER
# ════════════════════════════════════════════════════════════════════════════

def run_tests_and_get_suggestions(
    apk_path: str,
    tests_to_run: Optional[List[Dict[str, str]]] = None,
    app_type: Optional[str] = None,
    module_names: Optional[List[str]] = None,
    app_name: Optional[str] = None,
    app_version: Optional[str] = None,
    developer_name: Optional[str] = None,
) -> None:
    global STOP_FLAG, _DEVICE_MAPPING
    STOP_FLAG = False

    project_root = os.path.dirname(os.path.dirname(__file__))

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

    current_servers = get_servers()
    if not current_servers:
        send_log(
            "❌ NO APPIUM SERVERS RUNNING — Start Appium with devices first! "
            "Run /appium/start endpoint to start servers.",
            "FAILED",
        )
        return

    _DEVICE_MAPPING = {
        srv.get("port"): srv.get("device", "unknown")
        for srv in current_servers
        if srv.get("port")
    }

    # FIX: Set ALLURE_RESULTS_DIR env var so conftest._resolve_shared_alluredir()
    # picks up the same path that generate_report() will read from.
    results_abs = os.path.join(project_root, RESULTS_DIR)
    os.environ["ALLURE_RESULTS_DIR"] = results_abs

    _ensure_clean_allure_dir(project_root)
    _write_allure_environment(project_root, current_servers, app_name or "", app_version or "")

    final_test_list = tests_to_run or []
    if not final_test_list:
        send_log("⚠️  No valid test modules found. Aborting.", "FAILED")
        return

    valid_paths: List[str] = []
    path_to_name_map: Dict[str, str] = {}

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
        full_path = p.resolve() if p.is_absolute() else (BASE_DIR / path).resolve()

        print(f"Checking path:")
        print(f"   Input:  {path}")
        print(f"   Full:   {full_path}")
        print(f"   Exists: {full_path.exists()}\n")

        if full_path.exists():
            valid_paths.append(str(full_path))
            path_to_name_map[str(full_path)] = name
            send_module_status(name, "pending", "Waiting in queue...")
        else:
            send_log(f"❌ Script not found: {path}", "FAILED")

    if not valid_paths:
        send_log("❌ No valid scripts to execute. Check test file paths.", "FAILED")
        return

    try:
        import requests as _req
        _req.post(
            f"{BACKEND_URL}/test/module-status",
            json={"module": "__RUN_START__", "status": "start", "message": ""},
            timeout=2,
        )
    except Exception:
        pass

    device_mapping = get_device_mapping()
    workers = max(1, len(current_servers))

    print(f"\n{'='*70}")
    print(f"🚀 TEST EXECUTION STARTING")
    print(f"{'='*70}")
    print(f"   📦 APK: {os.path.basename(apk_path)}")
    print(f"   📱 Connected Devices: {len(current_servers)}")
    for device, port in device_mapping.items():
        os_ver = _get_android_os_version(device)
        print(f"      • {device:20} → Appium port {port}  [{os_ver}]")
    print(f"   ⚙️  Parallel Workers: {workers}")
    print(f"   📋 Test Modules: {len(valid_paths)}")
    print(f"{'='*70}\n")
    print(f"[DIRS] All workers writing to: {results_abs}")

    send_log(
        f"[Parallel] Running with {workers} worker(s) across {len(current_servers)} device(s)",
        "INFO",
    )
    for device, port in device_mapping.items():
        send_log(f"   📱 {device} → Appium server on port {port}", "INFO")

    try:
        import xdist
        use_parallel = True
    except ImportError:
        use_parallel = False

    # ── FIX: Pass INDIVIDUAL FILE PATHS (not directory) ───────────────────
    #
    # BEFORE (broken):
    #   test_dirs = [".../regular_farmer_test_cases"]   ← 1 item
    #   With --dist=each, xdist schedules the directory as ONE item → "2 workers [1 item]"
    #   Both workers end up running only the first collected test.
    #
    # AFTER (fixed):
    #   pytest_target_paths = [".../test_login.py", ".../test_onboarding.py"]  ← N items
    #   With --dist=each, xdist sees N items and sends ALL N to EACH worker.
    #   → "2 workers [2 items]" (or however many test files you have)
    #
    pytest_target_paths = valid_paths  # individual .py file paths

    pytest_args = pytest_target_paths + [
        f"--apk={apk_path}",
        "-v",
        f"--alluredir={results_abs}",   # FIX: explicit absolute path
    ]

    try:
        import pytest_rerunfailures  # type: ignore
        pytest_args += ["--reruns", "1"]
        send_log("🔁 Reruns enabled (pytest-rerunfailures detected)", "INFO")
    except ImportError:
        send_log("⚠️ pytest-rerunfailures not installed → skipping reruns", "WARN")

    if use_parallel and workers > 1:
        pytest_args += ["-n", str(workers), "--dist=each"]
        send_log(
            f"🚀 Running in PARALLEL: {workers} workers, FULL SUITE on EACH device",
            "INFO"
        )
        send_log(f"   Test files: {[os.path.basename(p) for p in pytest_target_paths]}", "INFO")
    else:
        send_log("⚠️ Running in SEQUENTIAL mode (xdist not installed or 1 device)", "WARN")

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
        project_root=project_root,
        current_servers=current_servers,
    )

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


# ════════════════════════════════════════════════════════════════════════════
#  PYTEST SUBPROCESS
# ════════════════════════════════════════════════════════════════════════════

def run_pytest_streaming_with_tracking(
    pytest_args: list,
    path_mapping: dict,
    project_root: Optional[str] = None,
    current_servers: Optional[list] = None,
) -> bool:
    """
    Execute pytest in a subprocess and stream output to the UI.

    FIX: Removed `clean_allure` parameter and --clean-alluredir flag.
    _ensure_clean_allure_dir() already wiped the dir before this is called.
    Passing --clean-alluredir here would delete all results written by gw0
    when gw1 starts up (race condition), leaving 0 items in the report.
    """
    global CURRENT_PROC, STOP_FLAG

    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(__file__))

    backend_dir = os.path.join(project_root, "backend")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = backend_dir + os.pathsep + existing if existing else backend_dir

    results_abs = os.path.join(project_root, RESULTS_DIR)

    env.update({
        "PYTHONIOENCODING":        "utf-8",
        "PYTHONUTF8":              "1",
        "PYTHONUNBUFFERED":        "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG":   "en_US.UTF-8" if os.name != "nt" else "",
        "LC_ALL": "en_US.UTF-8" if os.name != "nt" else "",
        # FIX: Tell conftest where to write results (absolute path)
        "ALLURE_RESULTS_DIR": results_abs,
    })

    if os.name == "nt":
        env = {k: v for k, v in env.items() if v}

    cmd = [
        sys.executable, "-u", "-m", "pytest",
        "-p", "allure_pytest",
        "-p", "xdist",
        "-p", "pytest_rerunfailures",
        "-s", "-v", "--tb=short",
        # NOTE: --alluredir already in pytest_args (absolute path)
        # NOTE: --clean-alluredir intentionally REMOVED (see docstring)
        "-o", "log_cli=true",
        "-o", "log_cli_level=INFO",
    ]
    cmd += pytest_args

    print(f"\n[pytest] Command:")
    print(f"   {' '.join(cmd)}\n")

    CURRENT_PROC = subprocess.Popen(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        encoding="utf-8",
        errors="replace",
    )

    active_module_name = None
    failed_modules: set = set()

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
        send_log(f"⚠️  Unicode error in output: {e}", "WARNING")
    except Exception as e:
        print(f"❌ Error reading test output: {e}")
        send_log(f"⚠️  Error reading test output: {e}", "WARNING")

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

    apk_arg      = sys.argv[1]
    app_type_arg = sys.argv[2] if len(sys.argv) > 2 else None
    modules_arg  = sys.argv[3:] if len(sys.argv) > 3 else None

    run_tests_and_get_suggestions(
        apk_path=apk_arg,
        app_type=app_type_arg,
        module_names=modules_arg,
    )