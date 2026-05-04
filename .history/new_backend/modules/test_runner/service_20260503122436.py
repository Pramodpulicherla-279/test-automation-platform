    import os
    import sys
    import pytest
    import asyncio
    import subprocess
    import json
    import socket
    import threading
    from fastapi.responses import JSONResponse
    from typing import Dict, List
    from new_backend.modules.appium_grid.appium_state import get_servers
    from new_backend.core.state import (
        test_steps_store,
        current_test_name,
        pending_payloads,
        dismissed_keys,
        PAYLOAD_PREFIXES,
        reset_run_state,
        runs
    )
    from new_backend.core.utils import pick_free_port, parse_step_from_message
    from new_backend.core.constants import ALLURE_CMD, ALLURE_REPORT_DIR
    from fastapi import HTTPException
    from new_backend.core.websocket import manager
    from new_backend.core.logger import logger
    from new_backend.core.events import broadcast_async
    from new_backend.modules.slack.service import APP_DEVELOPER_MAP, new_run, detect_app_variant, run_post_notify
    from new_backend.core.constants import SLACK_NOTIFY_CHANNEL

    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    sys.path.insert(0, PROJECT_ROOT)

    from tests.test_runner import (
        stop_current_tests,
        generate_report
    )

    # FIX: replaced `from manager import appium_servers` (stale list binding) with
    # get_servers() which reads the shared JSON file written by appium_state.set_servers().
    # This ensures both this module AND the pytest subprocess always see the live state.

    from new_backend.modules.slack.config import APP_VARIANTS, APP_DEVELOPER_MAP
    from .gdrive_loader import download_apk, extract_app_icon, get_apk_info


    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    BAS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    APKS_DIR = os.path.join(BASE_DIR, "backend", "temp_apks")
    os.makedirs(APKS_DIR, exist_ok=True)

    DOWNLOAD_PROCESS_OBJ = None
    latest_run_id = None


    # ════════════════════════════════════════════════════════════════════════════
    #  Log Step
    # ════════════════════════════════════════════════════════════════════════════

    async def log_step_flow(msg):
        global test_steps_store, current_test_name

        message = msg.message

        # ── Test context switch ──────────────────────────────────────────────
        if "[TEST_START:" in message:
            try:
                new_test = message.split("[TEST_START:")[1].split("]")[0].strip()
                if new_test and new_test != current_test_name:
                    current_test_name = new_test
                    test_steps_store.setdefault(current_test_name, [])
                    print(f"🔄 Test context switched → {current_test_name}")
            except Exception as e:
                print(f"❌ TEST_START parse warning: {e}")

        # ── Step capture (all patterns) ──────────────────────────────────────
        try:
            bucket = (
                message.split("[TEST:")[1].split("]")[0].strip()
                if "[TEST:" in message else current_test_name
            )
            step = parse_step_from_message(message)
            if step:
                test_steps_store.setdefault(bucket, [])
                if step not in test_steps_store[bucket]:
                    test_steps_store[bucket].append(step)
                    print(f"✅ Step captured → {bucket}: {step}")
        except Exception as e:
            print(f"❌ Step capture warning: {e}")

        # ── Payload prefix handling ──────────────────────────────────────────
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


    # ════════════════════════════════════════════════════════════════════════════
    #  Run Tests
    #  FIX: Removed duplicate definition — only one run_tests_flow kept.
    #       Replaced stale `appium_servers` import with get_servers() live call.
    # ════════════════════════════════════════════════════════════════════════════

    async def run_tests_flow():
        current_servers = get_servers()

        if not current_servers:
            return {"error": "Start Appium first"}

        workers = max(1, len(current_servers))
        print(f"[TestRunner] Running with {workers} workers")

        args = [
            "-n", str(workers),
            "--alluredir=allure-results"
        ]

        result = pytest.main(args)

        return {"status": "completed", "exit_code": result}
    # ════════════════════════════════════════════════════════════════════════════
    #  Device Status
    # ════════════════════════════════════════════════════════════════════════════

    async def device_status_flow():
        servers = get_servers()

        return {
            "connected": len(servers) > 0,
            "devices": servers,
            "count": len(servers)
        }
        
    # ✅ ADD THIS FUNCTION (PLACE AFTER device_status_flow)

    async def validate_appium_ready():
        servers = get_servers()

        if not servers:
            return False, "❌ Appium NOT started", []

        active_servers = [s for s in servers if s.get("device") and s.get("port")]

        if not active_servers:
            return False, "❌ No active Appium devices found", []

        return True, f"✅ {len(active_servers)} device(s) connected", active_servers   


    # ════════════════════════════════════════════════════════════════════════════
    #  APK Download (subprocess streaming)
    # ════════════════════════════════════════════════════════════════════════════

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
        


    # ════════════════════════════════════════════════════════════════════════════
    #  APK List
    # ════════════════════════════════════════════════════════════════════════════

    async def list_apks_flow():
        try:
            files = [name for name in os.listdir(APKS_DIR) if name.lower().endswith((".apk", ".apks"))]
            print(f"📦 Found {len(files)} APK(s) in {APKS_DIR}")
            return {"apks": files}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    # ════════════════════════════════════════════════════════════════════════════
    #  Module Status
    # ════════════════════════════════════════════════════════════════════════════

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


    # ════════════════════════════════════════════════════════════════════════════
    #  Start Test (GDrive URL)
    #  FIX: Removed duplicate broadcast("Starting APK download...") call.
    # ════════════════════════════════════════════════════════════════════════════

    async def start_test_flow(request, background_tasks, manager):
        reset_run_state()
        global DOWNLOAD_PROCESS_OBJ, latest_run_id

        run_id        = new_run()
        latest_run_id = run_id

        try:
            # FIX: single broadcast, no duplicate
            await manager.broadcast({
                "type": "LOG",
                "payload": {"message": "Starting APK download...", "status": "INFO"}
            })

            script_path = os.path.join(os.path.dirname(__file__), "gdrive_loader.py")
            apk_path = None
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            DOWNLOAD_PROCESS_OBJ = await asyncio.create_subprocess_exec(
                sys.executable, "-u", script_path, request.url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            async for line in DOWNLOAD_PROCESS_OBJ.stdout:
                decoded_line = line.decode("utf-8").strip()
                if decoded_line.startswith("PROGRESS:"):
                    await manager.broadcast({"type": "LOG", "payload": {
                        "message": decoded_line.replace("PROGRESS:", ""), "status": "PROGRESS"
                    }})
                elif decoded_line.startswith("RESULT:"):
                    apk_path = decoded_line.replace("RESULT:", "").strip()
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
            app_name     = info.get("app_name")
            app_version  = info.get("app_version")
            package_name = info.get("package_name")
            app_variant  = detect_app_variant(package_name, app_name)
            tests_to_run = request.tests_to_run or APP_VARIANTS.get(app_variant, [])

            # ── Store into run state immediately so conftest can fetch it ─────────
            developer_name = APP_DEVELOPER_MAP.get(app_variant, "Unknown Developer")
            if run_id in runs:
                runs[run_id]["app_name"]       = app_name       or ""
                runs[run_id]["app_version"]    = app_version     or ""
                runs[run_id]["package_name"]   = package_name   or ""
                runs[run_id]["app_variant"]    = app_variant     or ""
                runs[run_id]["developer_name"] = developer_name or ""

            await manager.broadcast({
                "type": "LOG",
                "payload": {"message": f"Detected app variant: {app_variant}", "status": "INFO"},
            })

            background_tasks.add_task(
                run_post_notify,
                run_id=run_id,
                apk_path=apk_path,
                tests_to_run   = tests_to_run,
                app_name       = app_name,
                app_version    = app_version,
                developer_name = developer_name,
                channel_id     = SLACK_NOTIFY_CHANNEL,
            )

            return {
                "status":       "success",
                "message":      "APK Downloaded. Test Starting...",
                "run_id":       run_id,
                "app_icon":     full_icon_url,
                "apk_path":     apk_path,
                "app_name":     app_name,
                "package_name": package_name,
                "app_version":  app_version,
                "app_variant":  app_variant,
                **{k: v for k, v in info.items() if k not in
                ("app_name", "app_version", "package_name")},
            }

        except Exception as e:
            DOWNLOAD_PROCESS_OBJ = None
            await manager.broadcast({"type": "LOG", "payload": {
                "message": f"Download interrupted: {str(e)}", "status": "FAILED",
            }})
            raise HTTPException(status_code=400, detail=f"Download Failed: {str(e)}")


    # ════════════════════════════════════════════════════════════════════════════
    #  Start Test (Existing APK)
    #  FIX: Pass validated `tests_to_run` (not raw `request.tests_to_run`) to
    #       run_post_notify so invalid paths don't sneak into the task.
    # ════════════════════════════════════════════════════════════════════════════

    async def start_test_existing_flow(request, background_tasks, manager):
        global latest_run_id

        run_id        = new_run()
        latest_run_id = run_id

        reset_run_state()

        try:
            apk_path = os.path.join(APKS_DIR, request.apk_name)

            if not os.path.isfile(apk_path):
                raise HTTPException(status_code=404, detail="APK not found on server")

            # ============================================================
            # ✅ API DEBUG LOGS (CORRECT POSITION)
            # ============================================================
            print("🔥 API HIT → /test/start-test-existing")
            print(f"📦 APK: {request.apk_name}")
            print(f"🧪 Tests: {request.tests_to_run}")

            print("🚀 start_test_existing_flow STARTED")

            # ============================================================
            # ✅ APPIUM VALIDATION
            # ============================================================
            is_ready, msg, servers = await validate_appium_ready()

            await manager.broadcast({
                "type": "LOG",
                "payload": {
                    "message": msg,
                    "status": "INFO" if is_ready else "FAILED"
                }
            })

            if not is_ready:
                raise HTTPException(status_code=400, detail=msg)

            # ============================================================
            # ✅ SHOW DEVICES (FRONTEND + BACKEND)
            # ============================================================
            for s in servers:
                print(f"📱 Device → {s['device']} | Port → {s['port']}")

                await manager.broadcast({
                    "type": "LOG",
                    "payload": {
                        "message": f"📱 Device {s['device']} → Port {s['port']}",
                        "status": "INFO"
                    }
                })

            # ============================================================
            # 🚀 START TEST FLOW
            # ============================================================
            await manager.broadcast({"type": "RUN_START", "payload": {}})

            await manager.broadcast({
                "type": "LOG",
                "payload": {
                    "message": f"Using existing APK: {request.apk_name}",
                    "status": "INFO"
                }
            })

            icon_url      = extract_app_icon(apk_path)
            full_icon_url = f"http://localhost:8000{icon_url}" if icon_url else None

            info          = get_apk_info(apk_path) or {}
            package_name  = info.get("package_name", "")
            app_name      = info.get("app_name", "")
            app_version   = info.get("app_version", "")

            app_variant   = detect_app_variant(package_name, app_name)
            variant_tests = APP_VARIANTS.get(app_variant, [])
            tests_to_run  = request.tests_to_run

            # ============================================================
            # ✅ VALIDATE TEST FILES
            # ============================================================
            from pathlib import Path

            if tests_to_run:
                valid = []
                invalid = []
            
                BASE_PATH = Path(PROJECT_ROOT).resolve()
            
                print("\n🔍 BACKEND PATH DEBUG")
                print(f"PROJECT ROOT (BASE_DIR): {BASE_PATH}")
                print(f"CWD: {os.getcwd()}")
                print(f"APKs DIR: {APKS_DIR}\n")
            
                for t in tests_to_run:
                    raw_path = t.get("path")
            
                    if not raw_path:
                        invalid.append(t)
                        continue
            
                    # 🔥 FIX: resolve absolute path
                    full_path = (BASE_PATH / raw_path).resolve()
            
                    print(f"Checking:")
                    print(f"  Input: {raw_path}")
                    print(f"  Full : {full_path}")
                    print(f"  Exists: {full_path.exists()}\n")
            
                    if full_path.exists():
                        # ✅ IMPORTANT: send FULL PATH forward
                        valid.append({
                            "name": t.get("name"),
                            "path": str(full_path)
                        })
                    else:
                        invalid.append(t)
            
                if invalid:
                    bad_paths = [t["path"] for t in invalid]
            
                    await manager.broadcast({
                        "type": "LOG",
                        "payload": {
                            "message": f"⚠️ Invalid paths removed: {bad_paths}",
                            "status": "WARN",
                        }
                    })
            
                if not valid:
                    raise HTTPException(
                        status_code=400,
                        detail=f"❌ No valid test files found. Invalid paths: {[t['path'] for t in tests_to_run]}"
                    )
            
                tests_to_run = valid
            else:
                tests_to_run = variant_tests

            if not tests_to_run:
                raise HTTPException(
                    status_code=400,
                    detail=f"No valid test scripts found for variant '{app_variant}'"
                )

            await manager.broadcast({
                "type": "LOG",
                "payload": {
                    "message": f"Running {len(tests_to_run)} test(s): {[t['name'] for t in tests_to_run]}",
                    "status": "INFO",
                }
            })

            developer_name = APP_DEVELOPER_MAP.get(app_variant, "Unknown Developer")

            background_tasks.add_task(
                run_post_notify,
                run_id=run_id,
                apk_path=apk_path,
                tests_to_run=tests_to_run,
                app_name=app_name,
                app_version=app_version,
                developer_name=developer_name,
                channel_id=SLACK_NOTIFY_CHANNEL,
            )

            return {
                "status": "success",
                "message": "Using existing APK. Test Starting...",
                "run_id": run_id,
                "app_icon": full_icon_url,
                "apk_path": apk_path,
                "app_variant": app_variant,
                "tests_to_run": tests_to_run,
                **info,
            }

        except HTTPException:
            raise

        except Exception as e:
            print(f"❌ ERROR in start_test_existing_flow: {e}")

            await manager.broadcast({
                "type": "LOG",
                "payload": {
                    "message": f"Failed to start test: {str(e)}",
                    "status": "FAILED"
                }
            })

            raise HTTPException(status_code=400, detail=f"Failed: {str(e)}")


    # ════════════════════════════════════════════════════════════════════════════
    #  Stop / Allure / Complete / Generate Report
    # ════════════════════════════════════════════════════════════════════════════

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
        subprocess.Popen(
            [ALLURE_CMD, "open", "-h", "127.0.0.1", "-p", str(port), ALLURE_REPORT_DIR],
            cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True
        )
        return JSONResponse({"url": f"http://127.0.0.1:{port}"})


    async def run_complete_flow(event):
        await manager.broadcast({"type": "RUN_COMPLETE", "payload": {"report_url": event.report_url}})
        return {"ok": True}


    async def api_generate_report_flow():
        try:
            threading.Thread(target=generate_report).start()
            return {"status": "ok", "message": "Report generation started"}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})