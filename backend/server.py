# server.py
import os
import sys
sys.dont_write_bytecode = True
import json
import datetime
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
import logging
from gdrive_loader import download_apk, extract_app_icon, get_apk_info
from typing import List, Optional, Dict, Any
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger("uvicorn.error")
from starlette.websockets import WebSocketDisconnect


# Add project root to sys.path so we can import tests.*
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # root: f:\projects\test-automation-platform
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tests.test_runner import run_tests_and_get_suggestions, stop_current_tests, generate_report

# ─── In-memory stores (new) ───────────────────────────────────────────────────
_jira_history:     list[dict] = []   # tickets created via Create button
_pending_payloads: list[dict] = []   # all payloads received this session
_dismissed_keys:   set[str]   = set()  # test_name keys dismissed (removed or created)

# ─── Payload prefixes to intercept from log lines ────────────────────────────
_PAYLOAD_PREFIXES = ("AUTOMATION_PAYLOAD_JSON:", "JIRA_PAYLOAD_JSON:")


# ─── Lifespan ─────────────────────────────────────────────────────────────────
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

# Use absolute path and auto-create the dir
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
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    return f"http://127.0.0.1:{_allure_port}"


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

# NEW: payload from conftest HTTP POST
class JiraPayloadRequest(BaseModel):
    ticket_id:      Optional[str]       = None
    issue_id:       Optional[str]       = None
    app_name:       Optional[str]       = None
    app_version:    Optional[str]       = None
    module:         Optional[str]       = None
    feature:        Optional[str]       = None
    issue_summary:  Optional[str]       = None
    title:          Optional[str]       = None
    test_name:      Optional[str]       = None
    test_id:        Optional[str]       = None
    steps_executed: Optional[List[Any]] = None
    developer_name: Optional[str]       = None
    description:    Optional[str]       = None

# NEW: create request from IssuePanel "Create" button
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


# ─── WebSocket Connection Manager (unchanged) ─────────────────────────────────
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


@app.post("/api/run-complete")
async def run_complete(event: RunCompleteEvent):
    await manager.broadcast({"type": "RUN_COMPLETE", "payload": {"report_url": event.report_url}})
    return {"ok": True}

# ─── Jira connection test ─────────────────────────────────────────────────────
@app.get("/api/jira/test-connection")
async def jira_test_connection():
    import requests as req_lib
    from jira_integration.jira_config import config as jira_config
    from requests.auth import HTTPBasicAuth

    base = {
        "jira_url":         jira_config.url         or "(not set)",
        "jira_email":       jira_config.email        or "(not set)",
        "jira_project_key": jira_config.project_key  or "(not set)",
        "jira_token_set":   bool(jira_config.api_token),
        "jira_enabled":     jira_config.enabled,
    }

    if not all([jira_config.url, jira_config.email, jira_config.api_token]):
        return {**base, "status": "MISSING_CONFIG",
                "message": "One or more required .env variables not set"}

    try:
        me = req_lib.get(
            f"{jira_config.url}/rest/api/3/myself",
            auth=HTTPBasicAuth(jira_config.email, jira_config.api_token),
            headers={"Accept": "application/json"}, timeout=10,
        )
        if me.status_code == 401:
            return {**base, "status": "AUTH_FAILED",
                    "message": (
                        "401 Unauthorized - JIRA_EMAIL or JIRA_API_TOKEN is wrong. "
                        "Generate a new token at: https://id.atlassian.com/manage-profile/security/api-tokens "
                        f"| Current email: {jira_config.email}"
                    )}
        if me.status_code != 200:
            return {**base, "status": f"AUTH_ERROR_{me.status_code}", "message": me.text[:200]}

        user = me.json()
        base["jira_account"] = user.get("displayName")
        base["jira_account_id"] = user.get("accountId")
    except Exception as e:
        return {**base, "status": "CONNECTION_ERROR", "message": str(e)}

    try:
        proj = req_lib.get(
            f"{jira_config.url}/rest/api/3/project/{jira_config.project_key}",
            auth=HTTPBasicAuth(jira_config.email, jira_config.api_token),
            headers={"Accept": "application/json"}, timeout=10,
        )
        if proj.status_code == 404:
            return {**base, "status": "PROJECT_NOT_FOUND",
                    "message": f"Project '{jira_config.project_key}' not found - check JIRA_PROJECT_KEY in .env"}
        if proj.status_code == 403:
            return {**base, "status": "PROJECT_NO_PERMISSION",
                    "message": f"No access to project '{jira_config.project_key}' - ask your Jira admin to add you"}
        if proj.status_code == 200:
            base["project_name"] = proj.json().get("name")
    except Exception as e:
        base["project_check"] = str(e)

    return {**base, "status": "ALL_OK",
            "message": f"Credentials OK. Connected as '{base.get('jira_account')}'. Project '{jira_config.project_key}' accessible."}



def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@app.post("/api/allure/start")
async def allure_start():
    port = _pick_free_port()
    subprocess.Popen(
        [ALLURE_CMD, "open", "-h", "127.0.0.1", "-p", str(port), ALLURE_REPORT_DIR],
        cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True,
    )
    return JSONResponse({"url": f"http://127.0.0.1:{port}"})


@app.get("/device-status")
async def device_status():
    try:
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=5,
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


# ─── /api/log-step — intercept payload lines arriving via test_runner ─────────
@app.post("/api/log-step")
async def log_step(msg: LogMessage):
    logger.info("[PYTEST][%s] %s", msg.status, msg.message)

    # Intercept AUTOMATION_PAYLOAD_JSON / JIRA_PAYLOAD_JSON lines
    # These arrive because test_runner.send_log() streams every pytest stdout line here
    for prefix in _PAYLOAD_PREFIXES:
        if msg.message.startswith(prefix):
            raw = msg.message[len(prefix):].strip()
            try:
                payload = json.loads(raw)
                # NOTE: do NOT add to _pending_payloads here — /api/jira/payload HTTP POST
                # is the primary path and handles storage + JIRA_PAYLOAD broadcast.
                # log_step just shows a clean readable console line for visibility.
                logger.info("[JIRA_PAYLOAD intercepted] module=%s test=%s",
                            payload.get("module"), payload.get("test_name"))

                # Build clean readable console summary line
                mod    = payload.get('module', '?')
                tname  = payload.get('test_name', '?')
                iid    = payload.get('issue_id', '')
                steps  = payload.get('steps_executed') or []
                desc   = str(payload.get('description') or '')
                err_line = desc.split('\n')[0][:120] if desc else ''
                steps_preview = ", ".join(steps[:3]) + ("…" if len(steps) > 3 else "") if steps else "none"
                clean_line = f"[PAYLOAD] {iid} | {mod} | {tname} | Steps ({len(steps)}): {steps_preview}"
                _broadcast_async({"type": "LOG", "payload": {"message": clean_line, "status": "PAYLOAD"}})
                if err_line:
                    _broadcast_async({"type": "LOG", "payload": {"message": f"  Error: {err_line}", "status": "FAILED"}})
            except Exception as exc:
                logger.warning("Failed to parse payload from log-step: %s", exc)
                # Still show original line if parsing fails
                _broadcast_async({"type": "LOG", "payload": {"message": msg.message, "status": msg.status}})
            return {"status": "ok"}  # do NOT broadcast the raw JSON line

    _broadcast_async({"type": "LOG", "payload": {"message": msg.message, "status": msg.status}})
    return {"status": "ok"}


@app.post("/api/metric")
async def log_metric(data: dict):
    _broadcast_async({"type": "METRIC", "payload": data})
    _broadcast_async({"type": "METRIC", "payload": data})
    return {"status": "ok"}


@app.post("/api/module-status")
async def module_status(data: dict):
    module = data.get("module")
    status = data.get("status")
    module  = data.get("module")
    status  = data.get("status")
    message = data.get("message", "")

    _broadcast_async({
        "type": "MODULE",
        "payload": {"module": module, "status": status, "message": message},
    })
    _broadcast_async({"type": "MODULE", "payload": {"module": module, "status": status, "message": message}})
    return {"status": "ok"}


# ─── NEW: POST /api/jira/payload ──────────────────────────────────────────────
# conftest._post_payload_to_backend() calls this directly via HTTP POST.
# This is the fastest path — bypasses stdout capture entirely.
@app.post("/api/jira/payload")
async def receive_jira_payload(req: JiraPayloadRequest):
    payload = req.model_dump(exclude_none=False)

    # Store for late-joining clients
    _pending_payloads.append(payload)

    # Broadcast to all IssuePanel WebSocket clients
    await manager.broadcast({"type": "JIRA_PAYLOAD", "payload": payload})

    # Console summary is already sent by log_step when it intercepts JIRA_PAYLOAD_JSON:
    # Do NOT duplicate it here. Just log to server.
    logger.info("[/api/jira/payload] %s module=%s test=%s", req.issue_id, req.module, req.test_name)
    return {"status": "received", "issue_id": req.issue_id, "module": req.module}


# ─── NEW: GET /api/jira/payloads ─────────────────────────────────────────────
# IssuePanel fetches this on mount to catch payloads received before WS connected.
@app.get("/api/jira/payloads")
async def get_pending_payloads():
    # Only return payloads that haven't been dismissed (removed or created)
    active = [
        p for p in _pending_payloads
        if _make_dismiss_key(p) not in _dismissed_keys
    ]
    return {"payloads": active}


def _make_dismiss_key(payload: dict) -> str:
    """Stable key for dedup — same logic as IssuePanel dedupKey."""
    test_name = str(payload.get("test_name") or "").strip()
    module    = str(payload.get("module")    or "").strip()
    if test_name:
        return f"tn::{module}::{test_name}"
    title = str(payload.get("issue_summary") or payload.get("title") or "").strip()
    return f"sum::{module}::{title}"


@app.post("/api/jira/dismiss")
async def dismiss_payload(data: dict):
    """
    Called by IssuePanel when user clicks Remove or Create.
    Prevents the payload from reappearing on page refresh.
    """
    key = _make_dismiss_key(data)
    if key:
        _dismissed_keys.add(key)
    return {"status": "dismissed", "key": key}


# ─── NEW: POST /api/jira/create ───────────────────────────────────────────────
# Called by IssuePanel "Create" button.
# ONLY calls create_jira_issue(). Does NOT call build_extended_jira_payload()
# (that does a GET /rest/api/3/issue/{key} which fails with 401 on restricted projects).
@app.post("/api/jira/create")
async def jira_create(req: JiraCreateRequest):
    from jira_integration.jira_service import create_jira_issue
    from jira_integration.jira_config import config as jira_config

    # Validate config before hitting Jira API
    if not jira_config.enabled:
        raise HTTPException(status_code=400,
                            detail="Jira is disabled. Set JIRA_ENABLED=true in backend/.env")

    missing = [n for n, v in {
        "JIRA_URL":         jira_config.url,
        "JIRA_EMAIL":       jira_config.email,
        "JIRA_API_TOKEN":   jira_config.api_token,
        "JIRA_PROJECT_KEY": jira_config.project_key,
    }.items() if not v]

    if missing:
        raise HTTPException(status_code=400,
                            detail=f"Missing .env variables: {', '.join(missing)}. "
                                   f"Edit backend/.env and restart the server.")

    summary     = (req.title or req.issue_summary or "Automation Failure").strip()
    description = (req.description or "Automation Test Failure").strip()

    # Capture stdout from create_jira_issue so AUTOMATION_PAYLOAD_JSON lines
    # are broadcast to the frontend console (jira_service uses print() not send_log)
    import io as _io
    _captured = _io.StringIO()

    try:
        import contextlib as _ctx
        with _ctx.redirect_stdout(_captured):
            issue_key = create_jira_issue(
                summary        = summary,
                description    = description,
                app_name       = req.app_name,
                app_version    = req.app_version,
                module         = req.module or req.parent,
                feature        = req.feature,
                issue_summary  = summary,
                test_name      = req.test_name,
                test_id        = req.test_id,
                steps_executed = req.steps_executed or [],
                developer_name = req.developer_name,
            )
    except Exception as exc:
        err = str(exc)
        logger.error("Jira create exception: %s", err)

        # jira_service now raises RuntimeError("Jira API 401: You do not have permission...")
        # Surface the exact message directly to the frontend
        if "401" in err:
            raise HTTPException(status_code=400,
                                detail=f"Jira 401 Unauthorized — wrong JIRA_EMAIL or JIRA_API_TOKEN.\n"
                                       f"Fix: Open backend/.env, correct JIRA_EMAIL and JIRA_API_TOKEN, restart server.\n"
                                       f"Jira said: {err}")
        if "403" in err or "permission" in err.lower():
            raise HTTPException(status_code=400,
                                detail=f"Jira 403 Forbidden — your account cannot create issues in project '{jira_config.project_key}'.\n"
                                       f"Fix: Ask your Jira admin to grant 'Create Issues' permission, or check JIRA_PROJECT_KEY in .env.\n"
                                       f"Jira said: {err}")
        raise HTTPException(status_code=400, detail=f"Jira error: {err}")

    if not issue_key:
        raise HTTPException(status_code=400,
                            detail="Jira returned no issue key — check JIRA_ENABLED, JIRA_URL, JIRA_EMAIL, "
                                   "JIRA_API_TOKEN and JIRA_PROJECT_KEY in backend/.env")

    # Broadcast captured jira_service print() lines to frontend console
    for _line in _captured.getvalue().splitlines():
        _line = _line.strip()
        if not _line:
            continue
        _status = "PAYLOAD" if any(_line.startswith(p) for p in _PAYLOAD_PREFIXES) else "INFO"
        _broadcast_async({"type": "LOG", "payload": {"message": _line, "status": _status}})
        # If it's AUTOMATION_PAYLOAD_JSON, also parse and store it
        for _pfx in _PAYLOAD_PREFIXES:
            if _line.startswith(_pfx):
                try:
                    _parsed = json.loads(_line[len(_pfx):].strip())
                    # Don't re-add to _pending_payloads (already added via /api/jira/payload)
                    logger.info("[jira_service stdout] %s", _pfx)
                except Exception:
                    pass
                break

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
        "sprint":          req.sprint or "",
        "start_date":      req.start_date or "",
        "end_date":        req.end_date or "",
        "steps_executed":  req.steps_executed or [],
        "status":          "Assigned",
        "created_at":      datetime.datetime.now().isoformat(),
    }

    _jira_history.append(entry)
    _broadcast_async({"type": "JIRA_CREATED", "payload": entry})

    return {"issue_id": issue_key, "issue_key": issue_key, "issue_url": issue_url, **entry}


# ─── NEW: GET /api/jira/history ──────────────────────────────────────────────
_jira_comments: dict = {}   # issue_key -> list of {author, text, created_at}

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
    author = data.get("author") or "QA Automation"
    comment = {
        "author":     author,
        "text":       text,
        "created_at": datetime.datetime.now().isoformat(),
    }
    if issue_key not in _jira_comments:
        _jira_comments[issue_key] = []
    _jira_comments[issue_key].append(comment)
    _broadcast_async({"type": "JIRA_COMMENT", "payload": {"issue_key": issue_key, "comment": comment}})
    return {"status": "ok", "comment": comment}


# Keep the legacy route JiraHistory.jsx uses
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


# ─── NEW: Health check ────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    from jira_integration.jira_config import config as jira_config
    return {
        "status":           "ok",
        "jira_enabled":     jira_config.enabled,
        "jira_url":         jira_config.url         or "(not set — add JIRA_URL to .env)",
        "jira_project_key": jira_config.project_key or "(not set — add JIRA_PROJECT_KEY to .env)",
        "jira_email":       jira_config.email        or "(not set — add JIRA_EMAIL to .env)",
        "jira_token_set":   bool(jira_config.api_token),
        "new_routes": [
            "POST /api/jira/payload  — conftest sends failure payloads here",
            "GET  /api/jira/payloads — IssuePanel fetches on mount",
            "POST /api/jira/create   — IssuePanel 'Create' button",
            "GET  /api/jira/history  — created tickets this session",
            "GET  /api/health        — this endpoint",
        ],
    }


# ─── All original routes below (unchanged) ────────────────────────────────────

@app.post("/start-test")
async def start_test(request: TestRequest, background_tasks: BackgroundTasks):
    global _pending_payloads, _dismissed_keys
    # Clear stale payloads from previous run so IssuePanel starts fresh
    _pending_payloads = []
    _dismissed_keys   = set()

    global DOWNLOAD_PROCESS_OBJ

    try:
        await manager.broadcast({
            "type": "LOG",
            "payload": {"message": "Starting APK download...", "status": "INFO"}
        })
        await manager.broadcast({"type": "LOG", "payload": {"message": "Starting APK download...", "status": "INFO"}})

        script_path = os.path.join(os.path.dirname(__file__), "gdrive_loader.py")
        apk_path = None
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        DOWNLOAD_PROCESS_OBJ = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script_path, request.url,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env,
        )

        async for line in DOWNLOAD_PROCESS_OBJ.stdout:
            decoded_line = line.decode("utf-8").strip()
            if decoded_line.startswith("PROGRESS:"):
                raw_msg = decoded_line.replace("PROGRESS:", "")
                await manager.broadcast({"type": "LOG", "payload": {"message": raw_msg, "status": "PROGRESS"}})
            elif decoded_line.startswith("RESULT:"):
                apk_path = decoded_line.replace("RESULT:", "").strip()
            elif decoded_line:
                await manager.broadcast({"type": "LOG", "payload": {"message": decoded_line, "status": "INFO"}})

        await DOWNLOAD_PROCESS_OBJ.wait()

        if DOWNLOAD_PROCESS_OBJ.returncode != 0:
            stderr_data = await DOWNLOAD_PROCESS_OBJ.stderr.read()
            error_message = stderr_data.decode("utf-8").strip() or "Unknown error (process killed?)"
            raise Exception(f"Script Error: {error_message}")

        if not apk_path:
            raise Exception("Download script finished but returned no path.")

        DOWNLOAD_PROCESS_OBJ = None
        icon_url      = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None
        info = get_apk_info(apk_path) or {}

        background_tasks.add_task(
            run_tests_and_get_suggestions, apk_path,
            tests_to_run   = request.tests_to_run,
            app_name       = info.get("app_name"),
            app_version    = info.get("app_version"),
            developer_name = info.get("developer_name"),
        )

        return {
            "status": "success", "message": "APK Downloaded. Test Starting...",
            "app_icon": full_icon_url, "apk_path": apk_path, **info,
        }

    except Exception as e:
        DOWNLOAD_PROCESS_OBJ = None
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Download interrupted: {str(e)}", "status": "FAILED"}})
        raise HTTPException(status_code=400, detail=f"Download Failed: {str(e)}")


@app.post("/start-test-existing")
async def start_test_existing(request: ExistingTestRequest, background_tasks: BackgroundTasks):
    global _pending_payloads, _dismissed_keys
    # Clear stale payloads from previous run so IssuePanel starts fresh
    _pending_payloads = []
    _dismissed_keys   = set()

    try:
        apk_path = os.path.join(APKS_DIR, request.apk_name)
        if not os.path.isfile(apk_path):
            raise HTTPException(status_code=404, detail="APK not found on server")

        # Signal IssuePanel to clear stale issues from previous run
        await manager.broadcast({"type": "RUN_START", "payload": {}})
        await manager.broadcast(
            {"type": "LOG", "payload": {"message": f"Using existing APK: {request.apk_name}", "status": "INFO"}}
        )

        icon_url      = extract_app_icon(apk_path)
        full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None
        info = get_apk_info(apk_path) or {}

        background_tasks.add_task(
            run_tests_and_get_suggestions, apk_path,
            tests_to_run   = request.tests_to_run,
            app_name       = info.get("app_name"),
            app_version    = info.get("app_version"),
            developer_name = info.get("developer_name"),
        )

        return {
            "status": "success", "message": "Using existing APK. Test Starting...",
            "app_icon": full_icon_url, "apk_path": apk_path, **info,
        }

    except HTTPException:
        raise
    except Exception as e:
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Failed to start test: {str(e)}", "status": "FAILED"}})
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
            print("DEBUG: Terminating download process...")
            DOWNLOAD_PROCESS_OBJ.terminate()
            stopped_something = True
        except Exception as e:
            print(f"Error stopping download: {e}")

    test_stopped = stop_current_tests()
    if test_stopped:
        stopped_something = True

    if stopped_something:
        await manager.broadcast(
            {"type": "LOG", "payload": {"message": "Backend: Process stopped on user request.", "status": "FAILED"}}
        )
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)