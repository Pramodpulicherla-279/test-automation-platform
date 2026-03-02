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
import subprocess
import socket
import asyncio
from gdrive_loader import download_apk, extract_app_icon, get_apk_info
from typing import List, Optional, Dict
from starlette.websockets import WebSocketDisconnect

# Add project root to sys.path so we can import tests.*
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # root: f:\projects\test-automation-platform
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tests.test_runner import run_tests_and_get_suggestions, stop_current_tests, generate_report
# from gdrive_loader import download_apk, 

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
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

APKS_DIR = os.path.join(os.path.dirname(__file__), "temp_apks")
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
    
    try:
        # Tell frontend: starting download
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": "Starting APK download...", "status": "INFO"}
        })

        script_path = os.path.join(os.path.dirname(__file__), "gdrive_loader.py")
        apk_path = None

        # --- FIX: Force UTF-8 encoding for the subprocess ---
        # This prevents 'charmap' codec errors when printing emojis on Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # 1. Spawn the download subprocess
        # Using -u for unbuffered output to get real-time progress
        DOWNLOAD_PROCESS_OBJ = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script_path, request.url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env, 
        )

        # 2. Read the output stream
        async for line in DOWNLOAD_PROCESS_OBJ.stdout:
            decoded_line = line.decode('utf-8').strip()
            
            if decoded_line.startswith("PROGRESS:"):
                # Broadcast progress to UI
                raw_msg = decoded_line.replace("PROGRESS:", "")
                await manager.broadcast({
                    "type": "LOG",
                    "payload": {"message": raw_msg, "status": "PROGRESS"}
                })
            elif decoded_line.startswith("RESULT:"):
                # Capture the final file path
                apk_path = decoded_line.replace("RESULT:", "").strip()
            else:
                # Forward other logs
                if decoded_line:
                    await manager.broadcast({
                        "type": "LOG",
                        "payload": {"message": decoded_line, "status": "INFO"}
                    })

        # Wait for finish
        await DOWNLOAD_PROCESS_OBJ.wait()
        
         # 3. Check for failures
        if DOWNLOAD_PROCESS_OBJ.returncode != 0:
             # Read stderr to see why it crashed
            stderr_data = await DOWNLOAD_PROCESS_OBJ.stderr.read()
            error_message = stderr_data.decode('utf-8').strip() or "Unknown error (process killed?)"
            print(f"Subprocess Error: {error_message}")
            raise Exception(f"Script Error: {error_message}")

        if not apk_path:
            raise Exception("Download script finished but returned no path.")
            
        # Reset global ref
        DOWNLOAD_PROCESS_OBJ = None

        # 3. Extract Icon immediately after download
        icon_url = extract_app_icon(apk_path)

        # Construct full URL for Frontend
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

        info = get_apk_info(apk_path) or {}
        app_name = info.get("app_name")
        package_name = info.get("package_name")
        
        # 4. Trigger the actual Automation Test
        background_tasks.add_task(
                   run_tests_and_get_suggestions, 
                   apk_path, 
                   tests_to_run=request.tests_to_run
               )
        
        return {
            "status": "success", 
            "message": "APK Downloaded. Test Starting...",
            "app_icon": full_icon_url,
            "app_name": app_name,
            "package_name": package_name,
            "apk_path": apk_path
        }
    
    except Exception as e:
        DOWNLOAD_PROCESS_OBJ = None
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": f"Download interrupted: {str(e)}", "status": "FAILED"}
        })
        raise HTTPException(status_code=400, detail=f"Download Failed: {str(e)}")
    
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)