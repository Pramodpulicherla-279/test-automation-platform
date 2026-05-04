import os
import sys
import shutil

# Disable auto-loading of 3rd-party pytest plugins (like browserstack)
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

# FIX: use get_servers() from appium_state (reads shared JSON file) instead of
# directly importing appium_servers from manager (stale list binding).
from new_backend.modules.appium_grid.appium_state import (
    get_servers,
    get_device_for_port,
    get_device_mapping
)
import glob  
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

# ── Directory constants ────────────────────────────────────────────────────────
RESULTS_DIR = "allure-results"          # final merged results (single source of truth)
REPORT_DIR  = "allure-report"

# Per-device subdirectory prefix — each worker writes here, then we merge
# e.g.  allure-results-device/emulator-5554/
_PER_DEVICE_RESULTS_ROOT = "allure-results-device"

# --- Log queue + worker -------------------------------------------------------
_LOG_Q: "queue.Queue[tuple[str, str]]" = queue.Queue(maxsize=5000)
_LOG_WORKER_STARTED = False

_DEVICE_MAPPING: Dict[int, str] = {}   # port -> device_id


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

def _ensure_clean_allure_dirs(project_root: str, current_servers: list) -> None:
    """
    Create a clean per-device results directory for each connected device
    AND wipe the merged RESULTS_DIR so the new run starts fresh.

    Layout:
        allure-results/                  ← merged (generated after run)
        allure-results-device/
            emulator-5554/               ← pytest worker gw0 writes here
            emulator-5556/               ← pytest worker gw1 writes here
    """
    # Wipe + recreate the final merged dir
    # ── SAFE HISTORY PRESERVATION ─────────────────────────────
    merged = os.path.join(project_root, RESULTS_DIR)
    history_path = os.path.join(merged, "history")
    temp_history = os.path.join(project_root, "temp_history")
    
    # Clean previous temp history
    if os.path.exists(temp_history):
        shutil.rmtree(temp_history, ignore_errors=True)
    
    # Backup history if exists
    if os.path.isdir(history_path):
        shutil.copytree(history_path, temp_history)
    
    # Remove old merged results
    if os.path.isdir(merged):
        shutil.rmtree(merged, ignore_errors=True)
    
    os.makedirs(merged, exist_ok=True)
    
    # Restore history
    if os.path.exists(temp_history):
        shutil.copytree(temp_history, os.path.join(merged, "history"))
        shutil.rmtree(temp_history, ignore_errors=True)

    # Wipe + recreate per-device dirs
    device_root = os.path.join(project_root, _PER_DEVICE_RESULTS_ROOT)
    if os.path.isdir(device_root):
        shutil.rmtree(device_root, ignore_errors=True)
    os.makedirs(device_root, exist_ok=True)

    for srv in current_servers:
        device = srv.get("device", "unknown")
        d = os.path.join(device_root, device)
        os.makedirs(d, exist_ok=True)
        print(f"[ALLURE] Created per-device dir: {d}")

    # Wipe old HTML report
    report_path = os.path.join(project_root, REPORT_DIR)
    if os.path.isdir(report_path):
        shutil.rmtree(report_path, ignore_errors=True)


def _get_device_alluredir(project_root: str, device_id: str) -> str:
    """Return the per-device allure results path for a given device."""
    return os.path.join(project_root, _PER_DEVICE_RESULTS_ROOT, device_id)


def _merge_device_results(project_root: str, current_servers: list) -> None:
    import json as _json
    import glob

    merged_dir = os.path.join(project_root, RESULTS_DIR)
    device_root = os.path.join(project_root, _PER_DEVICE_RESULTS_ROOT)

    total_copied = 0

    for srv in current_servers:
        device = srv.get("device", "unknown")

        # 🔥 HANDLE WORKER DIRS (emulator-5554_gw0)
        device_pattern = os.path.join(device_root, f"{device}*")
        matching_dirs = glob.glob(device_pattern)

        if not matching_dirs:
            print(f"[MERGE] No results dir for {device} — skipping")
            continue

        for src_dir in matching_dirs:
            if not os.path.isdir(src_dir):
                continue

            print(f"[MERGE] Processing → {src_dir}")

            result_files = glob.glob(os.path.join(src_dir, "*.json"))
            attachment_files = [
                f for f in glob.glob(os.path.join(src_dir, "*"))
                if not f.endswith(".json")
            ]

            # ✅ PROCESS RESULTS PER DIRECTORY (FIXED)
            for rf in result_files:
                try:
                    with open(rf, "r", encoding="utf-8") as fh:
                        data = _json.load(fh)

                    labels = data.get("labels", [])
                    labels = [l for l in labels if l.get("name") != "device"]
                    labels.append({"name": "device", "value": device})
                    data["labels"] = labels

                    dest_rf = os.path.join(merged_dir, os.path.basename(rf))

                    # 🔥 PREVENT OVERWRITE
                    if os.path.exists(dest_rf):
                        base, ext = os.path.splitext(os.path.basename(rf))
                        dest_rf = os.path.join(
                            merged_dir,
                            f"{device}_{base}{ext}"
                        )

                    with open(dest_rf, "w", encoding="utf-8") as fh:
                        _json.dump(data, fh, ensure_ascii=False)

                    total_copied += 1

                except Exception as e:
                    print(f"[MERGE] Failed to process {rf}: {e}")

            # ✅ COPY ATTACHMENTS
            for af in attachment_files:
                try:
                    dest = os.path.join(merged_dir, os.path.basename(af))

                    if os.path.exists(dest):
                        base, ext = os.path.splitext(os.path.basename(af))
                        dest = os.path.join(
                            merged_dir,
                            f"{device}_{base}{ext}"
                        )

                    shutil.copy2(af, dest)

                except Exception as e:
                    print(f"[MERGE] Attachment copy failed {af}: {e}")

    print(f"[MERGE] Copied {total_copied} result file(s)")

# ════════════════════════════════════════════════════════════════════════════
#  ALLURE ENVIRONMENT FILE  (shows in Allure Overview tab)
# ════════════════════════════════════════════════════════════════════════════

def _write_allure_environment(
    project_root: str,
    current_servers: list,
    app_name: str = "",
    app_version: str = "",
) -> None:
    """
    Write allure-results/environment.properties.
    One block per device so the Allure Overview shows ALL devices.

    Example output:
        device.count=2
        device.0.id=emulator-5554
        device.0.port=4723
        device.0.os=Android 13
        device.1.id=emulator-5556
        device.1.port=4725
        device.1.os=Android 12
        app.name=Krishivaas Farmer
        app.version=1.3.96
    """
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
    """
    Query the real Android OS version from a connected device via ADB.
    Returns e.g. 'Android 13 (API 33)' or 'Android Unknown' on failure.
    """
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
    """Merge per-device results → generate unified Allure HTML report."""
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(__file__))

    # ── 1. Merge per-device result dirs into RESULTS_DIR ──────────────────
    current_servers = get_servers()
    if current_servers:
        send_log(f"[Report] Merging results from {len(current_servers)} device(s)...", "INFO")
        _merge_device_results(project_root, current_servers)
    else:
        send_log("[Report] No device mapping — using existing allure-results as-is", "WARN")

    # ── 2. Locate allure executable ────────────────────────────────────────
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
            shell=True,
        )
        send_log("✅ Allure HTML report generated.", "SUCCESS")

        send_log("Opening Allure report in browser...", "INFO")
        subprocess.Popen(
            [allure_cmd, "open", REPORT_DIR],
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

    # ── Device validation ──────────────────────────────────────────────────
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

    # ── Clean dirs + write environment file ───────────────────────────────
    _ensure_clean_allure_dirs(project_root, current_servers)
    _write_allure_environment(project_root, current_servers, app_name or "", app_version or "")

    # ── Resolve test paths ─────────────────────────────────────────────────
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

    # ── Log device map to UI ───────────────────────────────────────────────
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

    send_log(
        f"[Parallel] Running with {workers} worker(s) across {len(current_servers)} device(s)",
        "INFO",
    )
    for device, port in device_mapping.items():
        send_log(f"   📱 {device} → Appium server on port {port}", "INFO")

    # ── Detect xdist ──────────────────────────────────────────────────────
    try:
        import xdist
        use_parallel = True
    except ImportError:
        use_parallel = False

    # ── Build pytest args ─────────────────────────────────────────────────
    #
    # KEY FIX: each worker is told its own per-device alluredir via the
    # ALLURE_RESULTS_DIR environment variable which conftest reads.
    # The --alluredir flag still points to the MERGED dir so that allure
    # doesn't complain; the real per-device write is done inside conftest.
    #
    pytest_args = valid_paths + [
        f"--apk={apk_path}",
        "-v",
        # FIX: --alluredir was missing → pytest had no target dir and all devices
        # wrote results to a random temp location (or same flat dir), causing only
        # one device's results to survive. Point it at RESULTS_DIR (the merged
        # target); conftest routes each worker into its own per-device subdir via
        # DEVICE_RESULTS_ROOT, then _merge_device_results() copies everything here.
        f"--alluredir={os.path.join(project_root, RESULTS_DIR)}",
        f"--device-results-root={os.path.join(project_root, _PER_DEVICE_RESULTS_ROOT)}",
    ]
    
    # ✅ Add reruns ONLY if plugin is installed
    try:
        import pytest_rerunfailures  # type: ignore
        pytest_args += ["--reruns", "1"]
        send_log("🔁 Reruns enabled (pytest-rerunfailures detected)", "INFO")
    except ImportError:
        send_log("⚠️ pytest-rerunfailures not installed → skipping reruns", "WARN")
    
    if use_parallel and workers > 1:
        pytest_args += ["-n", str(workers), "--dist=each"]
        send_log(f"🚀 Running in PARALLEL with {workers} workers (FULL SUITE PER DEVICE)", "INFO")
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
        clean_allure=True,
        project_root=project_root,
        current_servers=current_servers,
    )

    # ── Post-run ───────────────────────────────────────────────────────────
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
    clean_allure: bool,
    project_root: Optional[str] = None,
    current_servers: Optional[list] = None,
) -> bool:
    """
    Execute pytest in a subprocess and stream output to the UI.

    Per-device allure results:
      - --alluredir points to allure-results (merged target, keeps allure happy)
      - The subprocess env carries DEVICE_RESULTS_ROOT so conftest.py can
        write each worker's results into allure-results-device/<device_id>/
      - After the subprocess finishes, generate_report() calls
        _merge_device_results() to copy everything into allure-results/.
    """
    global CURRENT_PROC, STOP_FLAG

    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(__file__))

    backend_dir = os.path.join(project_root, "backend")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = backend_dir + os.pathsep + existing if existing else backend_dir

    env.update({
        "PYTHONIOENCODING":       "utf-8",
        "PYTHONUTF8":             "1",
        "PYTHONUNBUFFERED":       "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG":   "en_US.UTF-8" if os.name != "nt" else "",
        "LC_ALL": "en_US.UTF-8" if os.name != "nt" else "",
        # Pass per-device root so conftest can resolve per-worker alluredir
        "DEVICE_RESULTS_ROOT": os.path.join(project_root, _PER_DEVICE_RESULTS_ROOT),
    })

    if os.name == "nt":
        env = {k: v for k, v in env.items() if v}

    cmd = [
        sys.executable, "-u", "-m", "pytest",
        "-p", "allure_pytest",
        "-p", "xdist",
        "-p", "pytest_rerunfailures",
        "-s", "-v", "--tb=short",
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