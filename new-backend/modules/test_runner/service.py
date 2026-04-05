import os
import sys
import asyncio
import subprocess
import json
import socket
from fastapi.responses import JSONResponse
from typing import Dict, List
from core.state import reset_run_state
from core.state import _appium_proc, APPIUM_PORT
from core.utils import pick_free_port
from core.constants import ALLURE_CMD, ALLURE_REPORT_DIR, PAYLOAD_PREFIXES
from fastapi import HTTPException
from core.websocket import manager
from core.logger import logger
from core.events import broadcast_async
from modules.test_runner.test_runner import (
    run_tests_and_get_suggestions,
    stop_current_tests,
    generate_report
)

from .gdrive_loader import download_apk, extract_app_icon, get_apk_info


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APKS_DIR = os.path.join(BASE_DIR, "backend", "temp_apks")
os.makedirs(APKS_DIR, exist_ok=True)

DOWNLOAD_PROCESS_OBJ = None

# SAME AS YOUR SERVER (no change)
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
}

async def log_step_flow(msg):
    global _test_steps_store, _current_test_name

    # logger.info("[PYTEST][%s] %s", msg.status, msg.message)
    message = msg.message

    # Switch active bucket when conftest sends [TEST_START:xxx]
    if "[TEST_START:" in message:
        try:
            new_test = message.split("[TEST_START:")[1].split("]")[0].strip()
            if new_test and new_test != _current_test_name:
                _current_test_name = new_test
                _test_steps_store.setdefault(_current_test_name, [])
                print(f"🔄 Test context switched → {_current_test_name}")
        except Exception as e:
            print(f"❌ TEST_START parse warning: {e}")

    # Capture [FOUND] steps into the correct bucket
    try:
        bucket = (
            message.split("[TEST:")[1].split("]")[0].strip()
            if "[TEST:" in message else _current_test_name
        )
        if "[FOUND]" in message:
            import re
            match = re.search(r"name='([^']+)'|name=\"([^\"]+)\"", message)
            step = (match.group(1) or match.group(2)) if match else None
            if step:
                _test_steps_store.setdefault(bucket, []).append(step)
                print(f"✅ Step captured → {bucket}: {step}")
    except Exception as e:
        print(f"❌ Step capture warning: {e}")

    # Intercept payload log lines
    for prefix in PAYLOAD_PREFIXES:
        if message.startswith(prefix):
            raw = message[len(prefix):].strip()
            try:
                payload = json.loads(raw)
                steps = payload.get('steps_executed') or []
                clean_line = (f"[PAYLOAD] {payload.get('issue_id','')} | "
                              f"{payload.get('module','?')} | {payload.get('test_name','?')} | "
                              f"Steps ({len(steps)}): {', '.join(steps[:3]) if steps else 'none'}")
                broadcast_async({"type": "LOG", "payload": {"message": clean_line, "status": "PAYLOAD"}})
            except Exception as exc:
                logger.warning("Failed to parse payload: %s", exc)
            return {"status": "ok"}


    broadcast_async({"type": "LOG", "payload": {"message": message, "status": msg.status}})
    return {"status": "ok"}


async def device_status_flow():
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().splitlines()[1:]
        return {"connected": any("\tdevice" in line for line in lines)}
    except Exception:
        return {"connected": False}
    
async def appium_start_flow():
    global _appium_proc
    if _appium_proc is not None and _appium_proc.poll() is None:
        return {"status": "running", "message": "Appium is already running via backend."}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", APPIUM_PORT)) == 0:
            return {"status": "running", "message": f"Appium already active on port {APPIUM_PORT}"}
    try:
        _appium_proc = subprocess.Popen(["appium", "-p", str(APPIUM_PORT)],
                                         shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "started", "message": f"Appium started on port {APPIUM_PORT}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
async def download_apk_from_url(url: str, manager):
    global DOWNLOAD_PROCESS_OBJ

    script_path = os.path.join(os.path.dirname(__file__), "gdrive_loader.py")

    apk_path = None
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    DOWNLOAD_PROCESS_OBJ = await asyncio.create_subprocess_exec(
        sys.executable,
        "-u",
        script_path,
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    async for line in DOWNLOAD_PROCESS_OBJ.stdout:
        decoded = line.decode("utf-8").strip()

        if decoded.startswith("PROGRESS:"):
            await manager.broadcast({
                "type": "LOG",
                "payload": {"message": decoded.replace("PROGRESS:", ""), "status": "PROGRESS"}
            })
        elif decoded.startswith("RESULT:"):
            apk_path = decoded.replace("RESULT:", "").strip()
        elif decoded:
            await manager.broadcast({
                "type": "LOG",
                "payload": {"message": decoded, "status": "INFO"}
            })

    await DOWNLOAD_PROCESS_OBJ.wait()

    if DOWNLOAD_PROCESS_OBJ.returncode != 0:
        stderr_data = await DOWNLOAD_PROCESS_OBJ.stderr.read()
        raise Exception(stderr_data.decode())

    if not apk_path:
        raise Exception("APK path not returned")

    return apk_path

async def appium_status_flow():
    global _appium_proc
    if _appium_proc is not None and _appium_proc.poll() is None:
        return {"status": "running", "port": APPIUM_PORT}
    return {"status": "stopped"}

async def appium_stop_flow():
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

async def list_apks_flow():
    try:
        files = [name for name in os.listdir(APKS_DIR) if name.lower().endswith((".apk", ".apks"))]
        return {"apks": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def module_status_flow(data: dict):
    module = data.get("module")
    status = data.get("status")

    # Special signal: new run starting — broadcast RUN_START so frontend clears
    if module == "__RUN_START__":
        broadcast_async({"type": "RUN_START", "payload": {}})
    else:
    
        broadcast_async({"type": "MODULE", "payload": {
            "module": module, "status": status, "message": data.get("message", "")
        }})
    return {"status": "ok"}

async def start_test_flow(request, background_tasks, manager):
    reset_run_state()
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
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env)
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

        # background_tasks.add_task(run_tests_and_get_suggestions, apk_path, tests_to_run=tests_to_run)

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
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Download interrupted: {str(e)}", "status": "FAILED"},})
        raise HTTPException(status_code=400, detail=f"Download Failed: {str(e)}")

async def start_test_existing_flow(request, background_tasks, manager):
    reset_run_state()
    try:
        apk_path = os.path.join(APKS_DIR, request.apk_name)
        if not os.path.isfile(apk_path):
            raise HTTPException(status_code=404, detail="APK not found on server")
        await manager.broadcast({"type": "RUN_START", "payload": {}})
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Using existing APK: {request.apk_name}", "status": "INFO"}})
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
        await manager.broadcast({"type": "LOG", "payload": {"message": f"Failed to start test: {str(e)}", "status": "FAILED"},})
        raise HTTPException(status_code=400, detail=f"Failed: {str(e)}")

def stop_test_flow(manager):
    stopped = False

    global DOWNLOAD_PROCESS_OBJ

    if DOWNLOAD_PROCESS_OBJ:
        DOWNLOAD_PROCESS_OBJ.terminate()
        stopped = True

    if stop_current_tests():
        stopped = True

    return stopped

async def allure_start_flow():
    port = pick_free_port()
    subprocess.Popen([ALLURE_CMD, "open", "-h", "127.0.0.1", "-p", str(port), ALLURE_REPORT_DIR],
                     cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    return JSONResponse({"url": f"http://127.0.0.1:{port}"})

async def run_complete_flow(event):
    await manager.broadcast({"type": "RUN_COMPLETE", "payload": {"report_url": event.report_url}})
    return {"ok": True}

async def api_generate_report_flow():
    try:
        import threading
        threading.Thread(target=generate_report).start()
        return {"status": "ok", "message": "Report generation started"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

