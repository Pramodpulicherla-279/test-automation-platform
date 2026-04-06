import os
import sys
sys.dont_write_bytecode = True
import json
import datetime
sys.dont_write_bytecode = True
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
from pathlib import Path
from pathlib import Path
import subprocess
import json
import json
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
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger("uvicorn.error")
from starlette.websockets import WebSocketDisconnect

from starlette.websockets import WebSocketDisconnect

# ─── Global dedup tracker ───────────────────────────────────────────────────
LAST_SLACK_EVENT_TS = None

# ─── Load env ────────────────────────────────────────────────────────────────
load_dotenv()
SLACK_BOT_TOKEN    = os.getenv("SLACK_BOT_TOKEN")
NETLIFY_AUTH_TOKEN = os.getenv("NETLIFY_AUTH_TOKEN")
NETLIFY_SITE_ID    = os.getenv("NETLIFY_SITE_ID")

# ─── Project root ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.abspath(__file__))))
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


# ─── In-memory stores ─────────────────────────────────────────────────────────
_jira_history:      list[dict]           = []
_pending_payloads:  list[dict]           = []
_dismissed_keys:    set[str]             = set()
_test_steps_store:  Dict[str, List[str]] = {}
_current_test_name: str                  = "default"

_PAYLOAD_PREFIXES = ("AUTOMATION_PAYLOAD_JSON:", "JIRA_PAYLOAD_JSON:")


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("Shutting down: Cleaning up child processes...")
    global _appium_proc, _allure_proc

    if _appium_proc is not None:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(_appium_proc.pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                _appium_proc.kill()
                _appium_proc.kill()
        except Exception as e:
            print(f"Error killing Appium: {e}")
    if _allure_proc is not None:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_allure_proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(_allure_proc.pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                _allure_proc.kill()
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
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
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
        cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    return f"http://127.0.0.1:{_allure_port}"

ALLURE_RESULTS_DIR = os.path.join(BASE_DIR, "allure-results")
os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
app.mount("/allure-results", StaticFiles(directory=ALLURE_RESULTS_DIR), name="allure-results")

UI_SCREENSHOTS_BASE = Path(__file__).resolve().parents[1] / "artifacts" / "ui_screenshots"
UI_SCREENSHOTS_BASE.mkdir(parents=True, exist_ok=True)
app.mount("/ui-screenshots", StaticFiles(directory=str(UI_SCREENSHOTS_BASE)), name="ui-screenshots")


# ─── Pydantic models ─────────────────────────────────────────────────────────

class AnalyzeReq(BaseModel):
    run_id: str | None = None

# ─── Models ───────────────────────────────────────────────────────────────────
class RunCompleteEvent(BaseModel):
    report_url: str

class ExistingTestRequest(BaseModel):
    apk_name: str
    tests_to_run: Optional[List[Dict[str, str]]] = None
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


# ─── WebSocket Connection Manager ─────────────────────────────────────────────
DOWNLOAD_PROCESS_OBJ = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()
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
    await manager.broadcast({"type": "RUN_COMPLETE", "payload": {"report_url": event.report_url}})
    return {"ok": True}


@app.get("/api/jira/test-connection")
async def jira_test_connection():
    import requests as req_lib
    from jira_integration.jira_config import config as jira_config
    from requests.auth import HTTPBasicAuth
    base = {
        "jira_url": jira_config.url or "(not set)", "jira_email": jira_config.email or "(not set)",
        "jira_project_key": jira_config.project_key or "(not set)",
        "jira_token_set": bool(jira_config.api_token), "jira_enabled": jira_config.enabled,
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
        base["jira_account"] = user.get("displayName")
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
        lines = result.stdout.strip().splitlines()[1:]
        return {"connected": any("\tdevice" in line for line in lines)}
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
    try:
        asyncio.create_task(manager.broadcast(message))
    except RuntimeError:
        pass


# ─── Step resolution (DESTRUCTIVE — pops bucket) ─────────────────────────────
def _resolve_steps_for_test(test_name: str) -> List[str]:
    """
    Called only by receive_jira_payload. Pops the matched bucket so
    the next test starts clean.

    Resolution order:
      1. Exact key  (test_name) — set when conftest sends [TEST_START:xxx]
      2. "default"  bucket      — set when no [TEST_START:] is used
      3. Empty list
    """
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


# ─── POST /api/log-step ───────────────────────────────────────────────────────
@app.post("/api/log-step")
async def log_step(msg: LogMessage):
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
    for prefix in _PAYLOAD_PREFIXES:
        if message.startswith(prefix):
            raw = message[len(prefix):].strip()
            try:
                payload = json.loads(raw)
                steps = payload.get('steps_executed') or []
                clean_line = (f"[PAYLOAD] {payload.get('issue_id','')} | "
                              f"{payload.get('module','?')} | {payload.get('test_name','?')} | "
                              f"Steps ({len(steps)}): {', '.join(steps[:3]) if steps else 'none'}")
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
    steps = (
        _test_steps_store.get(test_name)
        or _test_steps_store.get("default")
        or []
    )
    print(f"📤 Fetch steps → {test_name}: {steps}")
    return {"steps": steps, "test_name": test_name}


@app.post("/api/jira/steps")
async def add_step(data: dict):
    test_name = data.get("test_name", "unknown")
    step = data.get("step", "")
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
    module = data.get("module")
    status = data.get("status")
    # Special signal: new run starting — broadcast RUN_START so frontend clears
    if module == "__RUN_START__":
        _broadcast_async({"type": "RUN_START", "payload": {}})
    else:
    
        _broadcast_async({"type": "MODULE", "payload": {
            "module": module, "status": status, "message": data.get("message", "")
        }})
    return {"status": "ok"}


# ─── POST /api/jira/payload ───────────────────────────────────────────────────
@app.post("/api/jira/payload")
async def receive_jira_payload(req: JiraPayloadRequest):
    payload = req.model_dump(exclude_none=False)

    incoming_steps = payload.get("steps_executed")

    if not incoming_steps:
        # Conftest got [] from the GET endpoint — inject from store now.
        # _resolve_steps_for_test POPS the bucket → next test starts clean.
        test_name = req.test_name or "default"
        resolved  = _resolve_steps_for_test(test_name)
        payload["steps_executed"] = resolved

        # Also patch description to include steps if it was built without them
        if resolved and payload.get("description") and "Steps Executed:" not in payload["description"]:
            steps_block = "\n\nSteps Executed:\n" + "\n".join(
                f"{i+1}. {s}" for i, s in enumerate(resolved)
            )
            payload["description"] = payload["description"] + steps_block

        logger.info("[/api/jira/payload] Injected %d steps for test=%s", len(resolved), test_name)
    else:
        # Payload has steps already (e.g. future conftest improvement).
        # Still pop the bucket to keep the store clean for the next test.
        _resolve_steps_for_test(req.test_name or "default")
        logger.info("[/api/jira/payload] Payload already has %d steps for test=%s",
                    len(incoming_steps), req.test_name)

    _pending_payloads.append(payload)
    await manager.broadcast({"type": "JIRA_PAYLOAD", "payload": payload})

    logger.info("[/api/jira/payload] %s module=%s test=%s steps=%d",
                req.issue_id, req.module, req.test_name,
                len(payload.get("steps_executed") or []))

    return {"status": "received", "issue_id": req.issue_id, "module": req.module}


@app.get("/api/jira/payloads")
async def get_pending_payloads():
    active = [p for p in _pending_payloads if _make_dismiss_key(p) not in _dismissed_keys]
    return {"payloads": active}


def _make_dismiss_key(payload: dict) -> str:
    tn = str(payload.get("test_name") or "").strip()
    md = str(payload.get("module")    or "").strip()
    if tn:
        return f"tn::{md}::{tn}"
    title = str(payload.get("issue_summary") or payload.get("title") or "").strip()
    return f"sum::{md}::{title}"


@app.post("/api/jira/dismiss")
async def dismiss_payload(data: dict):
    key = _make_dismiss_key(data)
    if key:
        _dismissed_keys.add(key)
    return {"status": "dismissed", "key": key}


# ─── POST /api/jira/create ────────────────────────────────────────────────────
@app.post("/api/jira/create")
async def jira_create(req: JiraCreateRequest):
    from jira_integration.jira_service import create_jira_issue
    from jira_integration.jira_config import config as jira_config

    if not jira_config.enabled:
        raise HTTPException(status_code=400, detail="Jira is disabled. Set JIRA_ENABLED=true in backend/.env")
    missing = [n for n, v in {
        "JIRA_URL": jira_config.url, "JIRA_EMAIL": jira_config.email,
        "JIRA_API_TOKEN": jira_config.api_token, "JIRA_PROJECT_KEY": jira_config.project_key,
    }.items() if not v]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing .env variables: {', '.join(missing)}. Edit backend/.env and restart.")

    summary     = (req.title or req.issue_summary or "Automation Failure").strip()
    description = (req.description or "Automation Test Failure").strip()

    import io as _io, contextlib as _ctx
    _captured = _io.StringIO()
    try:
        with _ctx.redirect_stdout(_captured):
            issue_key = create_jira_issue(
                summary=summary, description=description,
                app_name=req.app_name, app_version=req.app_version,
                module=req.module or req.parent, feature=req.feature,
                issue_summary=summary, test_name=req.test_name, test_id=req.test_id,
                steps_executed=req.steps_executed or [], developer_name=req.developer_name,
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
        _line = _line.strip()
        if not _line:
            continue
        _status = "PAYLOAD" if any(_line.startswith(p) for p in _PAYLOAD_PREFIXES) else "INFO"
        _broadcast_async({"type": "LOG", "payload": {"message": _line, "status": _status}})

    issue_url = f"{jira_config.url}/browse/{issue_key}"
    entry = {
        "issue_id": issue_key, "issue_url": issue_url, "title": summary,
        "description": description, "developer_name": req.developer_name or "",
        "module": req.module or req.parent or "", "app_name": req.app_name or "",
        "app_version": req.app_version or "", "test_name": req.test_name or "",
        "ticket_id": req.ticket_id or "", "fix_version": req.fix_version or [],
        "affects_version": req.affects_version or [], "priority": req.priority or "High",
        "sprint": req.sprint or "", "start_date": req.start_date or "",
        "end_date": req.end_date or "", "steps_executed": req.steps_executed or [],
        "status": "Assigned", "created_at": datetime.datetime.now().isoformat(),
    }
    _jira_history.append(entry)
    _broadcast_async({"type": "JIRA_CREATED", "payload": entry})
    return {"issue_id": issue_key, "issue_key": issue_key, "issue_url": issue_url, **entry}


# ─── Jira history & comments ──────────────────────────────────────────────────
_jira_comments: dict = {}

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
    comment = {"author": data.get("author") or "QA Automation",
               "text": text, "created_at": datetime.datetime.now().isoformat()}
    _jira_comments.setdefault(issue_key, []).append(comment)
    _broadcast_async({"type": "JIRA_COMMENT", "payload": {"issue_key": issue_key, "comment": comment}})
    return {"status": "ok", "comment": comment}

@app.get("/jira/history")
async def jira_history_legacy():
    return {"issues": [{"key": e.get("issue_id",""), "summary": e.get("title",""),
                        "status": e.get("status","Assigned"), "url": e.get("issue_url",""),
                        "priority": e.get("priority",""), "assignee": e.get("developer_name",""),
                        "updated": e.get("created_at","")} for e in _jira_history]}


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    from jira_integration.jira_config import config as jira_config
    return {
        "status": "ok",
        "jira_enabled": jira_config.enabled,
        "jira_url": jira_config.url or "(not set)",
        "jira_project_key": jira_config.project_key or "(not set)",
        "jira_email": jira_config.email or "(not set)",
        "jira_token_set": bool(jira_config.api_token),
        # ── Debug info — shows exactly what's in the step store ──
        "step_store_keys":   list(_test_steps_store.keys()),
        "step_store_counts": {k: len(v) for k, v in _test_steps_store.items()},
        "current_test":      _current_test_name,
        "pending_payloads":  len(_pending_payloads),
    }


# ─── Shared run-state reset ───────────────────────────────────────────────────
def _reset_run_state():
    global _pending_payloads, _dismissed_keys, _test_steps_store, _current_test_name
    _test_steps_store  = {}
    _current_test_name = "default"
    _pending_payloads  = []
    _dismissed_keys    = set()


# ─── Test runner routes ───────────────────────────────────────────────────────

@app.post("/start-test")
async def start_test(request: TestRequest, background_tasks: BackgroundTasks):
    _reset_run_state()
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
            stopped = True
        except Exception as e:
            print(f"Error stopping download: {e}")
    if stop_current_tests():
        stopped_something = True
    if stopped_something:
        await manager.broadcast({"type": "LOG", "payload": {"message": "Backend: Process stopped on user request.", "status": "FAILED"}})
        return {"status": "stopped"}
    return {"status": "no-process"}

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
        _appium_proc = subprocess.Popen(["appium", "-p", str(APPIUM_PORT)],
                                         shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

# ─── Add this Pydantic model alongside JiraPayloadRequest / JiraCreateRequest ─
 
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
    """
    Calls Gemini to generate a polished title + full formatted description
    (with Steps to Reproduce, Actual Result, Expected Result) and returns
    them so the frontend can paste directly into the issue card fields.
    """
    from generate_jira_desc import generate_jira_description, generate_jira_title
 
    issue_data = req.model_dump(exclude_none=True)
 
    try:
        loop = asyncio.get_event_loop()
 
        # Run both calls concurrently
        enhanced_description, enhanced_title = await asyncio.gather(
            loop.run_in_executor(None, generate_jira_description, issue_data),
            loop.run_in_executor(None, generate_jira_title, issue_data),
        )
 
    except Exception as exc:
        logger.error("[/api/jira/enhance] Gemini call failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"LLM enhancement failed: {str(exc)}",
        )
 
    logger.info(
        "[/api/jira/enhance] Enhanced issue_id=%s title='%s'",
        req.issue_id, enhanced_title,
    )
 
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
    uvicorn.run(app, host="127.0.0.1", port=8001)