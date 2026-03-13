# server.py
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
import os
import sys
import requests
import re
from dotenv import load_dotenv

# ✅ NEW: Added csv and glob imports for CSV report generation
import csv
import glob

from gdrive_loader import download_apk, extract_app_icon, get_apk_info
from typing import List, Optional, Dict
from starlette.websockets import WebSocketDisconnect

LAST_SLACK_EVENT_TS = None

# Load environment variables from .env
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

print("Slack Token Loaded:", SLACK_BOT_TOKEN)


# Add project root to sys.path so we can import tests.*
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tests.test_runner import run_tests_and_get_suggestions, stop_current_tests, generate_report

print("server is running...")
# ---------------- APP VARIANT CONFIG ----------------

PACKAGE_VARIANT_MAP = {
    "com.agribride.krishivaas.farmer_app": "regular_farmer",
    "com.agribride.krishivaas.client_app": "regular_client",
    "com.agribride.krishivaas.farmer_state_app": "state_farmer",
    "com.agribride.krishivaas.client_state_app": "state_client",
}

APP_VARIANTS = {
    "regular_farmer": [
        {"name": "Login", "path": "tests/test_cases/regular_farmer_test_cases/test_login_pytest.py"},
        {"name": "Dashboard", "path": "tests/test_cases/regular_farmer_test_cases/TestOnboarding.py"},
        {"name": "Add Updates", "path": "tests/farmer/test_updates.py"},
    ],
    "regular_client": [
        {"name": "Login", "path": "tests/test_cases/regular_client_test_cases/login_pytest.py"},
        {"name": "Marketplace", "path": "tests/client/test_marketplace.py"},
        {"name": "Cart", "path": "tests/client/test_cart.py"},
    ],
    "state_farmer": [
        {"name": "Login", "path": "tests/state_farmer/test_login.py"},
        {"name": "Schemes", "path": "tests/state_farmer/test_schemes.py"},
    ],
    "state_client": [
        {"name": "Login", "path": "tests/test_cases/state_client_test_cases/test_login_pytest.py"},
        {"name": "Onboarding", "path": "tests/test_cases/state_client_test_cases/test_Onboarding.py"},
    ],
}


# ✅ NEW: Helper — fetch Slack user's real name from their user ID
def get_slack_user_name(user_id: str) -> str:
    """Fetch a Slack user's real name using their user ID."""
    try:
        resp = requests.get(
            "https://slack.com/api/users.info",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            params={"user": user_id},
        )
        data = resp.json()
        if data.get("ok"):
            return data["user"]["real_name"]
    except Exception as e:
        print(f"[Slack] Could not fetch user name: {e}")
    return "Unknown Developer"


# ✅ NEW: Generate CSV from allure-results JSON files
def generate_csv_report(output_path: str) -> str:
    """Parse Allure result JSONs and write a CSV summary."""
    results_dir = os.path.join(BASE_DIR, "allure-results")
    rows = []

    for json_file in glob.glob(os.path.join(results_dir, "*-result.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            rows.append({
                "Test Name": data.get("name", "Unknown"),
                "Status": data.get("status", "Unknown").upper(),
                "Duration (s)": round((data.get("stop", 0) - data.get("start", 0)) / 1000, 2),
                "Suite": data.get("suiteName", "N/A"),
                "Message": data.get("statusDetails", {}).get("message", "").replace("\n", " ")[:200],
            })
        except Exception as e:
            print(f"[CSV] Skipping {json_file}: {e}")

    # Write CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Test Name", "Status", "Duration (s)", "Suite", "Message"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[CSV] Report written: {output_path} ({len(rows)} tests)")
    return output_path


# ✅ NEW: Send CSV file to Slack with a summary message
def send_slack_report(channel_id: str, developer_name: str, app_name: str, apk_version: str, csv_path: str):
    """Upload CSV report to Slack with a summary message."""
    if not SLACK_BOT_TOKEN:
        print("[Slack] No bot token — cannot send report.")
        return

    # Count pass/fail from CSV
    passed = failed = 0
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Status"] == "PASSED":
                    passed += 1
                else:
                    failed += 1
    except Exception as e:
        print(f"[Slack] Could not read CSV for summary: {e}")

    summary = (
        f"✅ *Automation Report Ready!*\n"
        f"👤 *Developer:* {developer_name}\n"
        f"📱 *App:* {app_name}\n"
        f"🔖 *Version:* {apk_version}\n"
        f"🟢 Passed: {passed}  |  🔴 Failed: {failed}"
    )

    try:
        with open(csv_path, "rb") as f:
            resp = requests.post(
                "https://slack.com/api/files.upload",
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                data={
                    "channels": channel_id,
                    "initial_comment": summary,
                    "filename": f"{app_name}_v{apk_version}_report.csv",
                    "title": f"Allure Report — {app_name} v{apk_version}",
                },
                files={"file": f},
            )
        data = resp.json()
        if not data.get("ok"):
            print(f"[Slack] File upload failed: {data.get('error')}")
        else:
            print("[Slack] CSV report sent to Slack successfully!")
    except Exception as e:
        print(f"[Slack] Exception uploading file: {e}")


# --- Cleanup Handler (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("Shutting down: Cleaning up child processes...")
    global _appium_proc, _allure_proc
    
    if _appium_proc is not None:
        try:
            print("Killing Appium...")
            if os.name == 'nt':
                 subprocess.run(["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                 _appium_proc.kill()
        except Exception as e:
            print(f"Error killing Appium: {e}")

    if _allure_proc is not None:
        try:
            print("Killing Allure...")
            if os.name == 'nt':
                 subprocess.run(["taskkill", "/F", "/T", "/PID", str(_allure_proc.pid)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                 _allure_proc.kill()
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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

_allure_proc: subprocess.Popen | None = None
_allure_port: int | None = None

_appium_proc: subprocess.Popen | None = None
APPIUM_PORT = 4723

ALLURE_CMD = r"C:\Users\Pramo\scoop\shims\allure"

UI_SCREENSHOTS_BASE = Path(__file__).resolve().parents[1] / "artifacts" / "ui_screenshots"
UI_SCREENSHOTS_BASE.mkdir(parents=True, exist_ok=True)

app.mount("/ui-screenshots", StaticFiles(directory=str(UI_SCREENSHOTS_BASE)), name="ui-screenshots")


class AnalyzeReq(BaseModel):
    run_id: str | None = None


def _latest_run_id() -> str:
    runs = [p for p in UI_SCREENSHOTS_BASE.iterdir() if p.is_dir()]
    if not runs:
        raise HTTPException(404, detail="No UI screenshots found. Run tests and capture screenshots first.")
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].name


@app.post("/api/ui-screenshots/analyze")
def analyze_ui_screenshots(req: AnalyzeReq):
    print("UI parser api called")
    run_id = req.run_id or _latest_run_id()
    print(run_id)
    run_dir = UI_SCREENSHOTS_BASE / run_id
    if not run_dir.exists():
        raise HTTPException(404, detail=f"Run screenshots folder not found: {run_id}")

    validator = Path(__file__).resolve().parents[1] / "ui-parser" / "ui_screenshot_validator.py"
    if not validator.exists():
        raise HTTPException(500, detail=f"Validator script not found: {validator}")

    cmd = [sys.executable, str(validator), "--root-dir", str(run_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        raise HTTPException(500, detail=f"UI validator failed: {proc.stderr.strip() or proc.stdout.strip()}")

    payload = json.loads(proc.stdout or "{}")
    results = payload.get("results", [])

    for r in results:
        rel = r.get("relative_path")
        r["screenshot_url"] = f"/ui-screenshots/{run_id}/{rel}" if rel else None

    return {"run_id": run_id, "results": results}

def _start_allure_server() -> str:
    global _allure_proc, _allure_port

    if not os.path.isdir(ALLURE_REPORT_DIR):
        raise HTTPException(status_code=404, detail=f"Allure report dir not found: {ALLURE_REPORT_DIR}")

    if _allure_proc is not None and _allure_proc.poll() is None:
        try:
            _allure_proc.terminate()
        except Exception:
            pass
        _allure_proc = None

    _allure_port = _pick_free_port()

    _allure_proc = subprocess.Popen(
        ["allure", "open", "-h", "127.0.0.1", "-p", str(_allure_port), ALLURE_REPORT_DIR],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )

    return f"http://127.0.0.1:{_allure_port}"


class RunCompleteEvent(BaseModel):
    report_url: str

class ExistingTestRequest(BaseModel):
    apk_name: str
    tests_to_run: Optional[List[Dict[str, str]]] = None

class LogMessage(BaseModel):
    message: str
    status: str = "INFO"

DOWNLOAD_PROCESS_OBJ = None


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

        results = await asyncio.gather(*(_safe_send(ws) for ws in connections), return_exceptions=True)

        for ws, ok in zip(connections, results):
            if ok is not True:
                await self.disconnect(ws)

class TestRequest(BaseModel):
    url: str
    tests_to_run: Optional[List[Dict[str, str]]] = None

manager = ConnectionManager()

@app.post("/api/run-complete")
async def run_complete(event: RunCompleteEvent):
    await manager.broadcast({
        "type": "RUN_COMPLETE",
        "payload": {"report_url": event.report_url}
    })
    return {"ok": True}

def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])

@app.post("/api/allure/start")
async def allure_start():
    port = _pick_free_port()
    subprocess.Popen(
        [ALLURE_CMD, "open", "-h", "127.0.0.1", "-p", str(port), ALLURE_REPORT_DIR],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True
    )
    url = f"http://127.0.0.1:{port}"
    return JSONResponse({"url": url})

@app.get("/device-status")
async def device_status():
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = result.stdout.strip().splitlines()[1:]
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

def _broadcast_async(message: dict) -> None:
    try:
        asyncio.create_task(manager.broadcast(message))
    except RuntimeError:
        pass

@app.post("/api/log-step")
async def log_step(msg: LogMessage):
    _broadcast_async({
        "type": "LOG",
        "payload": {"message": msg.message, "status": msg.status},
    })
    return {"status": "ok"}

@app.post("/api/metric")
async def log_metric(data: dict):
    _broadcast_async({"type": "METRIC", "payload": data})
    return {"status": "ok"}

@app.post("/api/module-status")
async def module_status(data: dict):
    module = data.get("module")
    status = data.get("status")
    message = data.get("message", "")

    _broadcast_async({
        "type": "MODULE",
        "payload": {"module": module, "status": status, "message": message},
    })
    return {"status": "ok"}

@app.post("/start-test")
async def start_test(request: TestRequest, background_tasks: BackgroundTasks):

    global DOWNLOAD_PROCESS_OBJ
    global _appium_proc

    if DOWNLOAD_PROCESS_OBJ is not None:
        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": "⚠️ A download/test is already running. Ignoring duplicate request.",
                "status": "INFO"
            }
        })
        return {
            "status": "ignored",
            "message": "A download/test is already running."
        }

    if _appium_proc is None or _appium_proc.poll() is not None:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": "Starting Appium server...", "status": "INFO"}
        })

        _appium_proc = subprocess.Popen(
            ["appium", "-p", str(APPIUM_PORT)],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        await asyncio.sleep(5)

    try:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": "Starting APK download...", "status": "INFO"}
        })

        loop = asyncio.get_event_loop()

        def progress_callback(msg):
            clean = msg.replace('\r', '').strip()
            if clean:
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({
                        "type": "LOG",
                        "payload": {"message": clean, "status": "PROGRESS"}
                    }),
                    loop
                )

        apk_path = await loop.run_in_executor(
            None,
            lambda: download_apk(request.url, progress_callback)
        )

        DOWNLOAD_PROCESS_OBJ = None

        icon_url = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

        info = get_apk_info(apk_path) or {}
        app_name = info.get("app_name")
        package_name = info.get("package_name")

        app_variant = PACKAGE_VARIANT_MAP.get(package_name)
        tests_to_run = request.tests_to_run or APP_VARIANTS.get(app_variant, [])

        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": f"Detected app variant: {app_variant}",
                "status": "INFO"
            }
        })

        background_tasks.add_task(
            run_tests_and_get_suggestions,
            apk_path,
            tests_to_run=tests_to_run
        )

        return {
            "status": "success",
            "message": "APK Downloaded. Test Starting...",
            "app_icon": full_icon_url,
            "app_name": app_name,
            "package_name": package_name,
            "apk_path": apk_path,
            "app_variant": app_variant
        }

    except Exception as e:
        DOWNLOAD_PROCESS_OBJ = None

        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": f"Download interrupted: {str(e)}",
                "status": "FAILED"
            }
        })

        raise HTTPException(
            status_code=400,
            detail=f"Download Failed: {str(e)}"
        )

@app.post("/start-test-existing")
async def start_test_existing(request: ExistingTestRequest, background_tasks: BackgroundTasks):
    try:
        apk_path = os.path.join(APKS_DIR, request.apk_name)

        if not os.path.isfile(apk_path):
            raise HTTPException(status_code=404, detail="APK not found on server")

        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": f"Using existing APK: {request.apk_name}",
                "status": "INFO",
            }
        })

        icon_url = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

        info = get_apk_info(apk_path) or {}
        app_name = info.get("app_name")
        package_name = info.get("package_name")

        background_tasks.add_task(
            run_tests_and_get_suggestions, 
            apk_path, 
            tests_to_run=request.tests_to_run
        )
        return {
            "status": "success",
            "message": "Using existing APK. Test Starting...",
            "app_icon": full_icon_url,
            "app_name": app_name,
            "package_name": package_name,
            "apk_path": apk_path,
        }

    except HTTPException:
        raise
    except Exception as e:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"Failed to start test: {str(e)}", "status": "FAILED"}
        })
        raise HTTPException(status_code=400, detail=f"Failed: {str(e)}")
    
@app.get("/api/apk-list")
async def list_apks():
    try:
        files = []
        for name in os.listdir(APKS_DIR):
            if name.lower().endswith((".apk", ".apks")):
                files.append(name)
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
            print("DEBUG: Terminating download process...")
            DOWNLOAD_PROCESS_OBJ.terminate()
            stopped_something = True
        except Exception as e:
            print(f"Error stopping download: {e}")

    test_stopped = stop_current_tests()
    if test_stopped:
        stopped_something = True
    print(f"DEBUG: stop_current_tests() -> {test_stopped}")

    if stopped_something:
        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": "Backend: Process (Download/Test) stopped on user request.",
                "status": "FAILED",
            }
        })
        return {"status": "stopped"}
    else:
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
        if s.connect_ex(('127.0.0.1', APPIUM_PORT)) == 0:
             return {"status": "running", "message": f"Appium (or something) already active on port {APPIUM_PORT}"}

    try:
        _appium_proc = subprocess.Popen(
            ["appium", "-p", str(APPIUM_PORT)],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "started", "message": f"Appium started on port {APPIUM_PORT}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/appium/stop")
async def appium_stop():
    global _appium_proc
    if _appium_proc is not None:
        if os.name == 'nt':
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)],
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"Error executing taskkill: {e}")
                _appium_proc.kill()
        
        _appium_proc = None
        return {"status": "stopped"}
    
    return {"status": "not_running"}

@app.post("/api/generate-report")
async def api_generate_report():
    try:
        import threading
        t = threading.Thread(target=generate_report)
        t.start()
        return {"status": "ok", "message": "Report generation started"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ✅ NEW: Background task — runs tests, generates CSV, sends to Slack
async def _run_tests_and_notify_slack(
    apk_path: str,
    tests_to_run: list,
    channel_id: str,
    developer_name: str,
    app_name: str,
    apk_version: str,
):
    """Run automation tests, generate CSV report, then post it to Slack."""
    loop = asyncio.get_event_loop()

    # Step 1: Run tests (blocking, so run in thread pool)
    await loop.run_in_executor(
        None,
        lambda: run_tests_and_get_suggestions(apk_path, tests_to_run=tests_to_run)
    )

    # Step 2: Generate Allure report so allure-results JSONs are fresh
    await loop.run_in_executor(None, generate_report)

    # Step 3: Generate CSV from allure-results
    safe_app_name = app_name.replace(" ", "_") if app_name else "App"
    safe_version = apk_version.replace(" ", "_") if apk_version else "unknown"
    csv_path = os.path.join(BASE_DIR, f"report_{safe_app_name}_v{safe_version}.csv")
    await loop.run_in_executor(None, lambda: generate_csv_report(csv_path))

    # Step 4: Send CSV file to Slack
    send_slack_report(
        channel_id=channel_id,
        developer_name=developer_name,
        app_name=app_name or "Unknown App",
        apk_version=apk_version or "Unknown",
        csv_path=csv_path,
    )


@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):

    global LAST_SLACK_EVENT_TS

    body = await request.json()

    if body.get("type") == "url_verification":
        return {"challenge": body["challenge"]}

    event = body.get("event", {})
    print("Slack Event Received:", event)

    if event.get("subtype") is not None:
        return {"status": "ignored"}

    event_ts = event.get("ts")
    if event_ts == LAST_SLACK_EVENT_TS:
        print("Duplicate Slack event ignored")
        return {"status": "duplicate"}

    LAST_SLACK_EVENT_TS = event_ts

    if event.get("type") == "message":
        text = event.get("text", "")
        print("Message text:", text)

        if "drive.google.com" in text:
            file_id = extract_drive_file_id(text)

            if file_id:
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

                # ✅ NEW: Capture channel and sender info for Slack reply
                channel_id = event.get("channel")
                sender_user_id = event.get("user")
                developer_name = get_slack_user_name(sender_user_id)

                print("Google Drive APK detected")
                print("Download URL:", download_url)
                print(f"[Slack] Developer: {developer_name}")

                try:
                    print("APK downloading from slack event started")
                    from gdrive_loader import download_apk, get_apk_info
                    loop = asyncio.get_event_loop()
                    apk_path = await loop.run_in_executor(None, lambda: download_apk(download_url))
                    info = get_apk_info(apk_path) or {}
                    package_name = info.get("package_name")

                    # ✅ NEW: Extract app_name and apk_version for the Slack report
                    app_name = info.get("app_name", "Unknown App")
                    apk_version = info.get("version_name") or info.get("version_code") or "Unknown"

                    app_variant = PACKAGE_VARIANT_MAP.get(package_name)
                    tests_to_run = APP_VARIANTS.get(app_variant, [])

                    print(f"[Slack] app_variant: {app_variant}")
                    print(f"[Slack] tests_to_run: {tests_to_run}")
                    print(f"[Slack] app_name: {app_name} | version: {apk_version}")

                    await manager.broadcast({
                        "type": "LOG",
                        "payload": {
                            "message": f"[Slack] {developer_name} triggered: {app_name} v{apk_version} | Variant: {app_variant}",
                            "status": "INFO"
                        }
                    })

                    # ✅ NEW: Use _run_tests_and_notify_slack instead of run_tests_and_get_suggestions
                    # This runs tests → generates CSV → sends report back to Slack automatically
                    background_tasks.add_task(
                        _run_tests_and_notify_slack,
                        apk_path=apk_path,
                        tests_to_run=tests_to_run,
                        channel_id=channel_id,
                        developer_name=developer_name,
                        app_name=app_name,
                        apk_version=apk_version,
                    )

                except Exception as e:
                    print(f"[Slack] Error resolving APK info: {e}")
                    # Fallback: run tests without Slack notification
                    background_tasks.add_task(
                        run_tests_and_get_suggestions,
                        apk_path,
                    )

    return {"status": "ok"}

def extract_drive_file_id(text):
    text = text.replace("<", "").replace(">", "")
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', text)
    return match.group(1) if match else None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)