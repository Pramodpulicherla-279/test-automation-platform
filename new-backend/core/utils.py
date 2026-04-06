import socket
import re
import asyncio
from pathlib import Path
from fastapi import HTTPException
from aiohttp_retry import List
from core.websocket import manager
from core.state import test_steps_store
from core.constants import UI_SCREENSHOTS_BASE

def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])
    
def resolve_steps_for_test(test_name: str) -> List[str]:
    """
    Called only by receive_jira_payload. Pops the matched bucket so
    the next test starts clean.

    Resolution order:
      1. Exact key  (test_name) — set when conftest sends [TEST_START:xxx]
      2. "default"  bucket      — set when no [TEST_START:] is used
      3. Empty list
    """
    if test_name and test_name in test_steps_store:
        steps = test_steps_store.pop(test_name)
        print(f"✅ Steps resolved (exact) → {test_name}: {steps}")
        return steps
    if "default" in test_steps_store:
        steps = test_steps_store.pop("default")
        print(f"✅ Steps resolved (default fallback) → {test_name}: {steps}")
        return steps
    print(f"⚠️  No steps in store for {test_name}")
    return []

def make_dismiss_key(payload: dict) -> str:
    tn = str(payload.get("test_name") or "").strip()
    md = str(payload.get("module")    or "").strip()
    if tn:
        return f"tn::{md}::{tn}"
    title = str(payload.get("issue_summary") or payload.get("title") or "").strip()
    return f"sum::{md}::{title}"

def latest_run_id() -> str:
    runs = [p for p in UI_SCREENSHOTS_BASE.iterdir() if p.is_dir()]
    if not runs:
        raise HTTPException(404, detail="No UI screenshots found. Run tests and capture screenshots first.")
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].name


