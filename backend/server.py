import os
import sys
import json
import datetime

sys.dont_write_bytecode = True
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.responses import Response
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
import csv
import glob
import logging
from gdrive_loader import download_apk, extract_app_icon, get_apk_info
from typing import List, Optional, Dict, Any

logger = logging.getLogger("uvicorn.error")
from starlette.websockets import WebSocketDisconnect
from jira_integration.mongo_config import mongo_config
from jira_integration.mongo_config import (
    connect_mongodb,
    disconnect_mongodb,
    is_mongodb_enabled,
)
from jira_integration.mongo_jira_integration import (
    create_and_store_jira_issue,
    store_removed_ticket,
)

# ── In-memory fallback stores ─────────────────────────────────────────────────
_dismissed_history: list[dict] = []   # removed/dismissed tickets

# ─── Global dedup tracker ────────────────────────────────────────────────────
LAST_SLACK_EVENT_TS = None

# ─── Load env from backend directory ─────────────────────────────────────────
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)
print(f"[ENV] Loaded .env from: {_ENV_PATH}")

_jira_email = os.getenv("JIRA_EMAIL", "")
_jira_token = os.getenv("JIRA_API_TOKEN", "")
print(f"[ENV] JIRA_EMAIL     = {_jira_email or '(NOT SET)'}")
print(f"[ENV] JIRA_API_TOKEN = {'(set, length=' + str(len(_jira_token)) + ')' if _jira_token else '(NOT SET)'}")

SLACK_BOT_TOKEN    = os.getenv("SLACK_BOT_TOKEN")
NETLIFY_AUTH_TOKEN = os.getenv("NETLIFY_AUTH_TOKEN")
NETLIFY_SITE_ID    = os.getenv("NETLIFY_SITE_ID")

# ─── Project root ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tests.test_runner import (
    run_tests_and_get_suggestions,
    stop_current_tests,
    generate_report,
)

print("server is running...")

# ─── App variant config ───────────────────────────────────────────────────────
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

APP_DEVELOPER_MAP = {
    "regular_farmer": "@Anuj",
    "regular_client": "@Vaibhav Bhagwat",
    "state_farmer":   "@Swaroopa",
    "state_client":   "@Vikash Chandra",
}

# ─── Global process handles ───────────────────────────────────────────────────
_appium_proc: subprocess.Popen | None = None
_allure_proc: subprocess.Popen | None = None
_allure_port: int | None = None
APPIUM_PORT = 4723
ALLURE_CMD  = r"C:\Users\Pramo\scoop\shims\allure"
DOWNLOAD_PROCESS_OBJ = None


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


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
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
            params={"user": user_id}, timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            return data["user"]["real_name"]
    except Exception as e:
        print(f"[Slack] Could not fetch user name: {e}")
    return "Unknown Developer"


def deploy_to_netlify() -> str | None:
    allure_report_path = os.path.join(BASE_DIR, "allure-report")
    if not NETLIFY_AUTH_TOKEN or not NETLIFY_SITE_ID:
        print("[Netlify] Missing NETLIFY_AUTH_TOKEN or NETLIFY_SITE_ID in .env")
        return None
    if not os.path.isdir(allure_report_path):
        print(f"[Netlify] allure-report folder not found: {allure_report_path}")
        return None

    netlify_cmd = r"C:\Users\ABDUL SAMAD\AppData\Roaming\npm\netlify.cmd"

    print("[Netlify] Deploying allure-report to Netlify...")
    try:
        result = subprocess.run(
            [
                netlify_cmd, "deploy",
                "--prod",
                "--dir",     allure_report_path,
                "--site",    NETLIFY_SITE_ID,
                "--auth",    NETLIFY_AUTH_TOKEN,
                "--message", "Automated test report",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            shell=True,
        )

        print(f"[Netlify] Return code: {result.returncode}")

        if result.returncode != 0:
            print(f"[Netlify] Deploy failed. stderr: {result.stderr}")
            return None
        url = "https://krishivaas-test-reports.netlify.app"
        print(f"[Netlify] ✅ Deployed at: {url}")
        return url
    except Exception as e:
        print(f"[Netlify] Exception: {e}")
        return None


def send_slack_message(
    channel_id:     str,
    developer_name: str,
    app_name:       str,
    apk_version:    str,
    passed:         int,
    failed:         int,
    report_url:     str,
) -> None:
    """Send Allure report link to Slack as a message."""
    if not SLACK_BOT_TOKEN:
        print("[Slack] No bot token — cannot send report.")
        return
    summary = (
        f"✅ *Automation Report Ready!*\n"
        f"👤 *Developer:* {developer_name}\n"
        f"📱 *App:* {app_name}\n"
        f"🔖 *Version No:* {apk_version}\n"
        f"🟢 Passed: {passed}  |  🔴 Failed: {failed}\n"
        f"📊 *View Full Report:* {report_url}"
    )

    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}

    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={**headers, "Content-Type": "application/json"},
            json={
                "channel": channel_id,
                "text":    summary,
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("ok"):
            print("[Slack] ✅ Report link sent to Slack successfully!")
        else:
            print(f"[Slack] ❌ Failed to send message: {data.get('error')}")
    except Exception as e:
        print(f"[Slack] Exception sending message: {e}")


def extract_drive_file_id(text: str) -> str | None:
    text = text.replace("<", "").replace(">", "")
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", text)
    return match.group(1) if match else None


# ════════════════════════════════════════════════════════════════════════════
#  BACKGROUND TASKS
# ════════════════════════════════════════════════════════════════════════════

async def _run_tests_and_notify_slack(
    apk_path:       str,
    tests_to_run:   list,
    channel_id:     str,
    developer_name: str,
    app_name:       str,
    apk_version:    str,
) -> None:
    """Run tests → Allure report → deploy to Netlify → send link to Slack."""
    loop = asyncio.get_event_loop()

    print("[Slack Flow] Step 1: Running tests...")
    try:
        await loop.run_in_executor(
            None,
            lambda: run_tests_and_get_suggestions(apk_path, tests_to_run=tests_to_run),
        )
        print("[Slack Flow] Step 1 done.")
    except Exception as e:
        print(f"[Slack Flow] Step 1 FAILED: {e}")
        return

    print("[Slack Flow] Step 2: Generating Allure report...")
    try:
        await loop.run_in_executor(None, generate_report)
        print("[Slack Flow] Step 2 done.")
    except Exception as e:
        print(f"[Slack Flow] Report FAILED: {e}"); return

    passed = failed = 0
    try:
        for json_file in glob.glob(os.path.join(BASE_DIR, "allure-results", "*-result.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("status", "").upper() == "PASSED":
                passed += 1
            else:
                failed += 1
        print(f"[Slack Flow] Step 3 done. Passed: {passed} | Failed: {failed}")
    except Exception as e:
        print(f"[Slack Flow] Count FAILED: {e}")

    print("[Slack Flow] Step 4: Deploying to Netlify...")
    report_url = None
    try:
        report_url = await loop.run_in_executor(None, deploy_to_netlify)
        if report_url:
            print(f"[Slack Flow] Step 4 done. URL: {report_url}")
        else:
            print("[Slack Flow] Step 4: Netlify deploy failed — will send fallback message.")
            report_url = "Report deployment failed — check server logs"
    except Exception as e:
        print(f"[Slack Flow] Step 4 FAILED: {e}")
        report_url = "Report deployment failed"

    print("[Slack Flow] Step 5: Sending report link to Slack...")
    try:
        await loop.run_in_executor(
            None,
            lambda: send_slack_message(
                channel_id=channel_id,
                developer_name=developer_name,
                app_name=app_name or "Unknown App",
                apk_version=apk_version or "Unknown",
                passed=passed,
                failed=failed,
                report_url=report_url,
            ),
        )
        print("[Slack Flow] Step 5 done.")
    except Exception as e:
        print(f"[Slack Flow] Step 5 FAILED: {e}")


async def _handle_slack_apk(
    file_id:        str,
    channel_id:     str,
    sender_user_id: str,
) -> None:
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print(f"[Slack] Download URL: {download_url}")

    try:
        loop     = asyncio.get_event_loop()
        apk_path = await loop.run_in_executor(None, lambda: download_apk(download_url))

        info = get_apk_info(apk_path) or {}
        print(f"[APK Info] {info}")

        package_name = info.get("package_name")
        app_name     = info.get("app_name") or info.get("application") or "Unknown App"
        apk_version  = (
            info.get("version_name")
            or info.get("versionName")
            or info.get("version_code")
            or info.get("versionCode")
            or info.get("apk_version")
            or "Unknown"
        )

        app_variant    = PACKAGE_VARIANT_MAP.get(package_name)
        tests_to_run   = APP_VARIANTS.get(app_variant, [])
        developer_name = APP_DEVELOPER_MAP.get(app_variant, get_slack_user_name(sender_user_id))

        print(f"[Slack] app_variant:    {app_variant}")
        print(f"[Slack] tests_to_run:   {tests_to_run}")
        print(f"[Slack] app_name:       {app_name}")
        print(f"[Slack] apk_version:    {apk_version}")
        print(f"[Slack] developer_name: {developer_name}")

        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": (
                    f"[Slack] {developer_name} triggered: "
                    f"{app_name} v{apk_version} | Variant: {app_variant}"
                ),
                "status": "INFO",
            },
        })

        await _ensure_appium_running()

        await _run_tests_and_notify_slack(
            apk_path=apk_path,
            tests_to_run=tests_to_run,
            channel_id=channel_id,
            developer_name=developer_name,
            app_name=app_name,
            apk_version=apk_version,
        )

    except Exception as e:
        print(f"[Slack] _handle_slack_apk error: {e}")
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"[Slack] Error: {str(e)}", "status": "FAILED"},
        })


# ════════════════════════════════════════════════════════════════════════════
#  APP LIFESPAN
# ════════════════════════════════════════════════════════════════════════════

_jira_history:      list[dict]           = []
_pending_payloads:  list[dict]           = []
_dismissed_keys:    set[str]             = set()
_test_steps_store:  Dict[str, List[str]] = {}
_current_test_name: str                  = "default"

_PAYLOAD_PREFIXES = ("AUTOMATION_PAYLOAD_JSON:", "JIRA_PAYLOAD_JSON:")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ────────────────────────────────────────────────────────────────────────
    # STARTUP
    # ────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("[STARTUP] Initializing application...")
    print("=" * 70)
    print("[STARTUP] Connecting to MongoDB...")
    if connect_mongodb():
        logger.info("✅ [STARTUP] MongoDB connected successfully")
        print("✅ [STARTUP] MongoDB connected successfully")
    else:
        logger.warning("⚠️  [STARTUP] MongoDB connection failed or disabled")
        print("⚠️  [STARTUP] MongoDB connection failed or disabled")
    print("[STARTUP] Server ready for requests\n")
    yield

    print("\n" + "=" * 70)
    print("[SHUTDOWN] Cleaning up...")
    disconnect_mongodb()
    global _appium_proc
    if _appium_proc is not None:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                _appium_proc.kill()
        except Exception:
            pass
    print("[SHUTDOWN] Cleanup complete\n")


# ════════════════════════════════════════════════════════════════════════════
#  FASTAPI APP
# ════════════════════════════════════════════════════════════════════════════

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
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

# ────────────────────────────────────────────────────────────────────────────
# Include MongoDB Routes (NEW)
# ────────────────────────────────────────────────────────────────────────────
from mongodb_routes import router as mongodb_router
app.include_router(mongodb_router)


class AnalyzeReq(BaseModel):
    run_id: str | None = None


def _latest_run_id() -> str:
    runs = [p for p in UI_SCREENSHOTS_BASE.iterdir() if p.is_dir()]
    if not runs:
        raise HTTPException(404, detail="No UI screenshots found.")
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].name


@app.post("/api/ui-screenshots/analyze")
def analyze_ui_screenshots(req: AnalyzeReq):
    print("UI parser api called")
    run_id  = req.run_id or _latest_run_id()
    run_dir = UI_SCREENSHOTS_BASE / run_id
    if not run_dir.exists():
        raise HTTPException(404, detail=f"Run screenshots folder not found: {run_id}")
    validator = Path(__file__).resolve().parents[1] / "ui-parser" / "ui_screenshot_validator.py"
    if not validator.exists():
        raise HTTPException(500, detail=f"Validator script not found: {validator}")
    proc = subprocess.run([sys.executable, str(validator), "--root-dir", str(run_dir)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise HTTPException(500, detail=f"UI validator failed: {proc.stderr.strip() or proc.stdout.strip()}")
    payload = json.loads(proc.stdout or "{}")
    results = payload.get("results", [])
    for r in results:
        rel = r.get("relative_path")
        r["screenshot_url"] = f"/ui-screenshots/{run_id}/{rel}" if rel else None
    return {"run_id": run_id, "results": results}


ALLURE_RESULTS_DIR = os.path.join(BASE_DIR, "allure-results")
os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
app.mount("/allure-results", StaticFiles(directory=ALLURE_RESULTS_DIR), name="allure-results")
app.mount("/ui-screenshots", StaticFiles(directory=str(UI_SCREENSHOTS_BASE)), name="ui-screenshots")


# ─── Models ───────────────────────────────────────────────────────────────────
class RunCompleteEvent(BaseModel):
    report_url: str

class ExistingTestRequest(BaseModel):
    apk_name: str
    tests_to_run: Optional[List[Dict[str, str]]] = None

class LogMessage(BaseModel):
    message: str
    status: str = "INFO"

class TestRequest(BaseModel):
    url: str
    tests_to_run: Optional[List[Dict[str, str]]] = None

class JiraPayloadRequest(BaseModel):
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
    app_name:        Optional[str]       = None
    app_version:     Optional[str]       = None
    module:          Optional[str]       = None
    feature:         Optional[str]       = None
    issue_summary:   Optional[str]       = None
    test_name:       Optional[str]       = None
    test_id:         Optional[str]       = None
    steps_executed:  Optional[List[Any]] = None
    developer_name:  Optional[str]       = None
    priority:        Optional[str]       = None
    title:           Optional[str]       = None
    description:     Optional[str]       = None
    parent:          Optional[str]       = None
    fix_version:     Optional[List[str]] = None
    affects_version: Optional[List[str]] = None
    issue_id:        Optional[str]       = None
    issue_url:       Optional[str]       = None
    ticket_id:       Optional[str]       = None
    start_date:      Optional[str]       = None
    end_date:        Optional[str]       = None
    sprint:          Optional[str]       = None


# ─── WebSocket Connection Manager ─────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
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
        async def _safe_send(ws):
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

def _broadcast_async(message: dict) -> None:
    try:
        asyncio.create_task(manager.broadcast(message))
    except RuntimeError:
        pass


# ════════════════════════════════════════════════════════════════════════════
#  DESCRIPTION / STEPS HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _is_unknown(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        s = value.strip()
        return not s or s.lower().startswith("unknown")
    return False


def _calculate_duration(start_date: Optional[str], end_date: Optional[str]) -> str:
    if not start_date or not end_date:
        return "Unknown"
    try:
        start    = datetime.datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end      = datetime.datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        duration = (end - start).total_seconds()
        minutes  = int(duration / 60)
        seconds  = int(duration % 60)
        return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
    except Exception as e:
        print(f"[WARN] Could not calculate duration: {e}")
        return "Unknown"


def _extract_steps_from_numbered_list(text: str) -> List[str]:
    """
    Parse lines matching '1. Step text' from any block of text.
    Used as a fallback when steps_executed list is empty but the
    conftest already embedded them in the description string.
    Returns a de-duplicated list preserving order.
    """
    seen:  set   = set()
    steps: list  = []
    for line in text.splitlines():
        m = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if m:
            step = m.group(1).strip()
            if step and step not in seen:
                seen.add(step)
                steps.append(step)
    return steps


def _strip_embedded_steps_from_description(text: str) -> str:
    """
    Remove any 'Steps Executed:' block AND any '==...== STEPS EXECUTED ==...=='
    block that the conftest or a previous formatting pass wrote into the
    description string, so we never render steps twice.

    Also removes the formatted METADATA block so format_description_with_steps
    can rebuild it cleanly.
    """
    if not text:
        return text
    lines  = text.splitlines()
    result = []
    skip   = False
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # ── Detect start of an embedded "Steps Executed:" prose block ──
        if re.match(r'^steps\s+executed\s*:?\s*$', stripped, re.IGNORECASE):
            skip = True
            i += 1
            continue

        # ── Detect start of a separator-bordered section header ──
        # Matches lines that are all '=' characters (our separator)
        if re.match(r'^={10,}$', stripped):
            # Peek at next non-blank line to see if it's a known header
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                header = lines[j].strip().upper()
                if header in ("STEPS EXECUTED", "METADATA"):
                    skip = header == "STEPS EXECUTED"
                    if header == "METADATA":
                        i = j + 1
                        while i < len(lines) and not re.match(r"^={10,}$", lines[i].strip()):
                            i += 1
                        i += 1
                        skip = False
                        continue
                    else:
                        i = j + 1
                        while i < len(lines) and not re.match(r"^={10,}$", lines[i].strip()):
                            i += 1
                        i += 1
                        skip = False
                        continue
        if skip:
            if re.match(r"^\d+\.", stripped):
                i += 1
                continue
            else:
                skip = False
        result.append(lines[i])
        i += 1
    return "\n".join(result).rstrip()


def format_description_with_steps(
    description: str,
    app_name: Optional[str] = None,
    app_version: Optional[str] = None,
    module: Optional[str] = None,
    test_name: Optional[str] = None,
    developer_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sprint: Optional[str] = None,
    steps_executed: Optional[List[str]] = None,
) -> str:
    """
    Build a clean plain-text description:
      <error / base text>
      ==================================================
      METADATA
      ==================================================
      App / Version / Module / Test / Developer / Start / End / Duration / Sprint
      ==================================================
      STEPS EXECUTED
      ==================================================
      1. step …

    Strips any previously embedded steps / metadata blocks first so this
    function is safe to call repeatedly without causing duplication.
    """
    # 1. Remove any previously embedded steps/metadata from the raw description
    base = _strip_embedded_steps_from_description(
        description.strip() if description else "Test automation failure detected."
    ).strip() or "Test automation failure detected."

    lines = [base, "", "=" * 50, "METADATA", "=" * 50]
    if app_name       and not _is_unknown(app_name):       lines.append(f"App: {app_name}")
    if app_version    and not _is_unknown(app_version):    lines.append(f"Version: {app_version}")
    if module         and not _is_unknown(module):         lines.append(f"Module: {module}")
    if test_name      and not _is_unknown(test_name):      lines.append(f"Test: {test_name}")
    if developer_name and not _is_unknown(developer_name): lines.append(f"Developer: {developer_name}")
    if start_date:  lines.append(f"Start: {start_date}")
    if end_date:    lines.append(f"End: {end_date}")
    if start_date and end_date:
        lines.append(f"Duration: {_calculate_duration(start_date, end_date)}")
    if sprint:      lines.append(f"Sprint: {sprint}")
    if steps_executed:
        lines += ["", "=" * 50, "STEPS EXECUTED", "=" * 50]
        for i, step in enumerate(steps_executed, 1):
            lines.append(f"{i}. {step}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/run-complete")
async def run_complete(event: RunCompleteEvent):
    await manager.broadcast({"type": "RUN_COMPLETE", "payload": {"report_url": event.report_url}})
    return {"ok": True}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/api/jira/test-connection")
async def jira_test_connection():
    import requests as req_lib
    from jira_integration.jira_config import config as jira_config
    from requests.auth import HTTPBasicAuth
    base = {
        "jira_url": jira_config.url or "(not set)",
        "jira_email": jira_config.email or "(not set)",
        "jira_project_key": jira_config.project_key or "(not set)",
        "jira_token_set": bool(jira_config.api_token),
        "jira_enabled": jira_config.enabled,
    }
    if not all([jira_config.url, jira_config.email, jira_config.api_token]):
        return {**base, "status": "MISSING_CONFIG", "message": "One or more required .env variables not set"}
    try:
        me = req_lib.get(f"{jira_config.url}/rest/api/3/myself",
                         auth=HTTPBasicAuth(jira_config.email, jira_config.api_token),
                         headers={"Accept": "application/json"}, timeout=10)
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
        proj = req_lib.get(f"{jira_config.url}/rest/api/3/project/{jira_config.project_key}",
                           auth=HTTPBasicAuth(jira_config.email, jira_config.api_token),
                           headers={"Accept": "application/json"}, timeout=10)
        if proj.status_code == 404:
            return {**base, "status": "PROJECT_NOT_FOUND", "message": f"Project '{jira_config.project_key}' not found"}
        if proj.status_code == 403:
            return {**base, "status": "PROJECT_NO_PERMISSION", "message": f"No access to project '{jira_config.project_key}'"}
        if proj.status_code == 200:
            base["project_name"] = proj.json().get("name")
    except Exception as e:
        base["project_check"] = str(e)
    return {**base, "status": "ALL_OK",
            "message": f"Credentials OK. Connected as '{base.get('jira_account')}'. Project '{jira_config.project_key}' accessible."}


@app.post("/api/allure/start")
async def allure_start():
    port = _pick_free_port()
    subprocess.Popen([ALLURE_CMD, "open", "-h", "127.0.0.1", "-p", str(port), ALLURE_REPORT_DIR],
                     cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    return JSONResponse({"url": f"http://127.0.0.1:{port}"})


@app.get("/device-status")
async def device_status():
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        lines  = result.stdout.strip().splitlines()[1:]
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


# ─── Step resolution ──────────────────────────────────────────────────────────
def _resolve_steps_for_test(test_name: str) -> List[str]:
    if test_name and test_name in _test_steps_store:
        steps = _test_steps_store.pop(test_name)
        print(f"✅ Steps resolved (exact) → {test_name}: {steps}")
        return steps
    if "default" in _test_steps_store:
        steps = _test_steps_store.pop("default")
        print(f"✅ Steps resolved (default fallback) → {test_name}: {steps}")
        return steps
    print(f"⚠️  No steps in store for {test_name}")
    return []


# ════════════════════════════════════════════════════════════════════════════
#  FIX 1 — POST /api/log-step
#  Capture [FOUND], [CLICK], [TAP], [STEP], [ACTION] markers so that tests
#  which don't emit [FOUND] still get their steps recorded.
# ════════════════════════════════════════════════════════════════════════════

# Pre-compiled step-capture patterns (checked in order; first match wins)
_STEP_CAPTURE_PATTERNS: List[re.Pattern] = [
    re.compile(r'\[FOUND\]\s+name=[\'"]([^\'"]+)[\'"]', re.IGNORECASE),
    re.compile(r"\[(?:CLICK|TAP|PRESSED|TAPPED)\]\s+(.+)", re.IGNORECASE),
    re.compile(r"\[STEP\]\s+(.+)", re.IGNORECASE),
    re.compile(r"\[ACTION\]\s+(.+)", re.IGNORECASE),
    re.compile(r"✅\s+(?:Step\s+)?[–—-]?\s*(.+)", re.IGNORECASE),
]


def _parse_step_from_message(message: str) -> Optional[str]:
    for pattern in _STEP_CAPTURE_PATTERNS:
        m = pattern.search(message)
        if m:
            step = m.group(1).strip()
            if step:
                return step
    return None


@app.post("/api/log-step")
async def log_step(msg: LogMessage):
    global _test_steps_store, _current_test_name
    message = msg.message

    # ── Test context switch ──────────────────────────────────────────────
    if "[TEST_START:" in message:
        try:
            new_test = message.split("[TEST_START:")[1].split("]")[0].strip()
            if new_test and new_test != _current_test_name:
                _current_test_name = new_test
                _test_steps_store.setdefault(_current_test_name, [])
                print(f"🔄 Test context switched → {_current_test_name}")
        except Exception as e:
            print(f"❌ TEST_START parse warning: {e}")

    # ── Step capture (all patterns) ──────────────────────────────────────
    try:
        bucket = (
            message.split("[TEST:")[1].split("]")[0].strip()
            if "[TEST:" in message else _current_test_name
        )
        step = _parse_step_from_message(message)
        if step:
            _test_steps_store.setdefault(bucket, [])
            if step not in _test_steps_store[bucket]:
                _test_steps_store[bucket].append(step)
                print(f"✅ Step captured → {bucket}: {step}")
    except Exception as e:
        print(f"❌ Step capture warning: {e}")

    # ── Payload prefix handling ──────────────────────────────────────────
    for prefix in _PAYLOAD_PREFIXES:
        if message.startswith(prefix):
            raw = message[len(prefix):].strip()
            try:
                payload = json.loads(raw)
                steps   = payload.get("steps_executed") or []
                clean_line = (
                    f"[PAYLOAD] {payload.get('issue_id','')} | "
                    f"{payload.get('module','?')} | {payload.get('test_name','?')} | "
                    f"Steps ({len(steps)}): {', '.join(steps[:3]) if steps else 'none'}"
                )
                _broadcast_async({"type": "LOG", "payload": {"message": clean_line, "status": "PAYLOAD"}})
            except Exception as exc:
                logger.warning("Failed to parse payload: %s", exc)
            return {"status": "ok"}

    _broadcast_async({"type": "LOG", "payload": {"message": message, "status": msg.status}})
    return {"status": "ok"}


# ─── GET /api/jira/steps/{test_name} — NON-DESTRUCTIVE read ──────────────────
# conftest polls this to collect steps before building the payload.
# Falls back to "default" so conftest sees steps even without [TEST_START:].
# Does NOT pop — only receive_jira_payload pops via _resolve_steps_for_test.
@app.get("/api/jira/steps/{test_name}")
async def get_steps(test_name: str):
    steps = _test_steps_store.get(test_name) or _test_steps_store.get("default") or []
    print(f"📤 Fetch steps → {test_name}: {steps}")
    return {"steps": steps, "test_name": test_name}


@app.post("/api/jira/steps")
async def add_step(data: dict):
    test_name = data.get("test_name", "unknown")
    step      = data.get("step", "")
    _test_steps_store.setdefault(test_name, [])
    if step and step not in _test_steps_store[test_name]:
        _test_steps_store[test_name].append(step)
        print(f"✅ Step added → {test_name}: {step}")
    return {"status": "ok", "test_name": test_name, "step_count": len(_test_steps_store[test_name])}


@app.post("/api/reset-steps")
async def reset_steps():
    global _test_steps_store, _current_test_name
    _test_steps_store  = {}
    _current_test_name = "default"
    print("🧹 Step store cleared")
    return {"status": "cleared"}


@app.post("/api/module-status")
async def module_status(data: dict):
    module = data.get("module")
    status = data.get("status")
    if module == "__RUN_START__":
        _broadcast_async({"type": "RUN_START", "payload": {}})
    else:
        _broadcast_async({"type": "MODULE", "payload": {"module": module, "status": status, "message": data.get("message", "")}})
    return {"status": "ok"}


# ════════════════════════════════════════════════════════════════════════════
#  FIX 2 — POST /api/jira/payload
#  Also recover steps embedded by conftest as a "Steps Executed:\n1. …" prose
#  block (written by _build_description when _get_steps returns non-empty).
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/jira/payload")
async def receive_jira_payload(req: JiraPayloadRequest):
    payload = req.model_dump(exclude_none=False)

    # ── Step 1: Clean the raw description ────────────────────────────────────
    # The conftest may embed a "Steps Executed:" block directly in the
    # description string. Strip it out NOW so it never appears twice.
    raw_description = payload.get("description") or ""
    steps_from_desc = _extract_steps_from_numbered_list(raw_description)
    clean_description = _strip_embedded_steps_from_description(raw_description).strip()
    payload["description"] = clean_description or "Test automation failure detected."

    incoming_steps = [s for s in (payload.get("steps_executed") or []) if s]
    if not incoming_steps:
        test_name = req.test_name or "default"
        resolved  = _resolve_steps_for_test(test_name)
        if not resolved and steps_from_desc:
            resolved = steps_from_desc
        payload["steps_executed"] = resolved
        logger.info("[/api/jira/payload] Injected %d steps for test=%s", len(resolved), test_name)
    else:
        _resolve_steps_for_test(req.test_name or "default")
        payload["steps_executed"] = incoming_steps
        logger.info("[/api/jira/payload] Payload already has %d steps for test=%s", len(incoming_steps), req.test_name)

    payload["description"] = format_description_with_steps(
        description=payload["description"],
        app_name=payload.get("app_name"),
        app_version=payload.get("app_version"),
        module=payload.get("module"),
        test_name=payload.get("test_name"),
        developer_name=payload.get("developer_name"),
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date"),
        sprint=payload.get("sprint"),
        steps_executed=payload.get("steps_executed"),
    )

    _pending_payloads.append(payload)
    await manager.broadcast({"type": "JIRA_PAYLOAD", "payload": payload})
    logger.info("[/api/jira/payload] %s module=%s test=%s steps=%d",
                req.issue_id, req.module, req.test_name, len(payload.get("steps_executed") or []))
    return {"status": "received", "issue_id": req.issue_id, "module": req.module}


@app.get("/api/jira/payloads")
async def get_pending_payloads():
    active = [p for p in _pending_payloads if _make_dismiss_key(p) not in _dismissed_keys]
    return {"payloads": active}


def _make_dismiss_key(payload: dict) -> str:
    tn    = str(payload.get("test_name") or "").strip()
    md    = str(payload.get("module")    or "").strip()
    if tn:
        return f"tn::{md}::{tn}"
    title = str(payload.get("issue_summary") or payload.get("title") or "").strip()
    return f"sum::{md}::{title}"


@app.post("/api/jira/dismiss")
async def dismiss_payload(data: dict):
    key = _make_dismiss_key(data)
    if key:
        _dismissed_keys.add(key)

    import uuid as _uuid
    dismissed_issue_id = (
        data.get("issue_id")
        or data.get("internal_issue_id")
        or ("DISMISSED-" + str(_uuid.uuid4())[:8].upper())
    )
    summary = data.get("issue_summary") or data.get("title") or "Dismissed Payload"
    module  = data.get("module")  or "Unknown"
    feature = data.get("feature") or "Unknown"

    # ── In-memory fallback entry ─────────────────────────────────────────
    dismissed_entry = {
        "issue_id":        dismissed_issue_id,
        "issue_url":       "",
        "title":           summary,
        "description":     data.get("description") or "",
        "developer_name":  data.get("developer_name") or "",
        "module":          module,
        "app_name":        data.get("app_name") or "",
        "app_version":     data.get("app_version") or "",
        "test_name":       data.get("test_name") or "",
        "ticket_id":       "",
        "priority":        data.get("priority") or "High",
        "status":          "Unassigned",
        "ticket_type":     "removed",
        "type":            "removed",
        "sprint":          data.get("sprint") or "",
        "start_date":      data.get("start_date") or "",
        "end_date":        data.get("end_date") or "",
        "steps_executed":  data.get("steps_executed") or [],
        "fix_version":     data.get("fix_version") or [],
        "affects_version": data.get("affects_version") or [],
        "created_at":      datetime.datetime.now().isoformat(),
    }
    _dismissed_history.append(dismissed_entry)

    # ── Persist to MongoDB ────────────────────────────────────────────────
    try:
        store_removed_ticket(
            issue_id=dismissed_issue_id,
            summary=summary,
            module=module,
            feature=feature,
            app_name=data.get("app_name"),
            app_version=data.get("app_version"),
            description=data.get("description"),
            test_name=data.get("test_name"),
            test_id=data.get("test_id"),
            steps_executed=data.get("steps_executed"),
            developer_name=data.get("developer_name"),
            priority=data.get("priority"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            sprint=data.get("sprint"),
            fix_version=data.get("fix_version"),
            affects_version=data.get("affects_version"),
        )
        logger.info("[/api/jira/dismiss] Removed ticket stored: %s", dismissed_issue_id)
    except Exception as exc:
        logger.warning("[/api/jira/dismiss] Could not save removed ticket to MongoDB: %s", exc)

    return {"status": "dismissed", "key": key}


@app.post("/api/jira/create")
async def jira_create(req: JiraCreateRequest):
    from jira_integration.jira_config import config as jira_config

    if not jira_config.enabled:
        raise HTTPException(status_code=400, detail="Jira is disabled. Set JIRA_ENABLED=true in backend/.env")

    missing = [n for n, v in {
        "JIRA_URL": jira_config.url, "JIRA_EMAIL": jira_config.email,
        "JIRA_API_TOKEN": jira_config.api_token, "JIRA_PROJECT_KEY": jira_config.project_key,
    }.items() if not v]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing .env variables: {', '.join(missing)}.")

    summary = (req.title or req.issue_summary or "Automation Failure").strip()

    steps_for_ticket: List[str] = [s for s in (req.steps_executed or []) if s]
    if not steps_for_ticket:
        steps_for_ticket = _resolve_steps_for_test(req.test_name or "default")
    if not steps_for_ticket and req.description:
        steps_for_ticket = _extract_steps_from_numbered_list(req.description)

    # ── FIX 3: Always rebuild description with steps so Jira ticket always
    #    shows the STEPS EXECUTED block regardless of frontend payload state.
    raw_desc = req.description or "Automation Test Failure"
    description = format_description_with_steps(
        description=_strip_embedded_steps_from_description(raw_desc),
        app_name=req.app_name, app_version=req.app_version,
        module=req.module or req.parent, test_name=req.test_name,
        developer_name=req.developer_name, start_date=req.start_date,
        end_date=req.end_date, sprint=req.sprint,
        steps_executed=steps_for_ticket,
    )

    logger.info("[/api/jira/create] Creating ticket test=%s steps=%d", req.test_name, len(steps_for_ticket))

    import io as _io, contextlib as _ctx
    _captured = _io.StringIO()
    try:
        with _ctx.redirect_stdout(_captured):
            result = create_and_store_jira_issue(
                summary=summary, description=description,
                app_name=req.app_name, app_version=req.app_version,
                module=req.module or req.parent, feature=req.feature,
                issue_summary=summary, test_name=req.test_name, test_id=req.test_id,
                steps_executed=steps_for_ticket, developer_name=req.developer_name,
                priority=req.priority, start_date=req.start_date, end_date=req.end_date,
                sprint=req.sprint, fix_version=req.fix_version,
                affects_version=req.affects_version,
            )
            if not result["success"]:
                raise Exception(result.get("error", "Unknown error"))
            issue_key = result["issue_id"]
            ticket_id = result["ticket_id"]
            issue_url = result["issue_url"]
    except Exception as exc:
        err = str(exc)
        logger.error("[/api/jira/create] Exception: %s", err)
        if "401" in err:
            raise HTTPException(status_code=400, detail=f"Jira 401 Unauthorized — wrong JIRA_EMAIL or JIRA_API_TOKEN.\nJira said: {err}")
        if "403" in err or "permission" in err.lower():
            raise HTTPException(status_code=400, detail=f"Jira 403 Forbidden — no permission to create issues.\nJira said: {err}")
        raise HTTPException(status_code=400, detail=f"Jira error: {err}")

    if not issue_key:
        raise HTTPException(status_code=400, detail="Jira returned no issue key — check all JIRA_* env vars in backend/.env")

    for _line in _captured.getvalue().splitlines():
        _line = _line.strip()
        if not _line:
            continue
        _broadcast_async({"type": "LOG", "payload": {"message": _line,
                          "status": "PAYLOAD" if any(_line.startswith(p) for p in _PAYLOAD_PREFIXES) else "INFO"}})

    entry = {
        "issue_id": issue_key, "issue_url": issue_url, "title": summary,
        "description": description, "developer_name": req.developer_name or "",
        "module": req.module or req.parent or "", "app_name": req.app_name or "",
        "app_version": req.app_version or "", "test_name": req.test_name or "",
        "ticket_id": ticket_id or req.ticket_id or "",
        "fix_version": req.fix_version or [], "affects_version": req.affects_version or [],
        "priority": req.priority or "High", "sprint": req.sprint or "Automation",
        "start_date": req.start_date or "", "end_date": req.end_date or "",
        "steps_executed": steps_for_ticket, "status": "Assigned",
        "ticket_type": "created", "type": "created",
        "created_at": datetime.datetime.now().isoformat(),
    }
    _jira_history.append(entry)
    _broadcast_async({"type": "JIRA_CREATED", "payload": entry})

    return {
        "issue_id": issue_key, "issue_key": issue_key,
        "issue_url": issue_url, "ticket_id": ticket_id,
        "mongodb_saved": ticket_id != "N/A", **entry,
    }


# ─── Jira history ─────────────────────────────────────────────────────────────
_jira_comments: dict = {}


@app.get("/api/jira/history")
async def jira_history_api(
    limit:    int = 500,
    skip:     int = 0,
    status:   Optional[str] = None,
    module:   Optional[str] = None,
    priority: Optional[str] = None,
):
    """
    Return Jira ticket history.

    Priority: MongoDB (persistent) → session memory (fallback).

    ✅ FIX: get_all_tickets() now re-raises exceptions. The try/except here
    catches those and falls through to session memory automatically, so the
    frontend never shows 0 when data actually exists in MongoDB.

    Each ticket carries `type` and `ticket_type`:
        "created"  → filed in Jira  → Assigned tab
        "removed"  → dismissed      → Unassigned tab
    """
    from jira_integration.mongo_operations import get_all_tickets
    from jira_integration.jira_config import config as jira_config

    def _normalise(t: dict) -> dict:
        """Map a MongoDB / memory document → frontend shape."""
        raw_type  = t.get("ticket_type") or t.get("type") or ""
        item_type = (
            raw_type if raw_type in ("created", "removed")
            else "removed" if t.get("status", "").lower() == "unassigned"
            else "created"
        )
        issue_id = t.get("issue_id", "")
        return {
            "issue_id":        issue_id,
            "issue_url":       t.get("issue_url") or (
                f"{jira_config.url}/browse/{issue_id}"
                if issue_id and item_type == "created" else ""
            ),
            "title":           t.get("summary", t.get("title", "")),
            "description":     t.get("description", ""),
            "developer_name":  t.get("developer_name", t.get("assignee", "")),
            "module":          t.get("module", ""),
            "app_name":        t.get("app_name", ""),
            "app_version":     t.get("app_version", ""),
            "test_name":       t.get("test_name", ""),
            "ticket_id":       t.get("ticket_id", ""),
            "priority":        t.get("priority", "High"),
            "status":          t.get("status", "Open"),
            "ticket_type":     item_type,
            "type":            item_type,               # ← what the frontend reads
            "sprint":          t.get("sprint", ""),
            "start_date":      t.get("start_date") or "",
            "end_date":        t.get("due_date") or t.get("end_date") or "",
            "steps_executed":  t.get("steps_executed", []),
            "fix_version":     t.get("fix_version", []),
            "affects_version": t.get("affects_version", []),
            "created_at":      t.get("created_at", ""),
        }

    # ── MongoDB path ──────────────────────────────────────────────────────
    if is_mongodb_enabled():
        try:
            filters = {}
            if status:   filters["status"]   = status
            if module:   filters["module"]   = module
            if priority: filters["priority"] = priority

            db_tickets = get_all_tickets(limit=limit, skip=skip, **filters)
            normalised = [_normalise(t) for t in db_tickets]

            logger.info(
                "[/api/jira/history] Returning %d tickets from MongoDB", len(normalised)
            )
            return {"issues": normalised, "source": "mongodb", "total": len(normalised)}

        except Exception as exc:
            # ✅ FIX: get_all_tickets now raises on connection failure.
            # We catch it here and fall through to session memory.
            logger.error(
                "[/api/jira/history] MongoDB query failed (%s), using session memory", exc
            )

    # ── Session-memory fallback ───────────────────────────────────────────
    logger.warning("[/api/jira/history] Returning session-memory history")

    # ✅ FIX: Apply _normalise() to session memory entries too, so field
    # names are mapped consistently (title, end_date, etc.)
    memory_issues: list[dict] = (
        [_normalise(e) for e in _jira_history] +
        [_normalise(e) for e in _dismissed_history]
    )

    logger.info(
        "[/api/jira/history] Returning %d tickets from session memory", len(memory_issues)
    )
    return {"issues": memory_issues, "source": "memory", "total": len(memory_issues)}


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
        {"key": e.get("issue_id",""), "summary": e.get("title",""),
         "status": e.get("status","Assigned"), "url": e.get("issue_url",""),
         "priority": e.get("priority",""), "assignee": e.get("developer_name",""),
         "updated": e.get("created_at","")}
        for e in _jira_history
    ]}


@app.get("/api/jira/tickets")
async def list_jira_tickets(
    limit:    int = 100,
    skip:     int = 0,
    status:   Optional[str] = None,
    module:   Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
):
    """
    Dedicated endpoint to list all tickets directly from MongoDB.
    Supports pagination and filtering.
    """
    from jira_integration.mongo_operations import get_all_tickets, get_statistics
    if not is_mongodb_enabled():
        raise HTTPException(status_code=503, detail="MongoDB is not connected.")
    filters = {}
    if status:   filters["status"]   = status
    if module:   filters["module"]   = module
    if priority: filters["priority"] = priority
    if assignee: filters["assignee"] = assignee
    tickets = get_all_tickets(limit=limit, skip=skip, **filters)
    stats   = get_statistics()
    return {"tickets": tickets, "total": stats.get("total", len(tickets)), "limit": limit, "skip": skip}


@app.get("/api/jira/tickets/{issue_id}")
async def get_jira_ticket(issue_id: str):
    from jira_integration.mongo_operations import get_ticket
    if not is_mongodb_enabled():
        raise HTTPException(status_code=503, detail="MongoDB is not connected.")
    ticket = get_ticket(issue_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {issue_id} not found in MongoDB.")
    return {"ticket": ticket}


@app.get("/api/jira/stats")
async def jira_stats():
    from jira_integration.mongo_operations import get_statistics
    if not is_mongodb_enabled():
        return {"error": "MongoDB not connected", "stats": {}}
    return {"stats": get_statistics()}


# @app.get("/api/health")
# async def health():
#     from jira_integration.jira_config import config as jira_config
#     return {
#         "status":            "ok",
#         "jira_enabled":      jira_config.enabled,
#         "jira_url":          jira_config.url or "(not set)",
#         "jira_project_key":  jira_config.project_key or "(not set)",
#         "jira_email":        jira_config.email or "(not set)",
#         "jira_token_set":    bool(jira_config.api_token),
#         "mongodb_enabled":   is_mongodb_enabled(),
#         "step_store_keys":   list(_test_steps_store.keys()),
#         "step_store_counts": {k: len(v) for k, v in _test_steps_store.items()},
#         "current_test":      _current_test_name,
#         "pending_payloads":  len(_pending_payloads),
#     }


def _reset_run_state():
    global _pending_payloads, _dismissed_keys, _test_steps_store, _current_test_name
    _test_steps_store  = {}
    _current_test_name = "default"
    _pending_payloads  = []
    _dismissed_keys    = set()


@app.post("/start-test")
async def start_test(request: TestRequest, background_tasks: BackgroundTasks):
    _reset_run_state()
    global DOWNLOAD_PROCESS_OBJ
    try:
        await manager.broadcast({"type": "LOG", "payload": {"message": "Starting APK download...", "status": "INFO"}})
        script_path = os.path.join(os.path.dirname(__file__), "gdrive_loader.py")
        apk_path    = None
        env         = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        DOWNLOAD_PROCESS_OBJ = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script_path, request.url,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env,
        )
        async for line in DOWNLOAD_PROCESS_OBJ.stdout:
            decoded_line = line.decode("utf-8").strip()
            if decoded_line.startswith("PROGRESS:"):
                await manager.broadcast({"type": "LOG", "payload": {"message": decoded_line.replace("PROGRESS:",""), "status": "PROGRESS"}})
            elif decoded_line.startswith("RESULT:"):
                apk_path = decoded_line.replace("RESULT:","").strip()
            elif decoded_line:
                await manager.broadcast({"type": "LOG", "payload": {"message": decoded_line, "status": "INFO"}})
        await DOWNLOAD_PROCESS_OBJ.wait()
        if DOWNLOAD_PROCESS_OBJ.returncode != 0:
            stderr_data = await DOWNLOAD_PROCESS_OBJ.stderr.read()
            raise Exception(f"Script Error: {stderr_data.decode('utf-8').strip() or 'Unknown error'}")
        if not apk_path:
            raise Exception("Download script finished but returned no path.")
        DOWNLOAD_PROCESS_OBJ = None
        icon_url      = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None
        info          = get_apk_info(apk_path) or {}
        app_name      = info.get("app_name")
        package_name  = info.get("package_name")
        app_variant   = PACKAGE_VARIANT_MAP.get(package_name)
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Detected app variant: {app_variant}", "status": "INFO"}})
        background_tasks.add_task(
            run_tests_and_get_suggestions, apk_path,
            tests_to_run=request.tests_to_run,
            app_name=info.get("app_name"), app_version=info.get("app_version"),
            developer_name=info.get("developer_name"),
        )
        return {
            "status": "success", "message": "APK Downloaded. Test Starting...",
            "app_icon": full_icon_url, "apk_path": apk_path, **info,
            "app_name": app_name, "package_name": package_name, "app_variant": app_variant,
        }
    except Exception as e:
        DOWNLOAD_PROCESS_OBJ = None
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Download interrupted: {str(e)}", "status": "FAILED"}})
        raise HTTPException(status_code=400, detail=f"Download Failed: {str(e)}")


@app.post("/start-test-existing")
async def start_test_existing(request: ExistingTestRequest, background_tasks: BackgroundTasks):
    _reset_run_state()
    try:
        apk_path = os.path.join(APKS_DIR, request.apk_name)
        if not os.path.isfile(apk_path):
            raise HTTPException(status_code=404, detail="APK not found on server")
        await manager.broadcast({"type": "RUN_START", "payload": {}})
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Using existing APK: {request.apk_name}", "status": "INFO"}})
        icon_url      = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None
        info          = get_apk_info(apk_path) or {}
        background_tasks.add_task(
            run_tests_and_get_suggestions, apk_path,
            tests_to_run=request.tests_to_run,
            app_name=info.get("app_name"), app_version=info.get("app_version"),
            developer_name=info.get("developer_name"),
        )
        return {"status": "success", "message": "Using existing APK. Test Starting...", "app_icon": full_icon_url, "apk_path": apk_path, **info}
    except HTTPException:
        raise
    except Exception as e:
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Failed to start test: {str(e)}", "status": "FAILED"}})
        raise HTTPException(status_code=400, detail=f"Failed: {str(e)}")


@app.get("/api/apk-list")
async def list_apks():
    try:
        files = [n for n in os.listdir(APKS_DIR) if n.lower().endswith((".apk", ".apks"))]
        return {"apks": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-test")
async def stop_test():
    global DOWNLOAD_PROCESS_OBJ
    stopped_something = False
    if DOWNLOAD_PROCESS_OBJ is not None:
        try:
            DOWNLOAD_PROCESS_OBJ.terminate()
        except Exception as e:
            print(f"Error stopping download: {e}")
    if stop_current_tests():
        stopped_something = True
    if stopped_something:
        await manager.broadcast({"type": "LOG", "payload": {"message": "Backend: Process stopped on user request.", "status": "FAILED"}})
        return {"status": "stopped"}
    return {"status": "no-process"}


@app.get("/api/appium/status")
async def appium_status():
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
        _appium_proc = subprocess.Popen(["appium", "-p", str(APPIUM_PORT)], shell=True,
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "started", "message": f"Appium started on port {APPIUM_PORT}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/appium/stop")
async def appium_stop():
    global _appium_proc
    if _appium_proc is not None:
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                _appium_proc.kill()
        _appium_proc = None
        return {"status": "stopped"}
    return {"status": "not_running"}


@app.post("/api/generate-report")
async def api_generate_report():
    try:
        import threading
        threading.Thread(target=generate_report).start()
        return {"status": "ok", "message": "Report generation started"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ════════════════════════════════════════════════════════════════════════════
#  SLACK EVENTS
# ════════════════════════════════════════════════════════════════════════════

@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    global LAST_SLACK_EVENT_TS
    body = await request.json()
    if body.get("type") == "url_verification":
        return {"challenge": body["challenge"]}
    event = body.get("event", {})
    if event.get("subtype") is not None:
        return {"status": "ignored"}
    event_ts = event.get("ts")
    if event_ts and event_ts == LAST_SLACK_EVENT_TS:
        return {"status": "duplicate"}
    LAST_SLACK_EVENT_TS = event_ts
    if event.get("type") == "message" and "drive.google.com" in event.get("text", ""):
        file_id = extract_drive_file_id(event.get("text", ""))
        if file_id:
            background_tasks.add_task(
                _handle_slack_apk, file_id=file_id,
                channel_id=event.get("channel"), sender_user_id=event.get("user"),
            )
    return {"status": "ok"}


class JiraEnhanceRequest(BaseModel):
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
    return {"status": "enhanced", "issue_id": req.issue_id, "title": enhanced_title, "description": enhanced_description}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)