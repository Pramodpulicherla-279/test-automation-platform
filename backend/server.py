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

from gdrive_loader import download_apk, extract_app_icon, get_apk_info
from typing import List, Optional, Dict
from starlette.websockets import WebSocketDisconnect

LAST_SLACK_EVENT_TS = None

# Load environment variables from .env
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

print("Slack Token Loaded:", SLACK_BOT_TOKEN)


# Add project root to sys.path so we can import tests.*
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # root: f:\projects\test-automation-platform
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tests.test_runner import run_tests_and_get_suggestions, stop_current_tests, generate_report
# from gdrive_loader import download_apk, 

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
# --- NEW: Cleanup Handler (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run on startup
    yield
    # Run on shutdown (Ctrl+C)
    print("Shutting down: Cleaning up child processes...")
    global _appium_proc, _allure_proc
    
    # Kill Appium
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

    # Kill Allure
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

# app = FastAPI()

# CORS: allow your React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],  # adjust if your frontend runs on a different port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use absolute path and auto-create the dir
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

APKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_apks")
os.makedirs(APKS_DIR, exist_ok=True)

# Serve generated Allure report (will be created by test_runner)
ALLURE_REPORT_DIR = os.path.join(BASE_DIR, "allure-report")
os.makedirs(ALLURE_REPORT_DIR, exist_ok=True)
app.mount("/allure-report", StaticFiles(directory=ALLURE_REPORT_DIR, html=True), name="allure-report")

_allure_proc: subprocess.Popen | None = None
_allure_port: int | None = None

# --- NEW: Appium Globals ---
_appium_proc: subprocess.Popen | None = None
APPIUM_PORT = 4723

ALLURE_CMD = r"C:\Users\Pramo\scoop\shims\allure"

# Base screenshots directory created by pytest conftest.py
UI_SCREENSHOTS_BASE = Path(__file__).resolve().parents[1] / "artifacts" / "ui_screenshots"
UI_SCREENSHOTS_BASE.mkdir(parents=True, exist_ok=True)

# Serve images so React can load them via URL:
# GET http://localhost:8000/ui-screenshots/<run_id>/<...>/<file>.png
app.mount("/ui-screenshots", StaticFiles(directory=str(UI_SCREENSHOTS_BASE)), name="ui-screenshots")


class AnalyzeReq(BaseModel):
    run_id: str | None = None  # optional; if not sent we auto-pick latest


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

    # Call validator as subprocess to avoid import issues (folder name ui-parser has a hyphen)
    cmd = [sys.executable, str(validator), "--root-dir", str(run_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        raise HTTPException(500, detail=f"UI validator failed: {proc.stderr.strip() or proc.stdout.strip()}")

    payload = json.loads(proc.stdout or "{}")
    results = payload.get("results", [])

    # Add screenshot_url expected by your React component
    for r in results:
        rel = r.get("relative_path")
        r["screenshot_url"] = f"/ui-screenshots/{run_id}/{rel}" if rel else None

    return {"run_id": run_id, "results": results}

def _start_allure_server() -> str:
    """
    Starts (or restarts) `allure open` server for the generated allure-report folder.
    Returns the URL the frontend should open.
    Requires: Allure CLI installed and in PATH.
    """
    global _allure_proc, _allure_port

    if not os.path.isdir(ALLURE_REPORT_DIR):
        raise HTTPException(status_code=404, detail=f"Allure report dir not found: {ALLURE_REPORT_DIR}")

    # Kill previous server if running
    if _allure_proc is not None and _allure_proc.poll() is None:
        try:
            _allure_proc.terminate()
        except Exception:
            pass
        _allure_proc = None

    _allure_port = _pick_free_port()

    # Start Allure server
    # (Allure CLI: `allure open -h <host> -p <port> <report_dir>`)
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
    tests_to_run: Optional[List[Dict[str, str]]] = None  # Added field

class LogMessage(BaseModel):
    message: str
    status: str = "INFO"

# --- Globals to manage child processes ---
DOWNLOAD_PROCESS_OBJ = None  # Holds the asyncio Process object

# 1. Connection Manager for WebSockets
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
        # Send concurrently + drop dead sockets (prevents one bad client from killing logs)
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

        # Remove failed connections
        for ws, ok in zip(connections, results):
            if ok is not True:
                await self.disconnect(ws)

class TestRequest(BaseModel):
    url: str
    tests_to_run: Optional[List[Dict[str, str]]] = None # Added field

manager = ConnectionManager()

@app.post("/api/run-complete")
async def run_complete(event: RunCompleteEvent):
    # Push an explicit event so frontend can react
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
    """
    Start Allure server (allure open) and return the URL.
    """
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
    """
    Returns whether at least one physical Android device is connected via ADB.
    """
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = result.stdout.strip().splitlines()[1:]  # skip header
        connected = any("\tdevice" in line for line in lines)
        return {"connected": connected}
    except Exception:
        # If adb is not installed or any error occurs, treat as no device
        return {"connected": False}

# 2. WebSocket Endpoint (Frontend connects here)
@app.websocket("/ws/test-status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Most frontends never send messages; this just keeps the socket open
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)

def _broadcast_async(message: dict) -> None:
    # Fire-and-forget broadcast so HTTP endpoints return immediately
    try:
        asyncio.create_task(manager.broadcast(message))
    except RuntimeError:
        # If no running loop (rare), just skip
        pass

# 3. The "Loopback" Endpoint (Pytest calls this)
@app.post("/api/log-step")
async def log_step(msg: LogMessage):
    _broadcast_async({
        "type": "LOG",
        "payload": {"message": msg.message, "status": msg.status},
    })
    return {"status": "ok"}

# 4. The "Profiler" Endpoint (Sidecar calls this)
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

    # Prevent duplicate downloads/tests
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

    # Start Appium if not running
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

        # Extract icon
        icon_url = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

        info = get_apk_info(apk_path) or {}
        app_name = info.get("app_name")
        package_name = info.get("package_name")

        app_variant = PACKAGE_VARIANT_MAP.get(package_name)
        # tests_to_run = APP_VARIANTS.get(app_variant, [])
        tests_to_run = request.tests_to_run or APP_VARIANTS.get(app_variant, [])

        await manager.broadcast({
            "type": "LOG",
            "payload": {
                "message": f"Detected app variant: {app_variant}",
                "status": "INFO"
            }
        })

        # Run automation tests
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
    """
    Start tests using an already-downloaded APK in backend/temp_apks.
    """
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

        # Extract icon / app info
        icon_url = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

        info = get_apk_info(apk_path) or {}
        app_name = info.get("app_name")
        package_name = info.get("package_name")

        # Run tests in background
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
    """
    Return list of already-downloaded APK files from backend/temp_apks.
    """
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
    """
    Stop the currently running pytest process OR the downloading process.
    """
    print("DEBUG: /stop-test called")
    
    stopped_something = False
    
    # 1. Check/Stop Download Process
    global DOWNLOAD_PROCESS_OBJ
    if DOWNLOAD_PROCESS_OBJ is not None:
        try:
            print("DEBUG: Terminating download process...")
            DOWNLOAD_PROCESS_OBJ.terminate()
            stopped_something = True
        except Exception as e:
            print(f"Error stopping download: {e}")
        # Note: We rely on the start_test loop to clean up DOWNLOAD_PROCESS_OBJ = None

    # 2. Check/Stop Pytest Process
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
    
# --- NEW: Appium Endpoints ---

@app.get("/api/appium/status")
async def appium_status():
    """Check if Appium process is running."""
    global _appium_proc
    if _appium_proc is not None and _appium_proc.poll() is None:
        return {"status": "running", "port": APPIUM_PORT}
    return {"status": "stopped"}

@app.post("/api/appium/start")
async def appium_start():
    """Start the Appium Server."""
    global _appium_proc
    
    # 1. Check if already running via Python
    if _appium_proc is not None and _appium_proc.poll() is None:
        return {"status": "running", "message": "Appium is already running via backend."}

    # 2. Check if port is locked (e.g. running from external terminal)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', APPIUM_PORT)) == 0:
             return {"status": "running", "message": f"Appium (or something) already active on port {APPIUM_PORT}"}

    try:
        # Start Appium. Assumes 'appium' is in your System PATH.
        # On Windows, shell=True is often needed for npm binaries.
        _appium_proc = subprocess.Popen(
            ["appium", "-p", str(APPIUM_PORT)],
            shell=True,
            stdout=subprocess.DEVNULL, # Or redirect to a log file
            stderr=subprocess.DEVNULL
        )
        return {"status": "started", "message": f"Appium started on port {APPIUM_PORT}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/appium/stop")
async def appium_stop():
    """Stop the Appium Server."""
    global _appium_proc
    if _appium_proc is not None:
        # On Windows with shell=True, terminate/kill only kills the shell (cmd.exe), not Appium (node.exe).
        # We need to strictly kill the process tree.
        if os.name == 'nt':
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)],
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"Error executing taskkill: {e}")
                # Fallback if taskkill fails for some reason
                _appium_proc.kill()
        
        _appium_proc = None
        return {"status": "stopped"}
    
    return {"status": "not_running"}

@app.post("/api/generate-report")
async def api_generate_report():
    """Manually trigger report generation."""
    try:
        # Run in thread pool to avoid blocking
        import threading
        t = threading.Thread(target=generate_report)
        t.start()
        return {"status": "ok", "message": "Report generation started"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    


@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):  # ✅ inject BackgroundTasks

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
                print("Google Drive APK detected")
                print("Download URL:", download_url)

                # ✅ Resolve APK info BEFORE calling start_test so we can log tests_to_run
                try:
                    print("apk downloading from slack event started")
                    from gdrive_loader import download_apk, get_apk_info
                    loop = asyncio.get_event_loop()
                    apk_path = await loop.run_in_executor(None, lambda: download_apk(download_url))
                    info = get_apk_info(apk_path) or {}
                    package_name = info.get("package_name")
                    app_variant = PACKAGE_VARIANT_MAP.get(package_name)
                    tests_to_run = APP_VARIANTS.get(app_variant, [])

                    # ✅ Debug log — visible in your console
                    print(f"[Slack] app_variant: {app_variant}")
                    print(f"[Slack] tests_to_run: {tests_to_run}")

                    await manager.broadcast({
                        "type": "LOG",
                        "payload": {
                            "message": f"[Slack] Detected variant: {app_variant} | Tests: {[t['name'] for t in tests_to_run]}",
                            "status": "INFO"
                        }
                    })

                    # ✅ Pass background_tasks from FastAPI DI + resolved tests_to_run
                    await start_test(
                        TestRequest(url=download_url, tests_to_run=tests_to_run),
                        background_tasks  # ✅ use the injected one, not a manually created one
                    )

                except Exception as e:
                    print(f"[Slack] Error resolving APK info: {e}")
                    # Fallback: call start_test without tests_to_run (it will auto-resolve)
                    await start_test(
                        TestRequest(url=download_url),
                        background_tasks
                    )

    return {"status": "ok"}

def extract_drive_file_id(text):
    text = text.replace("<", "").replace(">", "")
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', text)
    return match.group(1) if match else None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)