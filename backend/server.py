import os
import sys
import json
import datetime
import time
import threading
import uuid

sys.dont_write_bytecode = True
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
from pathlib import Path
import subprocess
import socket
import asyncio
from fastapi import Request
import requests
import re
from dotenv import load_dotenv
import glob
import logging
from gdrive_loader import download_apk, extract_app_icon, get_apk_info
from typing import List, Optional, Dict, Any

logger = logging.getLogger("uvicorn.error")
from starlette.websockets import WebSocketDisconnect

# ─── Global dedup tracker ────────────────────────────────────────────────────
PROCESSED_EVENTS: set = set()

# ─── Load env ────────────────────────────────────────────────────────────────
load_dotenv()
SLACK_BOT_TOKEN      = os.getenv("SLACK_BOT_TOKEN")
SLACK_NOTIFY_CHANNEL = os.getenv("SLACK_NOTIFY_CHANNEL", "")

# ─── Project root ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tests.test_runner import run_tests_and_get_suggestions, stop_current_tests, generate_report

print("server is running...")

# ─── App variant config ──────────────────────────────────────────────────────
PACKAGE_VARIANT_MAP = {
    "com.agribride.krishivaas.farmer_app":       "regular_farmer",
    "com.agribride.krishivaas.client_app":       "regular_client",
    "com.agribride.krishivaas.farmer_state_app": "state_farmer",
    "com.agribride.krishivaas.client_state_app": "state_client",
}

APP_VARIANTS = {
    "regular_farmer": [
        {"name": "Login",       "path": "tests/test_cases/regular_farmer_test_cases/test_login_pytest.py"},
        {"name": "Dashboard",   "path": "tests/test_cases/regular_farmer_test_cases/TestOnboarding.py"},
        {"name": "Add Updates", "path": "tests/farmer/test_updates.py"},
    ],
    "regular_client": [
        {"name": "Login",       "path": "tests/test_cases/regular_client_test_cases/login_pytest.py"},
        {"name": "Marketplace", "path": "tests/client/test_marketplace.py"},
        {"name": "Cart",        "path": "tests/client/test_cart.py"},
    ],
    "state_farmer": [
        {"name": "Login",   "path": "tests/state_farmer/test_login.py"},
        {"name": "Schemes", "path": "tests/state_farmer/test_schemes.py"},
    ],
    "state_client": [
        {"name": "Login",      "path": "tests/test_cases/state_client_test_cases/test_login_pytest.py"},
        {"name": "Onboarding", "path": "tests/test_cases/state_client_test_cases/test_Onboarding.py"},
    ],
}

# ─── Single source of truth for developer names ───────────────────────────────
APP_DEVELOPER_MAP = {
    "regular_farmer": "@Anuj",
    "regular_client": "@samad ahmed",
    "state_farmer":   "@Swaroopa",
    "state_client":   "@Vikash Chandra",
}

# ─── Global process handles ──────────────────────────────────────────────────
_appium_proc: subprocess.Popen | None = None
_allure_proc: subprocess.Popen | None = None
_allure_port: int | None = None
APPIUM_PORT = 4723

ALLURE_CMD = r"C:\Users\ABDUL SAMAD\scoop\shims\allure.cmd"
if not os.path.exists(ALLURE_CMD):
    raise Exception(f"Allure not found at: {ALLURE_CMD}")

DOWNLOAD_PROCESS_OBJ = None
_allure_start_lock = threading.Lock()

# ════════════════════════════════════════════════════════════════════════════
#  PER-RUN STATE STORE
# ════════════════════════════════════════════════════════════════════════════

_runs: Dict[str, Dict[str, Any]] = {}

_PAYLOAD_PREFIXES = ("AUTOMATION_PAYLOAD_JSON:", "JIRA_PAYLOAD_JSON:")


def _new_run() -> str:
    """Create a fresh isolated state bucket and return its run_id."""
    run_id = str(uuid.uuid4())
    _runs[run_id] = {
        "test_steps_store":  {},
        "pending_payloads":  [],
        "dismissed_keys":    set(),
        "current_test_name": "default",
        "report_url":        None,
        "started_at":        datetime.datetime.now().isoformat(),
    }
    return run_id


def _get_run(run_id: str) -> Dict[str, Any]:
    """Return the state bucket for run_id, or raise 404."""
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail=f"run_id '{run_id}' not found")
    return _runs[run_id]


# ─── Legacy single-run globals kept for routes that don't yet pass run_id ───
_latest_run_id: str | None = None

_jira_history:  List[dict] = []
_jira_comments: Dict[str, List[dict]] = {}


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def generate_allure_report():
    try:
        subprocess.run(
            [ALLURE_CMD, "generate", "allure-results", "-o", "allure-report", "--clean"],
            cwd=BASE_DIR,
            check=True,
            shell=True,
        )
        print("✅ Allure report generated")
    except Exception as e:
        print(f"❌ Allure generate failed: {e}")


def log_to_ui(message: str, status: str = "INFO"):
    try:
        asyncio.create_task(manager.broadcast({
            "type": "LOG",
            "payload": {"message": message, "status": status},
        }))
    except Exception:
        pass


def _is_appium_running() -> bool:
    global _appium_proc
    if _appium_proc is not None and _appium_proc.poll() is None:
        return True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", APPIUM_PORT)) == 0


async def _ensure_appium_running() -> None:
    global _appium_proc
    if _is_appium_running():
        print("[Appium] Already running.")
        return
    print("[Appium] Starting Appium server...")
    _appium_proc = subprocess.Popen(
        ["appium", "-p", str(APPIUM_PORT)],
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(15):
        await asyncio.sleep(1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", APPIUM_PORT)) == 0:
                print("[Appium] Server is ready.")
                return
    print("[Appium] WARNING: Appium did not become reachable within 15 s.")


def get_slack_user_name(user_id: str) -> str:
    try:
        resp = requests.get(
            "https://slack.com/api/users.info",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            params={"user": user_id},
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            return data["user"]["real_name"]
        print(f"[Slack] users.info error: {data.get('error')}")
    except Exception as e:
        print(f"[Slack] Could not fetch user name: {e}")
    return "Unknown Developer"


# ════════════════════════════════════════════════════════════════════════════
#  VARIANT DETECTION HELPER  ← NEW CENTRALISED FUNCTION
# ════════════════════════════════════════════════════════════════════════════

def _detect_app_variant(package_name: str, app_name: str) -> str | None:
    """
    Detect app variant with a clear priority order:
      1. Exact package name match  (most reliable)
      2. Keyword match on app_name (fallback)
    Returns one of: 'regular_farmer', 'regular_client',
                    'state_farmer',   'state_client',  or None.
    """
    # 1 — package name (exact, case-insensitive)
    pkg_lower = (package_name or "").strip().lower()
    for pkg, variant in PACKAGE_VARIANT_MAP.items():
        if pkg.lower() == pkg_lower:
            print(f"[Variant] Detected via package_name: '{package_name}' → {variant}")
            return variant

    # 2 — app name keywords
    name_lower = (app_name or "").strip().lower()

    if "state" in name_lower and "farmer" in name_lower:
        print(f"[Variant] Detected via app_name keywords: '{app_name}' → state_farmer")
        return "state_farmer"
    if "state" in name_lower and "client" in name_lower:
        print(f"[Variant] Detected via app_name keywords: '{app_name}' → state_client")
        return "state_client"
    if "farmer" in name_lower:
        print(f"[Variant] Detected via app_name keywords: '{app_name}' → regular_farmer")
        return "regular_farmer"
    if "client" in name_lower:
        print(f"[Variant] Detected via app_name keywords: '{app_name}' → regular_client")
        return "regular_client"

    print(f"[Variant] Could not detect variant — package='{package_name}' app='{app_name}'")
    return None


# ════════════════════════════════════════════════════════════════════════════
#  ALLURE SERVER
# ════════════════════════════════════════════════════════════════════════════

def _start_allure_server() -> str:
    global _allure_proc, _allure_port

    with _allure_start_lock:
        if _allure_proc is not None and _allure_proc.poll() is None and _allure_port is not None:
            print(f"[Allure] ♻️  Reusing existing server on port {_allure_port}")
            return f"http://127.0.0.1:{_allure_port}"

        if _allure_proc is not None:
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(_allure_proc.pid)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                else:
                    _allure_proc.terminate()
            except Exception:
                pass
            _allure_proc = None

        _allure_port = _pick_free_port()
        print(f"[Allure] 🚀 Starting new server on port {_allure_port}...")
        _allure_proc = subprocess.Popen(
            [ALLURE_CMD, "open", "-h", "127.0.0.1", "-p", str(_allure_port), ALLURE_REPORT_DIR],
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        time.sleep(2)
        return f"http://127.0.0.1:{_allure_port}"


# ════════════════════════════════════════════════════════════════════════════
#  VERCEL DEPLOY
# ════════════════════════════════════════════════════════════════════════════

def deploy_to_vercel(run_id: str) -> str | None:
    allure_report_path = os.path.join(BASE_DIR, "allure-report")
    if not os.path.isdir(allure_report_path):
        print(f"[Vercel] allure-report folder not found: {allure_report_path}")
        return None

    unique_name = f"allure-{run_id[:8]}"
    print(f"[Vercel] Deploying as project name: {unique_name} ...")

    try:
        result = subprocess.run(
            ["vercel", "--prod", "--yes", "--name", unique_name],
            cwd=allure_report_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            shell=True,
        )
        print(result.stdout)
        print(result.stderr)

        if result.returncode != 0:
            print(f"[Vercel] Deploy failed: {result.stderr}")
            return None

        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("https://"):
                print(f"[Vercel] ✅ Fresh URL: {line}")
                return line

    except subprocess.TimeoutExpired:
        print("[Vercel] Deploy timed out after 300 seconds.")
    except Exception as e:
        print(f"[Vercel] Exception: {e}")

    return None


# ════════════════════════════════════════════════════════════════════════════
#  SLACK NOTIFICATION
# ════════════════════════════════════════════════════════════════════════════

def send_slack_message(
    channel_id:     str,
    developer_name: str,
    app_name:       str,
    apk_version:    str,
    passed:         int,
    failed:         int,
    report_url:     str,
) -> None:
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    safe_url = report_url if (report_url or "").startswith("https://") else "https://allure-report-three.vercel.app"
    status_line = f"*🟢 Passed:* {passed}    *🔴 Failed:* {failed}"

    payload = {
        "channel": channel_id,
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🚀 Automation Report Ready!", "emoji": True},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*👤 Developer*\n{developer_name}"},
                    {"type": "mrkdwn", "text": f"*📱 App*\n{app_name}"},
                    {"type": "mrkdwn", "text": f"*🔖 Version*\n{apk_version}"},
                    {"type": "mrkdwn", "text": f"*📊 Results*\n{status_line}"},
                ],
            },
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "open_report",
                        "text": {"type": "plain_text", "text": "📄 Open Report", "emoji": True},
                        "url": safe_url,
                        "style": "primary",
                    }
                ],
            },
        ],
        "text": f"Automation report for {app_name} v{apk_version} — Passed: {passed}, Failed: {failed}",
    }

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers=headers,
        json=payload,
        timeout=10,
    )
    data = response.json()
    if not data.get("ok"):
        print(f"[Slack] chat.postMessage error: {data.get('error')} | {data.get('response_metadata')}")
    else:
        print(f"[Slack] Message sent successfully to {channel_id}")


def extract_drive_file_id(text: str) -> str | None:
    text = text.replace("<", "").replace(">", "")
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', text)
    return match.group(1) if match else None


# ════════════════════════════════════════════════════════════════════════════
#  BROADCAST HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _broadcast_async(message: dict) -> None:
    try:
        asyncio.create_task(manager.broadcast(message))
    except RuntimeError:
        pass


async def _broadcast_all_steps_to_frontend(run_id: str) -> None:
    run = _runs.get(run_id, {})
    store = run.get("test_steps_store", {})

    if not store:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": "ℹ️ No test steps were captured.", "status": "INFO"},
        })
        return

    total_steps = sum(len(v) for v in store.values())

    await manager.broadcast({
        "type": "STEPS_SUMMARY",
        "payload": {
            "run_id":        run_id,
            "steps_by_test": store,
            "total_steps":   total_steps,
        },
    })

    await manager.broadcast({
        "type": "LOG",
        "payload": {
            "message": f"📋 Steps Summary — {total_steps} step(s) across {len(store)} test(s):",
            "status": "INFO",
        },
    })

    for test_name, steps in store.items():
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"  🧪 {test_name}  ({len(steps)} steps)", "status": "INFO"},
        })
        for i, step in enumerate(steps, 1):
            await manager.broadcast({
                "type": "LOG",
                "payload": {"message": f"      {i}. {step}", "status": "STEP"},
            })


# ════════════════════════════════════════════════════════════════════════════
#  CORE POST-RUN PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def _run_post_notify(**kwargs) -> None:
    asyncio.run(_post_run_notify(**kwargs))


async def _post_run_notify(
    run_id:         str,
    apk_path:       str,
    tests_to_run:   list,
    app_name:       str,
    app_version:    str,
    developer_name: str,
    channel_id:     str,
) -> None:
    loop = asyncio.get_event_loop()

    await manager.broadcast({
        "type": "MODULES",
        "payload": {"run_id": run_id, "modules": tests_to_run},
    })

    # ── Step 1 — run tests ───────────────────────────────────────────────────
    log_to_ui(f"[{run_id[:8]}] Step 1: Running tests...", "INFO")
    try:
        await loop.run_in_executor(
            None,
            lambda: run_tests_and_get_suggestions(apk_path, tests_to_run=tests_to_run),
        )
        log_to_ui(f"[{run_id[:8]}] Step 1 done", "SUCCESS")
    except Exception as e:
        log_to_ui(f"[{run_id[:8]}] Step 1 FAILED: {e}", "ERROR")
        await manager.broadcast({"type": "LOG", "payload": {
            "message": f"[PostRun] Tests failed: {e}", "status": "FAILED",
        }})
        return

    await manager.broadcast({
        "type": "MODULES",
        "payload": {"run_id": run_id, "modules": tests_to_run},
    })

    # ── Step 2 — generate Allure report ──────────────────────────────────────
    log_to_ui(f"[{run_id[:8]}] Step 2: Generating Allure report...", "INFO")
    try:
        await loop.run_in_executor(None, generate_allure_report)
        log_to_ui(f"[{run_id[:8]}] Step 2 done", "SUCCESS")
    except Exception as e:
        log_to_ui(f"[{run_id[:8]}] Step 2 FAILED: {e}", "ERROR")

    # ── Step 3 — count pass/fail ──────────────────────────────────────────────
    passed = failed = 0
    try:
        results_dir = os.path.join(BASE_DIR, "allure-results")
        for json_file in glob.glob(os.path.join(results_dir, "*-result.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                result_data = json.load(f)
            status = result_data.get("status", "").upper()
            if status == "PASSED":
                passed += 1
            else:
                failed += 1
        log_to_ui(f"[{run_id[:8]}] Step 3 done. Passed: {passed} | Failed: {failed}", "SUCCESS")
    except Exception as e:
        print(f"[PostRun] Step 3 FAILED: {e}")

    # ── Broadcast captured steps for this run ────────────────────────────────
    await _broadcast_all_steps_to_frontend(run_id)

    # ── Step 4 — resolve report URL ──────────────────────────────────────────
    print(f"[{run_id[:8]}] Step 4: Resolving report URL...")
    local_url  = await loop.run_in_executor(None, _start_allure_server)
    vercel_url = await loop.run_in_executor(None, lambda: deploy_to_vercel(run_id))

    report_url = vercel_url if vercel_url else local_url
    print(f"[{run_id[:8]}] Step 4: Report URL → {report_url}")

    if run_id in _runs:
        _runs[run_id]["report_url"] = report_url

    # ── Step 5 — send Slack notification ─────────────────────────────────────
    final_channel_id = channel_id or SLACK_NOTIFY_CHANNEL
    print(f"[{run_id[:8]}] Final channel_id: {final_channel_id}")

    if not final_channel_id:
        print("[ERROR] No Slack channel found even after fallback")
        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": "⚠️ Slack notification skipped: No channel_id found",
                "status": "WARN",
            },
        })
        return

    print(f"[{run_id[:8]}] Step 5: Sending Slack notification...")
    print(f"[FINAL DEBUG] developer_name = '{developer_name}'")

    try:
        await loop.run_in_executor(
            None,
            lambda: send_slack_message(
                channel_id=final_channel_id,
                developer_name=developer_name,
                app_name=app_name or "Unknown App",
                apk_version=app_version or "Unknown",
                passed=passed,
                failed=failed,
                report_url=report_url,
            ),
        )
        log_to_ui(f"[{run_id[:8]}] Step 5 done. Slack notification sent", "SUCCESS")
        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": f"✅ Slack report sent! Passed: {passed} | Failed: {failed}",
                "status": "INFO",
            },
        })
    except Exception as e:
        print(f"[PostRun] Step 5 FAILED: {e}")
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"⚠️ Slack notification failed: {e}", "status": "WARN"},
        })


# ════════════════════════════════════════════════════════════════════════════
#  SLACK APK HANDLER  ← FIXED: uses _detect_app_variant + APP_DEVELOPER_MAP
# ════════════════════════════════════════════════════════════════════════════

async def _handle_slack_apk(
    file_id: str,
    channel_id: str,
    sender_user_id: str,
) -> None:
    run_id = _new_run()
    print(f"[Slack] New run_id: {run_id} for file_id: {file_id}")

    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    try:
        loop = asyncio.get_event_loop()
        apk_path = await loop.run_in_executor(None, lambda: download_apk(download_url))

        info = get_apk_info(apk_path) or {}
        print(f"[APK Info] {info}")

        package_name = (info.get("package_name") or "").strip()
        app_name     = (info.get("app_name") or info.get("application") or "Unknown App").strip()
        apk_version  = (
            info.get("version_name")
            or info.get("versionName")
            or info.get("version_code")
            or info.get("versionCode")
            or info.get("apk_version")
            or "Unknown"
        )

        # ── FIX: single reliable variant detection ───────────────────────────
        app_variant  = _detect_app_variant(package_name, app_name)
        tests_to_run = APP_VARIANTS.get(app_variant, [])

        # ── FIX: always look up from APP_DEVELOPER_MAP; never hardcode here ──
        developer_name = APP_DEVELOPER_MAP.get(app_variant, "Unknown Developer")

        # ── Debug logs ───────────────────────────────────────────────────────
        print(f"[DEBUG] package_name:   '{package_name}'")
        print(f"[DEBUG] app_name:       '{app_name}'")
        print(f"[DEBUG] app_variant:    '{app_variant}'")
        print(f"[DEBUG] developer_name: '{developer_name}'")
        print(f"[DEBUG] tests_to_run:   {tests_to_run}")
        print(f"[DEBUG] apk_version:    '{apk_version}'")

        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": (
                    f"[Slack] {developer_name} triggered: "
                    f"{app_name} v{apk_version} | Variant: {app_variant} | run_id: {run_id[:8]}"
                ),
                "status": "INFO",
            },
        })

        await _ensure_appium_running()

        await _post_run_notify(
            run_id=run_id,
            apk_path=apk_path,
            tests_to_run=tests_to_run,
            app_name=app_name,
            app_version=apk_version,
            developer_name=developer_name,
            channel_id=channel_id,
        )

    except Exception as e:
        print(f"[Slack] Error: {e}")
        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": f"[Slack] Error: {str(e)}",
                "status": "FAILED"
            }
        })


# ════════════════════════════════════════════════════════════════════════════
#  APP LIFESPAN
# ════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("Shutting down: Cleaning up child processes...")
    global _appium_proc, _allure_proc

    for proc in (_appium_proc, _allure_proc):
        if proc is not None:
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                else:
                    proc.kill()
            except Exception:
                pass


# ════════════════════════════════════════════════════════════════════════════
#  FASTAPI APP
# ════════════════════════════════════════════════════════════════════════════

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

APKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_apks")
os.makedirs(APKS_DIR, exist_ok=True)

ALLURE_REPORT_DIR = os.path.join(BASE_DIR, "allure-report")
os.makedirs(ALLURE_REPORT_DIR, exist_ok=True)
app.mount("/allure-report", StaticFiles(directory=ALLURE_REPORT_DIR, html=True), name="allure-report")

UI_SCREENSHOTS_BASE = Path(__file__).resolve().parents[1] / "artifacts" / "ui_screenshots"
UI_SCREENSHOTS_BASE.mkdir(parents=True, exist_ok=True)

ALLURE_RESULTS_DIR = os.path.join(BASE_DIR, "allure-results")
os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
app.mount("/allure-results", StaticFiles(directory=ALLURE_RESULTS_DIR), name="allure-results")
app.mount("/ui-screenshots", StaticFiles(directory=str(UI_SCREENSHOTS_BASE)), name="ui-screenshots")


# ─── Models ───────────────────────────────────────────────────────────────────

class AnalyzeReq(BaseModel):
    run_id: str | None = None

class RunCompleteEvent(BaseModel):
    report_url: str

class ExistingTestRequest(BaseModel):
    apk_name:     str
    tests_to_run: Optional[List[Dict[str, str]]] = None

class LogMessage(BaseModel):
    message:  str
    status:   str = "INFO"
    run_id:   Optional[str] = None

class TestRequest(BaseModel):
    url:          str
    tests_to_run: Optional[List[Dict[str, str]]] = None

class JiraPayloadRequest(BaseModel):
    run_id:          Optional[str]       = None
    ticket_id:       Optional[str]       = None
    issue_id:        Optional[str]       = None
    app_name:        Optional[str]       = None
    app_version:     Optional[str]       = None
    module:          Optional[str]       = None
    feature:         Optional[str]       = None
    issue_summary:   Optional[str]       = None
    title:           Optional[str]       = None
    test_name:       Optional[str]       = None
    test_id:         Optional[str]       = None
    steps_executed:  Optional[List[Any]] = None
    developer_name:  Optional[str]       = None
    description:     Optional[str]       = None
    start_date:      Optional[str]       = None
    end_date:        Optional[str]       = None
    fix_version:     Optional[List[str]] = None
    affects_version: Optional[List[str]] = None
    sprint:          Optional[str]       = None

class JiraCreateRequest(BaseModel):
    run_id:          Optional[str]       = None
    app_name:        Optional[str]       = None
    app_version:     Optional[str]       = None
    module:          Optional[str]       = None
    feature:         Optional[str]       = None
    issue_summary:   Optional[str]       = None
    test_name:       Optional[str]       = None
    test_id:         Optional[str]       = None
    steps_executed:  Optional[List[Any]] = None
    developer_name:  Optional[str]       = None
    title:           Optional[str]       = None
    description:     Optional[str]       = None
    parent:          Optional[str]       = None
    fix_version:     Optional[List[str]] = None
    affects_version: Optional[List[str]] = None
    priority:        Optional[str]       = None
    issue_id:        Optional[str]       = None
    issue_url:       Optional[str]       = None
    ticket_id:       Optional[str]       = None
    start_date:      Optional[str]       = None
    end_date:        Optional[str]       = None
    sprint:          Optional[str]       = None

class JiraEnhanceRequest(BaseModel):
    run_id:          Optional[str]       = None
    ticket_id:       Optional[str]       = None
    issue_id:        Optional[str]       = None
    title:           Optional[str]       = None
    test_name:       Optional[str]       = None
    test_id:         Optional[str]       = None
    app_name:        Optional[str]       = None
    app_version:     Optional[str]       = None
    module:          Optional[str]       = None
    feature:         Optional[str]       = None
    description:     Optional[str]       = None
    steps_executed:  Optional[List[Any]] = None
    developer_name:  Optional[str]       = None
    start_date:      Optional[str]       = None
    end_date:        Optional[str]       = None
    sprint:          Optional[str]       = None
    affects_version: Optional[List[str]] = None
    fix_version:     Optional[List[str]] = None


# ─── WebSocket Connection Manager ─────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            try:
                self.active_connections.remove(websocket)
            except ValueError:
                pass

    async def broadcast(self, message: dict):
        async with self._lock:
            connections = list(self.active_connections)
        if not connections:
            return

        async def _safe_send(ws: WebSocket):
            try:
                await ws.send_json(message)
                return True
            except Exception:
                return False

        results = await asyncio.gather(*(_safe_send(ws) for ws in connections), return_exceptions=True)
        for ws, ok in zip(connections, results):
            if ok is not True:
                await self.disconnect(ws)


manager = ConnectionManager()


# ════════════════════════════════════════════════════════════════════════════
#  STEP HELPERS  (per-run)
# ════════════════════════════════════════════════════════════════════════════

def _resolve_steps_for_test(run_id: str, test_name: str) -> List[str]:
    if run_id not in _runs:
        return []
    store = _runs[run_id]["test_steps_store"]
    if test_name and test_name in store:
        steps = store.pop(test_name)
        print(f"✅ Steps resolved (exact) → [{run_id[:8]}] {test_name}: {steps}")
        return steps
    if "default" in store:
        steps = store.pop("default")
        print(f"✅ Steps resolved (default fallback) → [{run_id[:8]}] {test_name}: {steps}")
        return steps
    print(f"⚠️  No steps in store for [{run_id[:8]}] {test_name}")
    return []


def _make_dismiss_key(payload: dict) -> str:
    tn = str(payload.get("test_name") or "").strip()
    md = str(payload.get("module")    or "").strip()
    if tn:
        return f"tn::{md}::{tn}"
    title = str(payload.get("issue_summary") or payload.get("title") or "").strip()
    return f"sum::{md}::{title}"


# ════════════════════════════════════════════════════════════════════════════
#  UI SCREENSHOT ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def _latest_screenshot_run_id() -> str:
    runs = [p for p in UI_SCREENSHOTS_BASE.iterdir() if p.is_dir()]
    if not runs:
        raise HTTPException(404, detail="No UI screenshots found. Run tests and capture screenshots first.")
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].name


@app.post("/api/ui-screenshots/analyze")
def analyze_ui_screenshots(req: AnalyzeReq):
    print("UI parser api called")
    run_id  = req.run_id or _latest_screenshot_run_id()
    run_dir = UI_SCREENSHOTS_BASE / run_id
    if not run_dir.exists():
        raise HTTPException(404, detail=f"Run screenshots folder not found: {run_id}")

    validator = Path(__file__).resolve().parents[1] / "ui-parser" / "ui_screenshot_validator.py"
    if not validator.exists():
        raise HTTPException(500, detail=f"Validator script not found: {validator}")

    cmd  = [sys.executable, str(validator), "--root-dir", str(run_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    if proc.returncode != 0:
        raise HTTPException(500, detail=f"UI validator failed: {proc.stderr.strip() or proc.stdout.strip()}")

    payload = json.loads(proc.stdout or "{}")
    results = payload.get("results", [])

    for r in results:
        rel = r.get("relative_path")
        r["screenshot_url"] = f"/ui-screenshots/{run_id}/{rel}" if rel else None

    return {"run_id": run_id, "results": results}


# ════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/run-complete")
async def run_complete(event: RunCompleteEvent):
    await manager.broadcast({"type": "RUN_COMPLETE", "payload": {"report_url": event.report_url}})
    return {"ok": True}


@app.get("/api/app-variants")
async def get_app_variants():
    return {
        "variants": APP_VARIANTS,
        "package_variant_map": PACKAGE_VARIANT_MAP,
    }


@app.get("/api/jira/test-connection")
async def jira_test_connection():
    import requests as req_lib
    from jira_integration.jira_config import config as jira_config
    from requests.auth import HTTPBasicAuth

    base = {
        "jira_url":         jira_config.url or "(not set)",
        "jira_email":       jira_config.email or "(not set)",
        "jira_project_key": jira_config.project_key or "(not set)",
        "jira_token_set":   bool(jira_config.api_token),
        "jira_enabled":     jira_config.enabled,
    }
    if not all([jira_config.url, jira_config.email, jira_config.api_token]):
        return {**base, "status": "MISSING_CONFIG", "message": "One or more required .env variables not set"}

    try:
        me = req_lib.get(
            f"{jira_config.url}/rest/api/3/myself",
            auth=HTTPBasicAuth(jira_config.email, jira_config.api_token),
            headers={"Accept": "application/json"},
            timeout=10,
        )
        if me.status_code == 401:
            return {**base, "status": "AUTH_FAILED",
                    "message": f"401 Unauthorized. Generate a new token at: https://id.atlassian.com/manage-profile/security/api-tokens | Current email: {jira_config.email}"}
        if me.status_code != 200:
            return {**base, "status": f"AUTH_ERROR_{me.status_code}", "message": me.text[:200]}
        user = me.json()
        base["jira_account"]    = user.get("displayName")
        base["jira_account_id"] = user.get("accountId")
    except Exception as e:
        return {**base, "status": "CONNECTION_ERROR", "message": str(e)}

    try:
        proj = req_lib.get(
            f"{jira_config.url}/rest/api/3/project/{jira_config.project_key}",
            auth=HTTPBasicAuth(jira_config.email, jira_config.api_token),
            headers={"Accept": "application/json"},
            timeout=10,
        )
        if proj.status_code == 404:
            return {**base, "status": "PROJECT_NOT_FOUND", "message": f"Project '{jira_config.project_key}' not found"}
        if proj.status_code == 403:
            return {**base, "status": "PROJECT_NO_PERMISSION", "message": f"No access to project '{jira_config.project_key}'"}
        if proj.status_code == 200:
            base["project_name"] = proj.json().get("name")
    except Exception as e:
        base["project_check"] = str(e)

    return {
        **base,
        "status": "ALL_OK",
        "message": f"Credentials OK. Connected as '{base.get('jira_account')}'. Project '{jira_config.project_key}' accessible.",
    }


@app.post("/api/allure/start")
async def allure_start():
    global _allure_proc, _allure_port

    if _allure_proc is not None and _allure_proc.poll() is None and _allure_port is not None:
        print(f"[Allure] ♻️  Reusing existing server on port {_allure_port}")
        return JSONResponse({"url": f"http://127.0.0.1:{_allure_port}"})

    if _allure_proc is not None:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_allure_proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                _allure_proc.terminate()
        except Exception:
            pass
        _allure_proc = None

    _allure_port = _pick_free_port()
    _allure_proc = subprocess.Popen(
        [ALLURE_CMD, "open", "-h", "127.0.0.1", "-p", str(_allure_port), ALLURE_REPORT_DIR],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True,
    )
    await asyncio.sleep(2)
    return JSONResponse({"url": f"http://127.0.0.1:{_allure_port}"})


@app.get("/device-status")
async def device_status():
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
        )
        lines = result.stdout.strip().splitlines()[1:]
        return {"connected": any("\tdevice" in line for line in lines)}
    except Exception:
        return {"connected": False}


@app.websocket("/ws/test-status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)


# ════════════════════════════════════════════════════════════════════════════
#  LOG-STEP
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/log-step")
async def log_step(msg: LogMessage):
    global _latest_run_id

    run_id = msg.run_id or _latest_run_id
    if run_id and run_id not in _runs:
        run_id = None

    message = msg.message

    if "[TEST_START:" in message:
        try:
            new_test = message.split("[TEST_START:")[1].split("]")[0].strip()
            if new_test and run_id and new_test != _runs[run_id]["current_test_name"]:
                _runs[run_id]["current_test_name"] = new_test
                _runs[run_id]["test_steps_store"].setdefault(new_test, [])
                print(f"🔄 Test context switched → [{run_id[:8]}] {new_test}")
                _broadcast_async({
                    "type": "LOG",
                    "payload": {"message": f"🧪 Test started: {new_test}", "status": "INFO"},
                })
        except Exception as e:
            print(f"❌ TEST_START parse warning: {e}")

    step_captured = False
    if run_id:
        try:
            current_test = _runs[run_id]["current_test_name"]
            bucket = (
                message.split("[TEST:")[1].split("]")[0].strip()
                if "[TEST:" in message else current_test
            )
            if "[FOUND]" in message:
                match = re.search(r"name='([^']+)'|name=\"([^\"]+)\"", message)
                step  = (match.group(1) or match.group(2)) if match else None
                if step:
                    store = _runs[run_id]["test_steps_store"]
                    store.setdefault(bucket, []).append(step)
                    step_num = len(store[bucket])
                    print(f"✅ Step captured → [{run_id[:8]}] {bucket}: {step}")
                    step_captured = True
                    _broadcast_async({
                        "type": "STEP_CAPTURED",
                        "payload": {
                            "run_id":      run_id,
                            "test_name":   bucket,
                            "step":        step,
                            "step_number": step_num,
                        },
                    })
                    _broadcast_async({
                        "type": "LOG",
                        "payload": {
                            "message": f"  📍 [{bucket}] Step {step_num}: {step}",
                            "status":  "STEP",
                        },
                    })
        except Exception as e:
            print(f"❌ Step capture warning: {e}")

    for prefix in _PAYLOAD_PREFIXES:
        if message.startswith(prefix):
            raw = message[len(prefix):].strip()
            try:
                payload    = json.loads(raw)
                steps      = payload.get("steps_executed") or []
                clean_line = (
                    f"[PAYLOAD] {payload.get('issue_id','')} | "
                    f"{payload.get('module','?')} | {payload.get('test_name','?')} | "
                    f"Steps ({len(steps)}): {', '.join(steps[:3]) if steps else 'none'}"
                )
                _broadcast_async({
                    "type": "LOG",
                    "payload": {"message": clean_line, "status": "PAYLOAD"},
                })
            except Exception as exc:
                logger.warning("Failed to parse payload: %s", exc)
            return {"status": "ok"}

    if not step_captured:
        _broadcast_async({"type": "LOG", "payload": {"message": message, "status": msg.status}})

    return {"status": "ok"}


@app.get("/api/jira/steps/{test_name}")
async def get_steps(test_name: str, run_id: Optional[str] = None):
    global _latest_run_id
    rid = run_id or _latest_run_id
    if not rid or rid not in _runs:
        return {"steps": [], "test_name": test_name}
    store = _runs[rid]["test_steps_store"]
    steps = store.get(test_name) or store.get("default") or []
    print(f"📤 Fetch steps → [{rid[:8]}] {test_name}: {steps}")
    return {"steps": steps, "test_name": test_name}


@app.post("/api/jira/steps")
async def add_step(data: dict):
    global _latest_run_id
    run_id    = data.get("run_id") or _latest_run_id
    test_name = data.get("test_name", "unknown")
    step      = data.get("step", "")

    if not run_id or run_id not in _runs:
        return {"status": "error", "detail": "Invalid or missing run_id"}

    store = _runs[run_id]["test_steps_store"]
    store.setdefault(test_name, [])
    if step and step not in store[test_name]:
        store[test_name].append(step)
        step_num = len(store[test_name])
        print(f"✅ Step added → [{run_id[:8]}] {test_name}: {step}")
        _broadcast_async({
            "type": "STEP_CAPTURED",
            "payload": {
                "run_id":      run_id,
                "test_name":   test_name,
                "step":        step,
                "step_number": step_num,
            },
        })
        _broadcast_async({
            "type": "LOG",
            "payload": {
                "message": f"  📍 [{test_name}] Step {step_num}: {step}",
                "status":  "STEP",
            },
        })

    return {"status": "ok", "run_id": run_id, "test_name": test_name, "step_count": len(store[test_name])}


@app.post("/api/reset-steps")
async def reset_steps(data: dict = {}):
    global _latest_run_id
    run_id = data.get("run_id") or _latest_run_id
    if run_id and run_id in _runs:
        _runs[run_id]["test_steps_store"]  = {}
        _runs[run_id]["current_test_name"] = "default"
        print(f"🧹 Step store cleared for run_id={run_id[:8]}")
    return {"status": "cleared", "run_id": run_id}


@app.post("/api/module-status")
async def module_status(data: dict):
    module = data.get("module")
    status = data.get("status")
    run_id = data.get("run_id")
    if module == "__RUN_START__":
        _broadcast_async({"type": "RUN_START", "payload": {"run_id": run_id}})
    else:
        _broadcast_async({
            "type": "MODULE",
            "payload": {
                "run_id":  run_id,
                "module":  module,
                "status":  status,
                "message": data.get("message", ""),
            },
        })
    return {"status": "ok"}


@app.post("/api/jira/payload")
async def receive_jira_payload(req: JiraPayloadRequest):
    global _latest_run_id
    run_id  = req.run_id or _latest_run_id
    payload = req.model_dump(exclude_none=False)

    incoming_steps = payload.get("steps_executed")

    if not incoming_steps:
        test_name = req.test_name or "default"
        resolved  = _resolve_steps_for_test(run_id or "", test_name)
        payload["steps_executed"] = resolved

        if resolved and payload.get("description") and "Steps Executed:" not in payload["description"]:
            steps_block = "\n\nSteps Executed:\n" + "\n".join(
                f"{i+1}. {s}" for i, s in enumerate(resolved)
            )
            payload["description"] = payload["description"] + steps_block

        logger.info("[/api/jira/payload] Injected %d steps for test=%s run_id=%s",
                    len(resolved), test_name, run_id)
    else:
        _resolve_steps_for_test(run_id or "", req.test_name or "default")
        logger.info("[/api/jira/payload] Payload already has %d steps for test=%s run_id=%s",
                    len(incoming_steps), req.test_name, run_id)

    if run_id and run_id in _runs:
        _runs[run_id]["pending_payloads"].append(payload)
    else:
        logger.warning("[/api/jira/payload] No valid run_id; payload stored globally")

    await manager.broadcast({"type": "JIRA_PAYLOAD", "payload": payload})

    logger.info("[/api/jira/payload] %s module=%s test=%s steps=%d",
                req.issue_id, req.module, req.test_name,
                len(payload.get("steps_executed") or []))

    return {"status": "received", "issue_id": req.issue_id, "module": req.module}


@app.get("/api/jira/payloads")
async def get_pending_payloads(run_id: Optional[str] = None):
    global _latest_run_id
    rid = run_id or _latest_run_id
    if not rid or rid not in _runs:
        return {"payloads": []}
    run    = _runs[rid]
    active = [
        p for p in run["pending_payloads"]
        if _make_dismiss_key(p) not in run["dismissed_keys"]
    ]
    return {"payloads": active, "run_id": rid}


@app.post("/api/jira/dismiss")
async def dismiss_payload(data: dict):
    global _latest_run_id
    run_id = data.get("run_id") or _latest_run_id
    key    = _make_dismiss_key(data)
    if run_id and run_id in _runs and key:
        _runs[run_id]["dismissed_keys"].add(key)
    return {"status": "dismissed", "key": key}


@app.post("/api/jira/create")
async def jira_create(req: JiraCreateRequest):
    from jira_integration.jira_service import create_jira_issue
    from jira_integration.jira_config  import config as jira_config

    if not jira_config.enabled:
        raise HTTPException(status_code=400, detail="Jira is disabled. Set JIRA_ENABLED=true in backend/.env")

    missing = [n for n, v in {
        "JIRA_URL":         jira_config.url,
        "JIRA_EMAIL":       jira_config.email,
        "JIRA_API_TOKEN":   jira_config.api_token,
        "JIRA_PROJECT_KEY": jira_config.project_key,
    }.items() if not v]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing .env variables: {', '.join(missing)}. Edit backend/.env and restart.")

    summary     = (req.title or req.issue_summary or "Automation Failure").strip()
    description = (req.description or "Automation Test Failure").strip()

    import io as _io, contextlib as _ctx
    _captured = _io.StringIO()
    try:
        with _ctx.redirect_stdout(_captured):
            print(f"[JIRA_CREATE] Creating ticket with dates:")
            print(f"  Start Date: {req.start_date}")
            print(f"  End Date:   {req.end_date}")
            print(f"  Sprint:     {req.sprint}")

            issue_key = create_jira_issue(
                summary=summary,
                description=description,
                app_name=req.app_name,
                app_version=req.app_version,
                module=req.module or req.parent,
                feature=req.feature,
                issue_summary=summary,
                test_name=req.test_name,
                test_id=req.test_id,
                steps_executed=req.steps_executed or [],
                developer_name=req.developer_name,
                start_date=req.start_date,
                end_date=req.end_date,
                sprint=req.sprint,
            )
    except Exception as exc:
        err = str(exc)
        logger.error("Jira create exception: %s", err)
        if "401" in err:
            raise HTTPException(status_code=400, detail=f"Jira 401 Unauthorized — wrong JIRA_EMAIL or JIRA_API_TOKEN.\nJira said: {err}")
        if "403" in err or "permission" in err.lower():
            raise HTTPException(status_code=400, detail=f"Jira 403 Forbidden — no permission to create issues.\nJira said: {err}")
        raise HTTPException(status_code=400, detail=f"Jira error: {err}")

    if not issue_key:
        raise HTTPException(status_code=400, detail="Jira returned no issue key — check all JIRA_* env vars in backend/.env")

    for _line in _captured.getvalue().splitlines():
        _line   = _line.strip()
        if not _line:
            continue
        _status = "PAYLOAD" if any(_line.startswith(p) for p in _PAYLOAD_PREFIXES) else "INFO"
        _broadcast_async({"type": "LOG", "payload": {"message": _line, "status": _status}})

    issue_url = f"{jira_config.url}/browse/{issue_key}"
    entry = {
        "issue_id":        issue_key,
        "issue_url":       issue_url,
        "title":           summary,
        "description":     description,
        "developer_name":  req.developer_name or "",
        "module":          req.module or req.parent or "",
        "app_name":        req.app_name or "",
        "app_version":     req.app_version or "",
        "test_name":       req.test_name or "",
        "ticket_id":       req.ticket_id or "",
        "fix_version":     req.fix_version or [],
        "affects_version": req.affects_version or [],
        "priority":        req.priority or "High",
        "sprint":          req.sprint or "Automation",
        "start_date":      req.start_date or "",
        "end_date":        req.end_date or "",
        "steps_executed":  req.steps_executed or [],
        "status":          "Assigned",
        "created_at":      datetime.datetime.now().isoformat(),
        "run_id":          req.run_id or _latest_run_id or "",
    }
    _jira_history.append(entry)
    _broadcast_async({"type": "JIRA_CREATED", "payload": entry})

    print(f"\n✓ JIRA Ticket Created: {issue_key}")
    print(f"  Start Date: {req.start_date}")
    print(f"  End Date:   {req.end_date}")
    print(f"  Sprint:     {req.sprint}")

    return {"issue_id": issue_key, "issue_key": issue_key, "issue_url": issue_url, **entry}


# ─── Jira history & comments ──────────────────────────────────────────────────

@app.get("/api/jira/history")
async def jira_history_api():
    return {"issues": _jira_history}


@app.get("/api/jira/comments/{issue_key}")
async def get_comments(issue_key: str):
    return {"comments": _jira_comments.get(issue_key, [])}


@app.post("/api/jira/comments/{issue_key}")
async def add_comment(issue_key: str, data: dict):
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Comment text required")
    comment = {
        "author":     data.get("author") or "QA Automation",
        "text":       text,
        "created_at": datetime.datetime.now().isoformat(),
    }
    _jira_comments.setdefault(issue_key, []).append(comment)
    _broadcast_async({"type": "JIRA_COMMENT", "payload": {"issue_key": issue_key, "comment": comment}})
    return {"status": "ok", "comment": comment}


@app.get("/jira/history")
async def jira_history_legacy():
    return {"issues": [
        {
            "key":      e.get("issue_id", ""),
            "summary":  e.get("title", ""),
            "status":   e.get("status", "Assigned"),
            "url":      e.get("issue_url", ""),
            "priority": e.get("priority", ""),
            "assignee": e.get("developer_name", ""),
            "updated":  e.get("created_at", ""),
        }
        for e in _jira_history
    ]}


@app.get("/api/health")
async def health():
    from jira_integration.jira_config import config as jira_config
    return {
        "status":            "ok",
        "jira_enabled":      jira_config.enabled,
        "jira_url":          jira_config.url or "(not set)",
        "jira_project_key":  jira_config.project_key or "(not set)",
        "jira_email":        jira_config.email or "(not set)",
        "jira_token_set":    bool(jira_config.api_token),
        "active_runs":       list(_runs.keys()),
        "latest_run_id":     _latest_run_id,
        "run_step_counts":   {rid: {k: len(v) for k, v in r["test_steps_store"].items()} for rid, r in _runs.items()},
        "pending_payloads":  {rid: len(r["pending_payloads"]) for rid, r in _runs.items()},
        "allure_port":       _allure_port,
        "allure_running":    _allure_proc is not None and _allure_proc.poll() is None,
    }


# ════════════════════════════════════════════════════════════════════════════
#  TEST RUNNER ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.post("/start-test")
async def start_test(request: TestRequest, background_tasks: BackgroundTasks):
    global DOWNLOAD_PROCESS_OBJ, _latest_run_id

    run_id        = _new_run()
    _latest_run_id = run_id

    try:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"Starting APK download... (run_id: {run_id[:8]})", "status": "INFO"},
        })

        script_path = os.path.join(os.path.dirname(__file__), "gdrive_loader.py")
        apk_path    = None
        env         = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        DOWNLOAD_PROCESS_OBJ = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script_path, request.url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        async for line in DOWNLOAD_PROCESS_OBJ.stdout:
            decoded_line = line.decode("utf-8", errors="replace").strip()
            if decoded_line.startswith("PROGRESS:"):
                await manager.broadcast({"type": "LOG", "payload": {
                    "message": decoded_line.replace("PROGRESS:", ""), "status": "PROGRESS",
                }})
            elif decoded_line.startswith("RESULT:"):
                apk_path = decoded_line.replace("RESULT:", "").strip()
            elif decoded_line:
                await manager.broadcast({"type": "LOG", "payload": {"message": decoded_line, "status": "INFO"}})

        await DOWNLOAD_PROCESS_OBJ.wait()
        if DOWNLOAD_PROCESS_OBJ.returncode != 0:
            stderr_data = await DOWNLOAD_PROCESS_OBJ.stderr.read()
            raise Exception(f"Script Error: {stderr_data.decode('utf-8', errors='replace').strip() or 'Unknown error'}")
        if not apk_path:
            raise Exception("Download script finished but returned no path.")

        DOWNLOAD_PROCESS_OBJ = None

        icon_url      = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

        info         = get_apk_info(apk_path) or {}
        print(f"[APK Info] {info}")
        package_name = info.get("package_name", "")
        app_name     = info.get("app_name", "")

        # ── FIX: use central helper ───────────────────────────────────────────
        app_variant  = _detect_app_variant(package_name, app_name)
        tests_to_run = request.tests_to_run or APP_VARIANTS.get(app_variant, [])

        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"Detected app variant: {app_variant}", "status": "INFO"},
        })

        background_tasks.add_task(
            _run_post_notify,
            run_id=run_id,
            apk_path=apk_path,
            tests_to_run=tests_to_run,
            app_name=app_name or "",
            app_version=info.get("app_version") or "",
            developer_name=APP_DEVELOPER_MAP.get(app_variant, "Unknown Developer"),
            channel_id=SLACK_NOTIFY_CHANNEL,
        )

        return {
            "status":       "success",
            "message":      "APK Downloaded. Test Starting...",
            "run_id":       run_id,
            "app_icon":     full_icon_url,
            "apk_path":     apk_path,
            **info,
            "app_name":     app_name,
            "package_name": package_name,
            "app_variant":  app_variant,
        }

    except Exception as e:
        DOWNLOAD_PROCESS_OBJ = None
        await manager.broadcast({"type": "LOG", "payload": {
            "message": f"Download interrupted: {str(e)}", "status": "FAILED",
        }})
        raise HTTPException(status_code=400, detail=f"Download Failed: {str(e)}")


@app.post("/start-test-existing")
async def start_test_existing(request: ExistingTestRequest, background_tasks: BackgroundTasks):
    global _latest_run_id

    run_id        = _new_run()
    _latest_run_id = run_id

    try:
        apk_path = os.path.join(APKS_DIR, request.apk_name)
        if not os.path.isfile(apk_path):
            raise HTTPException(status_code=404, detail="APK not found on server")

        await manager.broadcast({"type": "RUN_START", "payload": {"run_id": run_id}})
        await manager.broadcast({"type": "LOG", "payload": {
            "message": f"Using existing APK: {request.apk_name} (run_id: {run_id[:8]})", "status": "INFO",
        }})

        icon_url      = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None
        info          = get_apk_info(apk_path) or {}

        package_name = info.get("package_name", "")
        app_name     = info.get("app_name", "")

        # ── FIX: use central helper ───────────────────────────────────────────
        app_variant   = _detect_app_variant(package_name, app_name)
        variant_tests = APP_VARIANTS.get(app_variant, [])

        tests_to_run = request.tests_to_run

        if tests_to_run:
            valid   = [t for t in tests_to_run if os.path.isfile(os.path.join(BASE_DIR, t["path"]))]
            invalid = [t for t in tests_to_run if t not in valid]

            if invalid:
                bad_paths = [t["path"] for t in invalid]
                await manager.broadcast({"type": "LOG", "payload": {
                    "message": (
                        f"⚠️  {len(invalid)} invalid path(s) removed: {bad_paths}. "
                        f"Falling back to APP_VARIANTS defaults for variant '{app_variant}'."
                    ),
                    "status": "WARN",
                }})
            tests_to_run = valid if valid else variant_tests
        else:
            tests_to_run = variant_tests

        if not tests_to_run:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No valid test scripts found for variant '{app_variant}'. "
                    f"Check APP_VARIANTS paths in server.py."
                ),
            )

        await manager.broadcast({"type": "LOG", "payload": {
            "message": f"Running {len(tests_to_run)} test(s): {[t['name'] for t in tests_to_run]}",
            "status": "INFO",
        }})

        background_tasks.add_task(
            _run_post_notify,
            run_id=run_id,
            apk_path=apk_path,
            tests_to_run=tests_to_run,
            app_name=app_name or "",
            app_version=info.get("app_version") or "",
            developer_name=APP_DEVELOPER_MAP.get(app_variant, "Unknown Developer"),
            channel_id=SLACK_NOTIFY_CHANNEL,
        )

        return {
            "status":       "success",
            "message":      "Using existing APK. Test Starting...",
            "run_id":       run_id,
            "app_icon":     full_icon_url,
            "apk_path":     apk_path,
            "app_variant":  app_variant,
            "tests_to_run": tests_to_run,
            **info,
        }

    except HTTPException:
        raise
    except Exception as e:
        await manager.broadcast({"type": "LOG", "payload": {
            "message": f"Failed to start test: {str(e)}", "status": "FAILED",
        }})
        raise HTTPException(status_code=400, detail=f"Failed: {str(e)}")


@app.get("/api/apk-list")
async def list_apks():
    try:
        files = [name for name in os.listdir(APKS_DIR) if name.lower().endswith((".apk", ".apks"))]
        return {"apks": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-test")
async def stop_test():
    print("DEBUG: /stop-test called")
    stopped_something = False
    global DOWNLOAD_PROCESS_OBJ

    if DOWNLOAD_PROCESS_OBJ is not None:
        try:
            DOWNLOAD_PROCESS_OBJ.terminate()
            stopped_something = True
        except Exception as e:
            print(f"Error stopping download: {e}")

    if stop_current_tests():
        stopped_something = True

    if stopped_something:
        await manager.broadcast({"type": "LOG", "payload": {
            "message": "Backend: Process stopped on user request.", "status": "FAILED",
        }})
        return {"status": "stopped"}
    return {"status": "no-process"}


@app.get("/api/appium/status")
async def appium_status():
    global _appium_proc
    if _appium_proc is not None and _appium_proc.poll() is None:
        return {"status": "running", "port": APPIUM_PORT}
    return {"status": "stopped"}


@app.post("/api/appium/start")
async def appium_start():
    global _appium_proc
    if _appium_proc is not None and _appium_proc.poll() is None:
        return {"status": "running", "message": "Appium is already running via backend."}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", APPIUM_PORT)) == 0:
            return {"status": "running", "message": f"Appium already active on port {APPIUM_PORT}"}
    try:
        _appium_proc = subprocess.Popen(
            ["appium", "-p", str(APPIUM_PORT)],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"status": "started", "message": f"Appium started on port {APPIUM_PORT}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/appium/stop")
async def appium_stop():
    global _appium_proc
    if _appium_proc is not None:
        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            except Exception:
                _appium_proc.kill()
        _appium_proc = None
        return {"status": "stopped"}
    return {"status": "not_running"}


@app.post("/api/generate-report")
async def api_generate_report():
    try:
        threading.Thread(target=generate_report).start()
        return {"status": "ok", "message": "Report generation started"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/run/{run_id}")
async def get_run_state(run_id: str):
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail=f"run_id '{run_id}' not found")
    run = _runs[run_id]
    return {
        "run_id":           run_id,
        "started_at":       run["started_at"],
        "report_url":       run["report_url"],
        "current_test":     run["current_test_name"],
        "step_store_keys":  list(run["test_steps_store"].keys()),
        "pending_payloads": len(run["pending_payloads"]),
    }


# ════════════════════════════════════════════════════════════════════════════
#  SLACK EVENTS
# ════════════════════════════════════════════════════════════════════════════

@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}

    event_id = body.get("event_id")
    if event_id in PROCESSED_EVENTS:
        print("[Slack] Duplicate event ignored")
        return {"status": "duplicate"}
    PROCESSED_EVENTS.add(event_id)

    event = body.get("event", {})
    print("[Slack] Event received:", event)

    if event.get("subtype") is not None:
        return {"status": "ignored"}

    if event.get("type") == "message":
        text = event.get("text", "")
        if "drive.google.com" in text:
            file_id = extract_drive_file_id(text)
            if file_id:
                channel_id     = event.get("channel")
                sender_user_id = event.get("user")
                background_tasks.add_task(
                    _handle_slack_apk,
                    file_id=file_id,
                    channel_id=channel_id,
                    sender_user_id=sender_user_id,
                )

    return {"status": "ok"}


# ════════════════════════════════════════════════════════════════════════════
#  JIRA ENHANCE
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/jira/enhance")
async def enhance_jira_issue(req: JiraEnhanceRequest):
    from generate_jira_desc import generate_jira_description, generate_jira_title

    issue_data = req.model_dump(exclude_none=True)

    try:
        loop = asyncio.get_event_loop()
        enhanced_description, enhanced_title = await asyncio.gather(
            loop.run_in_executor(None, generate_jira_description, issue_data),
            loop.run_in_executor(None, generate_jira_title, issue_data),
        )
    except Exception as exc:
        logger.error("[/api/jira/enhance] Gemini call failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"LLM enhancement failed: {str(exc)}")

    logger.info("[/api/jira/enhance] Enhanced issue_id=%s title='%s'", req.issue_id, enhanced_title)

    return {
        "status":      "enhanced",
        "issue_id":    req.issue_id,
        "title":       enhanced_title,
        "description": enhanced_description,
    }


# ════════════════════════════════════════════════════════════════════════════
#  ENTRYPOINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)