# server.py
import os
import sys
sys.dont_write_bytecode = True
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
from pydantic import BaseModel
import subprocess
import socket
import asyncio
from datetime import datetime
from gdrive_loader import download_apk, extract_app_icon, get_apk_info
from typing import List, Optional, Dict
from starlette.websockets import WebSocketDisconnect

# Add project root to sys.path so we can import tests.*
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # root: f:\projects\test-automation-platform
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tests.test_runner import run_tests_and_get_suggestions, stop_current_tests, generate_report
from api_matrix import (
    storage, executor, Endpoint, Environment, TestSuite,
    APIMatrixStorage, APITestExecutor
)
from load_test_runner import K6LoadTestRunner
from performance_collector import PerformanceDataCollector
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

# ============================================================================
# API MATRIX TESTER ENDPOINTS
# ============================================================================

# Endpoints Management
@app.get("/api/matrix/endpoints")
async def get_endpoints():
    """Get all API endpoints"""
    return storage.get_endpoints()

@app.post("/api/matrix/endpoints")
async def create_endpoint(endpoint: Endpoint):
    """Create a new endpoint"""
    storage.add_endpoint(endpoint)
    await manager.broadcast({
        "type": "API_MATRIX",
        "payload": {"action": "endpoint_created", "endpoint": endpoint.dict()}
    })
    return {"status": "ok", "endpoint": endpoint.dict()}

@app.put("/api/matrix/endpoints/{endpoint_id}")
async def update_endpoint(endpoint_id: str, endpoint: Endpoint):
    """Update an existing endpoint"""
    if storage.update_endpoint(endpoint_id, endpoint):
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {"action": "endpoint_updated", "endpoint": endpoint.dict()}
        })
        return {"status": "ok", "endpoint": endpoint.dict()}
    raise HTTPException(status_code=404, detail="Endpoint not found")

@app.delete("/api/matrix/endpoints/{endpoint_id}")
async def delete_endpoint(endpoint_id: str):
    """Delete an endpoint"""
    if storage.delete_endpoint(endpoint_id):
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {"action": "endpoint_deleted", "endpoint_id": endpoint_id}
        })
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Endpoint not found")

# Environments Management
@app.get("/api/matrix/environments")
async def get_environments():
    """Get all environments"""
    return storage.get_environments()

@app.post("/api/matrix/environments")
async def create_environment(environment: Environment):
    """Create a new environment"""
    storage.add_environment(environment)
    await manager.broadcast({
        "type": "API_MATRIX",
        "payload": {"action": "environment_created", "environment": environment.dict()}
    })
    return {"status": "ok", "environment": environment.dict()}

@app.put("/api/matrix/environments/{env_id}")
async def update_environment(env_id: str, environment: Environment):
    """Update an existing environment"""
    if storage.update_environment(env_id, environment):
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {"action": "environment_updated", "environment": environment.dict()}
        })
        return {"status": "ok", "environment": environment.dict()}
    raise HTTPException(status_code=404, detail="Environment not found")

@app.delete("/api/matrix/environments/{env_id}")
async def delete_environment(env_id: str):
    """Delete an environment"""
    if storage.delete_environment(env_id):
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {"action": "environment_deleted", "env_id": env_id}
        })
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Environment not found")

# Test Execution
@app.post("/api/matrix/run-single")
async def run_single_test(endpoint_id: str, env_id: str):
    """Run a single test"""
    try:
        endpoints = storage.get_endpoints()
        environments = storage.get_environments()
        
        endpoint = next((e for e in endpoints if e['id'] == endpoint_id), None)
        environment = next((e for e in environments if e['id'] == env_id), None)
        
        if not endpoint or not environment:
            raise HTTPException(status_code=404, detail="Endpoint or environment not found")
        
        # Broadcast start
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {"action": "test_start", "endpoint_id": endpoint_id, "env_id": env_id}
        })
        
        # Execute test
        result = await executor.run_request(endpoint, environment)
        
        # Broadcast result
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {"action": "test_result", "result": result.dict()}
        })
        
        return result.dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/matrix/run-all")
async def run_all_tests():
    """Run all tests across all endpoints and environments"""
    try:
        endpoints = storage.get_endpoints()
        environments = storage.get_environments()
        
        if not endpoints or not environments:
            raise HTTPException(status_code=400, detail="No endpoints or environments configured")
        
        start_time = asyncio.get_event_loop().time()
        
        # Broadcast start
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {
                "action": "batch_start",
                "total": len(endpoints) * len(environments)
            }
        })
        
        # Define callback for progress
        async def progress_callback(data):
            await manager.broadcast({
                "type": "API_MATRIX",
                "payload": {
                    "action": "batch_progress",
                    "progress": data['progress'],
                    "current": data['current'],
                    "total": data['total'],
                    "result": data['result']
                }
            })
        
        # Execute batch
        results = await executor.run_batch(endpoints, environments, progress_callback)
        
        duration = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        # Calculate summary
        passed = len([r for r in results if r.pass_])
        failed = len([r for r in results if not r.pass_])
        
        summary = {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast completion
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {
                "action": "batch_complete",
                "summary": summary
            }
        })
        
        return {
            "status": "ok",
            "results": [r.dict() for r in results],
            "summary": summary
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Test Suites
@app.get("/api/matrix/suites")
async def list_suites():
    """List all saved test suites"""
    return storage.list_suites()

@app.post("/api/matrix/suites")
async def create_suite(suite: TestSuite):
    """Create a new test suite"""
    storage.save_suite(suite)
    await manager.broadcast({
        "type": "API_MATRIX",
        "payload": {"action": "suite_created", "suite": suite.dict()}
    })
    return {"status": "ok", "suite": suite.dict()}

@app.get("/api/matrix/suites/{suite_id}")
async def get_suite(suite_id: str):
    """Get a specific test suite"""
    suite = storage.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    return suite

@app.get("/api/matrix/suites/{suite_id}/results")
async def get_suite_results(suite_id: str):
    """Get results for a specific test suite"""
    results = storage.get_results(suite_id)
    return results

@app.post("/api/matrix/suites/{suite_id}/run")
async def run_suite(suite_id: str):
    """Execute a complete test suite"""
    try:
        suite = storage.get_suite(suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")
        
        endpoints = suite['endpoints']
        environments = suite['environments']
        
        start_time = asyncio.get_event_loop().time()
        
        # Broadcast start
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {
                "action": "suite_run_start",
                "suite_id": suite_id,
                "total": len(endpoints) * len(environments)
            }
        })
        
        # Execute tests
        async def progress_callback(data):
            await manager.broadcast({
                "type": "API_MATRIX",
                "payload": {
                    "action": "suite_run_progress",
                    "suite_id": suite_id,
                    **data
                }
            })
        
        results = await executor.run_batch(endpoints, environments, progress_callback)
        
        duration = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        # Calculate summary
        passed = len([r for r in results if r.pass_])
        failed = len([r for r in results if not r.pass_])
        
        summary = {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast completion
        await manager.broadcast({
            "type": "API_MATRIX",
            "payload": {
                "action": "suite_run_complete",
                "suite_id": suite_id,
                "summary": summary
            }
        })
        
        return {
            "status": "ok",
            "results": [r.dict() for r in results],
            "summary": summary
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health/Status
@app.get("/api/matrix/health")
async def matrix_health():
    """Check API Matrix health"""
    endpoints_count = len(storage.get_endpoints())
    environments_count = len(storage.get_environments())
    suites_count = len(storage.list_suites())
    
    return {
        "status": "ok",
        "endpoints": endpoints_count,
        "environments": environments_count,
        "suites": suites_count
    }

# ============================================================================
# AUTOMATION API TEST RESULTS ENDPOINT
# ============================================================================

class AutomationAPIResult(BaseModel):
    endpoint: str
    method: str
    description: str = ""
    expected_status: int
    actual_status: int
    passed: bool
    error: Optional[str] = None
    duration: int = 0
    timestamp: str = ""

@app.post("/api/matrix/automation-results")
async def save_automation_api_results(results: List[Dict]):
    """
    Save API test results from automation execution.
    This endpoint receives API validation results from pytest tests.
    
    Args:
        results: List of API test results from automation
        
    Returns:
        Saved results with summary
    """
    try:
        if not results:
            return {
                "status": "ok",
                "saved": 0,
                "summary": {"total": 0, "passed": 0, "failed": 0}
            }
        
        # Calculate summary
        passed = sum(1 for r in results if r.get("passed", False))
        failed = len(results) - passed
        
        # Store each result in an "Automation" suite
        suite_id = "automation_results"
        automation_suite = storage.get_suite(suite_id)
        
        # Create suite if doesn't exist
        if not automation_suite:
            automation_suite = {
                "id": suite_id,
                "name": "Automation API Results",
                "description": "API test results from automated test execution",
                "endpoints": [],
                "environments": [],
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat()
            }
            storage.save_suite(automation_suite)
        
        # Save each result
        for result_data in results:
            test_result = {
                "key": f"{result_data.get('endpoint', 'unknown')}::{result_data.get('method', 'GET')}",
                "pass_": result_data.get("passed", False),
                "status": result_data.get("actual_status", None),
                "duration": result_data.get("duration", 0),
                "error": result_data.get("error"),
                "url": result_data.get("endpoint"),
                "timestamp": result_data.get("timestamp", datetime.now().isoformat()),
                "method": result_data.get("method", "GET"),
                "description": result_data.get("description", "")
            }
            storage.save_result(suite_id, test_result)
        
        return {
            "status": "ok",
            "saved": len(results),
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save automation results: {str(e)}")

# ============================================================================
# BATCH API TESTING ENDPOINTS (from Excel)
# ============================================================================

from fastapi import UploadFile, File
from excel_api_loader import ExcelAPILoader, ExcelAPIConfig
import tempfile

@app.post("/api/batch/parse-excel")
async def parse_excel(file: UploadFile = File(...)):
    """
    Parse Excel file and return list of APIs to test.
    Excel should have columns: API Name, Method, Endpoint, Description, Headers, Params, Body, Expected Status, Auth Type, Auth Token
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Load APIs from Excel
            apis = ExcelAPILoader.load_from_excel(tmp_path)
            
            return {
                "status": "ok",
                "count": len(apis),
                "apis": [api.dict() for api in apis]
            }
        finally:
            # Clean up temp file
            import os
            try:
                os.remove(tmp_path)
            except:
                pass
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel: {str(e)}")

@app.post("/api/batch/run-tests")
async def run_batch_api_tests(request_body: dict):
    """
    Run batch API tests from Excel data.
    
    Request body:
    {
        "base_url": "http://localhost:3000",
        "apis": [ExcelAPIConfig dicts],
        "timeout": 10000
    }
    """
    try:
        base_url = request_body.get("base_url", "").strip()
        apis_data = request_body.get("apis", [])
        timeout = request_body.get("timeout", 10000)
        
        if not base_url:
            raise HTTPException(status_code=400, detail="base_url is required")
        if not apis_data:
            raise HTTPException(status_code=400, detail="No APIs provided")
        
        # Convert to ExcelAPIConfig objects
        apis = [ExcelAPIConfig(**api) for api in apis_data]
        
        # Run tests and broadcast results
        results = []
        start_time = asyncio.get_event_loop().time()
        
        await manager.broadcast({
            "type": "BATCH_API_TEST",
            "payload": {
                "action": "test_start",
                "total": len(apis)
            }
        })
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            for idx, api in enumerate(apis):
                try:
                    # Build URL
                    url = base_url.rstrip('/') + api.endpoint
                    
                    # Build headers
                    headers = api.headers or {}
                    headers['Content-Type'] = headers.get('Content-Type', 'application/json')
                    
                    # Add auth if needed
                    if api.auth_type == "bearer" and api.auth_token:
                        headers['Authorization'] = f"Bearer {api.auth_token}"
                    elif api.auth_type == "basic" and api.auth_token:
                        headers['Authorization'] = f"Basic {api.auth_token}"
                    
                    # Make request
                    async with session.request(
                        method=api.method,
                        url=url,
                        params=api.params or {},
                        json=api.body if api.body else None,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout/1000)
                    ) as resp:
                        response_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
                        status = resp.status
                        passed = status in api.expected_status
                        
                        try:
                            response_body = await resp.json()
                        except:
                            response_body = await resp.text()
                        
                        result = {
                            "api_name": api.api_name,
                            "method": api.method,
                            "endpoint": api.endpoint,
                            "url": url,
                            "status": status,
                            "expected": api.expected_status,
                            "passed": passed,
                            "response": response_body if isinstance(response_body, dict) else None,
                            "response_text": response_body if isinstance(response_body, str) else None,
                            "duration": response_time,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        results.append(result)
                        
                        # Broadcast progress
                        await manager.broadcast({
                            "type": "BATCH_API_TEST",
                            "payload": {
                                "action": "test_progress",
                                "index": idx + 1,
                                "total": len(apis),
                                "result": result
                            }
                        })
                
                except asyncio.TimeoutError:
                    result = {
                        "api_name": api.api_name,
                        "method": api.method,
                        "endpoint": api.endpoint,
                        "url": base_url.rstrip('/') + api.endpoint,
                        "status": None,
                        "expected": api.expected_status,
                        "passed": False,
                        "error": "Request timeout",
                        "duration": timeout,
                        "timestamp": datetime.now().isoformat()
                    }
                    results.append(result)
                    
                    await manager.broadcast({
                        "type": "BATCH_API_TEST",
                        "payload": {
                            "action": "test_progress",
                            "index": idx + 1,
                            "total": len(apis),
                            "result": result
                        }
                    })
                
                except Exception as e:
                    result = {
                        "api_name": api.api_name,
                        "method": api.method,
                        "endpoint": api.endpoint,
                        "url": base_url.rstrip('/') + api.endpoint,
                        "status": None,
                        "expected": api.expected_status,
                        "passed": False,
                        "error": str(e),
                        "duration": int((asyncio.get_event_loop().time() - start_time) * 1000),
                        "timestamp": datetime.now().isoformat()
                    }
                    results.append(result)
                    
                    await manager.broadcast({
                        "type": "BATCH_API_TEST",
                        "payload": {
                            "action": "test_progress",
                            "index": idx + 1,
                            "total": len(apis),
                            "result": result
                        }
                    })
        
        # Calculate summary
        total_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        passed = len([r for r in results if r["passed"]])
        failed = len([r for r in results if not r["passed"]])
        
        summary = {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "duration": total_time
        }
        
        await manager.broadcast({
            "type": "BATCH_API_TEST",
            "payload": {
                "action": "test_complete",
                "summary": summary
            }
        })
        
        return {
            "status": "ok",
            "results": results,
            "summary": summary
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch test failed: {str(e)}")

@app.get("/api/batch/sample-excel")
async def download_sample_excel():
    """Download sample Excel template for batch API testing"""
    try:
        import tempfile
        from fastapi.responses import FileResponse
        import time
        
        # Create unique filename with timestamp
        timestamp = int(time.time())
        tmp_dir = tempfile.gettempdir()
        sample_path = os.path.join(tmp_dir, f"api_batch_template_{timestamp}.xlsx")
        
        # Create the Excel file
        ExcelAPILoader.create_sample_excel(sample_path)
        
        # Verify file exists and has content
        if not os.path.exists(sample_path):
            raise Exception(f"File not created at {sample_path}")
        
        file_size = os.path.getsize(sample_path)
        if file_size == 0:
            raise Exception("Created file is empty")
        
        print(f"Sample Excel created: {sample_path} ({file_size} bytes)")
        
        # Return file with proper headers
        return FileResponse(
            path=sample_path,
            filename="api_batch_template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=api_batch_template.xlsx"
            }
        )
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"Download error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to create sample: {str(e)}")


# ============================================================================
# LOAD TESTING & PERFORMANCE MONITORING ENDPOINTS
# ============================================================================

class LoadTestConfig(BaseModel):
    test_name: str
    bearer_token: str
    headers: Optional[Dict[str, str]] = None
    requests: List[Dict] = []
    options: Optional[Dict] = None

class PerformanceRequest(BaseModel):
    endpoint: str
    duration_ms: int
    status_code: int
    success: bool = True

# Global instances
load_test_runner = K6LoadTestRunner()
performance_collector = PerformanceDataCollector()


@app.post("/api/load-test/start")
async def start_load_test(config: LoadTestConfig, background_tasks: BackgroundTasks):
    """
    Start a load test with k6
    Returns: test_id for tracking
    """
    try:
        test_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prepare test configuration
        test_config = {
            'bearer_token': config.bearer_token,
            'headers': config.headers or {},
            'requests': config.requests,
            'options': config.options or {
                'scenarios': {
                    'default': {
                        'executor': 'ramping-vus',
                        'stages': [
                            {'target': 5, 'duration': '10s'},
                            {'target': 5, 'duration': '30s'},
                            {'target': 0, 'duration': '10s'}
                        ]
                    }
                }
            }
        }
        
        # Reset performance collector
        performance_collector.clear()
        
        # Broadcast test started
        await manager.broadcast({
            'type': 'LOAD_TEST_STARTED',
            'test_id': test_id,
            'test_name': config.test_name,
            'timestamp': datetime.now().isoformat()
        })
        
        # Run test in background
        background_tasks.add_task(
            _run_load_test_background,
            test_id,
            test_config
        )
        
        return {
            'success': True,
            'test_id': test_id,
            'test_name': config.test_name
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _run_load_test_background(test_id: str, test_config: Dict):
    """Background task to run the load test"""
    try:
        result = await load_test_runner.run_test(test_config, test_id)
        
        # Broadcast test completed
        await manager.broadcast({
            'type': 'LOAD_TEST_COMPLETED',
            'test_id': test_id,
            'success': result['success'],
            'summary': performance_collector.get_summary(),
            'timestamp': datetime.now().isoformat()
        })
        
        # Save results
        export_file = f"backend/api_matrix_data/load_test_results/{test_id}_analysis.json"
        performance_collector.export_json(export_file)
        
    except Exception as e:
        print(f"Error running load test: {e}")
        await manager.broadcast({
            'type': 'LOAD_TEST_ERROR',
            'test_id': test_id,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })


@app.post("/api/load-test/metrics")
async def record_metric(metric: PerformanceRequest):
    """
    Record a performance metric during test execution
    """
    try:
        performance_collector.record_request(
            endpoint=metric.endpoint,
            duration_ms=metric.duration_ms,
            status_code=metric.status_code,
            success=metric.success
        )
        
        # Broadcast metric update
        await manager.broadcast({
            'type': 'METRIC_RECORDED',
            'metric': metric.dict()
        })
        
        return {'success': True}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/load-test/{test_id}/summary")
async def get_test_summary(test_id: str):
    """Get test summary and analytics"""
    try:
        summary = performance_collector.get_summary()
        
        return {
            'test_id': test_id,
            'summary': summary,
            'timeline': performance_collector.get_timeline_data(),
            'heatmap': performance_collector.get_heatmap_data(),
            'throughput': performance_collector.get_throughput_over_time(),
            'distribution': performance_collector.get_response_time_distribution()
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/load-test/{test_id}/details")
async def get_test_details(test_id: str):
    """Get detailed test results"""
    try:
        results = load_test_runner.get_test_results(test_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="Test not found")
        
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/load-test/list")
async def list_load_tests():
    """List all completed load tests"""
    try:
        tests = load_test_runner.list_tests()
        return {
            'success': True,
            'tests': tests,
            'total': len(tests)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.websocket("/ws/load-test/{test_id}")
async def websocket_load_test(websocket: WebSocket, test_id: str):
    """
    WebSocket endpoint for real-time load test metrics
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and receive any messages
            data = await websocket.receive_text()
            
            # Echo back or process commands if needed
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)