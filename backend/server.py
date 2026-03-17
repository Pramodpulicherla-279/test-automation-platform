import os
import sys
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
import json
import socket
import asyncio
from fastapi import Request
import requests
import re
from dotenv import load_dotenv
import csv
import glob

from gdrive_loader import download_apk, extract_app_icon, get_apk_info
from typing import List, Optional, Dict
from starlette.websockets import WebSocketDisconnect

# ─── Global dedup tracker ───────────────────────────────────────────────────
LAST_SLACK_EVENT_TS = None

# ─── Load env ────────────────────────────────────────────────────────────────
load_dotenv()
SLACK_BOT_TOKEN    = os.getenv("SLACK_BOT_TOKEN")
NETLIFY_AUTH_TOKEN = os.getenv("NETLIFY_AUTH_TOKEN")
NETLIFY_SITE_ID    = os.getenv("NETLIFY_SITE_ID")

print("Slack Token Loaded:", SLACK_BOT_TOKEN)
print("Netlify Token Loaded:", NETLIFY_AUTH_TOKEN)
print("Netlify Site ID Loaded:", NETLIFY_SITE_ID)

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

APP_DEVELOPER_MAP = {
    "regular_farmer": "@Anuj",
    "regular_client": "@Vaibhav Bhagwat",
    "state_farmer":   "@Swaroopa",
    "state_client":   "@Vikash Chandra",
}

# ─── Global process handles ──────────────────────────────────────────────────
_appium_proc: subprocess.Popen | None = None
_allure_proc: subprocess.Popen | None = None
_allure_port: int | None = None
APPIUM_PORT          = 4723
ALLURE_CMD           = r"C:\Users\Pramo\scoop\shims\allure"
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
    """Fetch a Slack user's real name using their user ID."""
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


def deploy_to_netlify() -> str | None:
    """Deploy allure-report folder to Netlify and return the live URL."""
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

        # Always return fixed production URL — no regex needed
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
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', text)
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

    # Step 1 — run tests
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

    # Step 2 — generate Allure report
    print("[Slack Flow] Step 2: Generating Allure report...")
    try:
        await loop.run_in_executor(None, generate_report)
        print("[Slack Flow] Step 2 done.")
    except Exception as e:
        print(f"[Slack Flow] Step 2 FAILED: {e}")
        return

    # Step 3 — count pass/fail from allure-results JSONs
    print("[Slack Flow] Step 3: Counting results...")
    passed = failed = 0
    try:
        results_dir = os.path.join(BASE_DIR, "allure-results")
        for json_file in glob.glob(os.path.join(results_dir, "*-result.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            status = data.get("status", "").upper()
            if status == "PASSED":
                passed += 1
            else:
                failed += 1
        print(f"[Slack Flow] Step 3 done. Passed: {passed} | Failed: {failed}")
    except Exception as e:
        print(f"[Slack Flow] Step 3 FAILED: {e}")

    # Step 4 — deploy allure-report to Netlify
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

    # Step 5 — send report link to Slack
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
    """
    Runs entirely as a background task — the /slack/events endpoint already
    returned 200 OK before this runs, so Slack never retries.
    Downloads APK → resolves metadata → starts Appium → runs tests → deploys to Netlify → sends link to Slack.
    """
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

        # Ensure Appium is up before tests start
        await _ensure_appium_running()

        # Run tests → Netlify deploy → Slack message
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("Shutting down: Cleaning up child processes...")
    global _appium_proc, _allure_proc

    if _appium_proc is not None:
        try:
            print("Killing Appium...")
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                _appium_proc.kill()
        except Exception as e:
            print(f"Error killing Appium: {e}")

    if _allure_proc is not None:
        try:
            print("Killing Allure...")
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_allure_proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                _allure_proc.kill()
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

ALLURE_RESULTS_DIR = os.path.join(BASE_DIR, "allure-results")
os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
app.mount("/allure-results", StaticFiles(directory=ALLURE_RESULTS_DIR), name="allure-results")

UI_SCREENSHOTS_BASE = Path(__file__).resolve().parents[1] / "artifacts" / "ui_screenshots"
UI_SCREENSHOTS_BASE.mkdir(parents=True, exist_ok=True)
app.mount("/ui-screenshots", StaticFiles(directory=str(UI_SCREENSHOTS_BASE)), name="ui-screenshots")


# ─── Pydantic models ─────────────────────────────────────────────────────────

class AnalyzeReq(BaseModel):
    run_id: str | None = None

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


# ─── WebSocket manager ───────────────────────────────────────────────────────

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

        async def _safe_send(ws: WebSocket):
            try:
                await ws.send_json(message)
                return True
            except Exception:
                return False

        results = await asyncio.gather(
            *(_safe_send(ws) for ws in connections), return_exceptions=True
        )
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
#  ROUTES
# ════════════════════════════════════════════════════════════════════════════

def _latest_run_id() -> str:
    runs = [p for p in UI_SCREENSHOTS_BASE.iterdir() if p.is_dir()]
    if not runs:
        raise HTTPException(404, detail="No UI screenshots found.")
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].name


@app.post("/api/ui-screenshots/analyze")
def analyze_ui_screenshots(req: AnalyzeReq):
    run_id  = req.run_id or _latest_run_id()
    run_dir = UI_SCREENSHOTS_BASE / run_id
    if not run_dir.exists():
        raise HTTPException(404, detail=f"Run folder not found: {run_id}")

    validator = Path(__file__).resolve().parents[1] / "ui-parser" / "ui_screenshot_validator.py"
    if not validator.exists():
        raise HTTPException(500, detail=f"Validator not found: {validator}")

    proc = subprocess.run(
        [sys.executable, str(validator), "--root-dir", str(run_dir)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise HTTPException(500, detail=f"UI validator failed: {proc.stderr.strip() or proc.stdout.strip()}")

    payload = json.loads(proc.stdout or "{}")
    results = payload.get("results", [])
    for r in results:
        rel = r.get("relative_path")
        r["screenshot_url"] = f"/ui-screenshots/{run_id}/{rel}" if rel else None
    return {"run_id": run_id, "results": results}


@app.post("/api/run-complete")
async def run_complete(event: RunCompleteEvent):
    await manager.broadcast({"type": "RUN_COMPLETE", "payload": {"report_url": event.report_url}})
    return {"ok": True}


@app.post("/api/allure/start")
async def allure_start():
    port = _pick_free_port()
    subprocess.Popen(
        [ALLURE_CMD, "open", "-h", "127.0.0.1", "-p", str(port), ALLURE_REPORT_DIR],
        cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True,
    )
    return JSONResponse({"url": f"http://127.0.0.1:{port}/index.html"})


@app.get("/device-status")
async def device_status():
    try:
        result    = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        lines     = result.stdout.strip().splitlines()[1:]
        connected = any("\tdevice" in line for line in lines)
        return {"connected": connected}
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


@app.post("/api/log-step")
async def log_step(msg: LogMessage):
    _broadcast_async({"type": "LOG", "payload": {"message": msg.message, "status": msg.status}})
    return {"status": "ok"}


@app.post("/api/metric")
async def log_metric(data: dict):
    _broadcast_async({"type": "METRIC", "payload": data})
    return {"status": "ok"}


@app.post("/api/module-status")
async def module_status(data: dict):
    _broadcast_async({
        "type": "MODULE",
        "payload": {
            "module":  data.get("module"),
            "status":  data.get("status"),
            "message": data.get("message", ""),
        },
    })
    return {"status": "ok"}


@app.post("/start-test")
async def start_test(request: TestRequest, background_tasks: BackgroundTasks):
    global DOWNLOAD_PROCESS_OBJ

    if DOWNLOAD_PROCESS_OBJ is not None:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": "⚠️ A download/test is already running.", "status": "INFO"},
        })
        return {"status": "ignored", "message": "A download/test is already running."}

    await manager.broadcast({
        "type": "LOG",
        "payload": {"message": "Checking Appium server...", "status": "INFO"},
    })
    await _ensure_appium_running()

    try:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": "Starting APK download...", "status": "INFO"},
        })
        loop = asyncio.get_event_loop()

        def progress_callback(msg):
            clean = msg.replace("\r", "").strip()
            if clean:
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({
                        "type": "LOG",
                        "payload": {"message": clean, "status": "PROGRESS"},
                    }),
                    loop,
                )

        apk_path             = await loop.run_in_executor(None, lambda: download_apk(request.url, progress_callback))
        DOWNLOAD_PROCESS_OBJ = None

        icon_url      = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

        info         = get_apk_info(apk_path) or {}
        print(f"[APK Info] {info}")
        app_name     = info.get("app_name")
        package_name = info.get("package_name")

        app_variant  = PACKAGE_VARIANT_MAP.get(package_name)
        tests_to_run = request.tests_to_run or APP_VARIANTS.get(app_variant, [])

        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"Detected app variant: {app_variant}", "status": "INFO"},
        })

        background_tasks.add_task(run_tests_and_get_suggestions, apk_path, tests_to_run=tests_to_run)

        return {
            "status":       "success",
            "message":      "APK Downloaded. Test Starting...",
            "app_icon":     full_icon_url,
            "app_name":     app_name,
            "package_name": package_name,
            "apk_path":     apk_path,
            "app_variant":  app_variant,
        }

    except Exception as e:
        DOWNLOAD_PROCESS_OBJ = None
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"Download interrupted: {str(e)}", "status": "FAILED"},
        })
        raise HTTPException(status_code=400, detail=f"Download Failed: {str(e)}")


@app.post("/start-test-existing")
async def start_test_existing(request: ExistingTestRequest, background_tasks: BackgroundTasks):
    try:
        apk_path = os.path.join(APKS_DIR, request.apk_name)
        if not os.path.isfile(apk_path):
            raise HTTPException(status_code=404, detail="APK not found on server")

        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"Using existing APK: {request.apk_name}", "status": "INFO"},
        })

        await _ensure_appium_running()

        icon_url      = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

        info         = get_apk_info(apk_path) or {}
        print(f"[APK Info] {info}")
        app_name     = info.get("app_name")
        package_name = info.get("package_name")

        background_tasks.add_task(
            run_tests_and_get_suggestions, apk_path, tests_to_run=request.tests_to_run
        )

        return {
            "status":       "success",
            "message":      "Using existing APK. Test Starting...",
            "app_icon":     full_icon_url,
            "app_name":     app_name,
            "package_name": package_name,
            "apk_path":     apk_path,
        }

    except HTTPException:
        raise
    except Exception as e:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"Failed to start test: {str(e)}", "status": "FAILED"},
        })
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
    stopped = False

    if DOWNLOAD_PROCESS_OBJ is not None:
        try:
            DOWNLOAD_PROCESS_OBJ.terminate()
            stopped = True
        except Exception as e:
            print(f"Error stopping download: {e}")

    if stop_current_tests():
        stopped = True

    if stopped:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": "Backend: Process stopped on user request.", "status": "FAILED"},
        })
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
        return {"status": "running", "message": "Appium already running."}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", APPIUM_PORT)) == 0:
            return {"status": "running", "message": f"Appium already active on port {APPIUM_PORT}"}
    try:
        _appium_proc = subprocess.Popen(
            ["appium", "-p", str(APPIUM_PORT)],
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
            except Exception as e:
                print(f"taskkill error: {e}")
                _appium_proc.kill()
        else:
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
#  SLACK EVENTS  — returns 200 immediately, does ALL work in background
# ════════════════════════════════════════════════════════════════════════════

@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    global LAST_SLACK_EVENT_TS

    body = await request.json()

    # Slack URL-verification handshake
    if body.get("type") == "url_verification":
        return {"challenge": body["challenge"]}

    event = body.get("event", {})
    print("[Slack] Event received:", event)

    # Ignore bot messages, edited messages, etc.
    if event.get("subtype") is not None:
        return {"status": "ignored"}

    # Deduplicate — Slack retries if no 200 within 3 s
    event_ts = event.get("ts")
    if event_ts and event_ts == LAST_SLACK_EVENT_TS:
        print("[Slack] Duplicate event ignored.")
        return {"status": "duplicate"}
    LAST_SLACK_EVENT_TS = event_ts

    if event.get("type") == "message":
        text = event.get("text", "")
        if "drive.google.com" in text:
            file_id = extract_drive_file_id(text)
            if file_id:
                channel_id     = event.get("channel")
                sender_user_id = event.get("user")

                # Queue ALL heavy work AFTER returning 200
                # so Slack never retries / double-triggers
                background_tasks.add_task(
                    _handle_slack_apk,
                    file_id=file_id,
                    channel_id=channel_id,
                    sender_user_id=sender_user_id,
                )

    # Return 200 immediately — before any download or test starts
    return {"status": "ok"}


# ════════════════════════════════════════════════════════════════════════════
#  ENTRYPOINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)