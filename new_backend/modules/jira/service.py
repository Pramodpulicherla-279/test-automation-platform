from core.state import test_steps_store, pending_payloads, dismissed_keys, PAYLOAD_PREFIXES, jira_history, jira_comments
from core.utils import resolve_steps_for_test, make_dismiss_key, extract_steps_from_numbered_list, format_description_with_steps, strip_embedded_steps_from_description
from core.logger import logger
from core.websocket import manager
from core.events import broadcast_async
import datetime
import os
import subprocess
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException
from .jira_config import config as jira_config
from .mongo_config import mongo_config
from .mongo_config import connect_mongodb, disconnect_mongodb, is_mongodb_enabled
from .mongo_jira_integration import create_and_store_jira_issue

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ────────────────────────────────────────────────────────────────────────
    # STARTUP
    # ────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("[STARTUP] Initializing application...")
    print("=" * 70)

    print("[STARTUP] Connecting to MongoDB...")
    if connect_mongodb():
        logger.info("✅ [STARTUP] MongoDB connected successfully")
        print("✅ [STARTUP] MongoDB connected successfully")
    else:
        logger.warning("⚠️  [STARTUP] MongoDB connection failed or disabled")
        print("⚠️  [STARTUP] MongoDB connection failed or disabled")

    print("[STARTUP] Server ready for requests\n")
    yield

    print("\n" + "=" * 70)
    print("[SHUTDOWN] Cleaning up...")
    print("=" * 70)
    
    # Disconnect from MongoDB
    disconnect_mongodb()
    
    # Clean up child processes
    global appium_proc, allure_proc
    if appium_proc is not None:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(appium_proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                appium_proc.kill()
        except Exception:
            pass

    print("[SHUTDOWN] Cleanup complete\n")

async def health_flow():
    return {
        "status": "ok",
        "jira_enabled": jira_config.enabled,
        "jira_url": jira_config.url or "(not set)",
        "jira_project_key": jira_config.project_key or "(not set)",
        "jira_email": jira_config.email or "(not set)",
        "jira_token_set": bool(jira_config.api_token),
        # ── Debug info — shows exactly what's in the step store ──
        "step_store_keys":   list(test_steps_store.keys()),
        "step_store_counts": {k: len(v) for k, v in test_steps_store.items()},
        "current_test":      current_test_name,
        "pending_payloads":  len(pending_payloads),
    }

async def jira_test_connection_flow():
    import requests as req_lib
    from .jira_config import config as jira_config
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

async def get_steps_flow(test_name: str):
    steps = (
        test_steps_store.get(test_name)
        or test_steps_store.get("default")
        or []
    )
    print(f"📤 Fetch steps → {test_name}: {steps}")
    return {"steps": steps, "test_name": test_name}

async def add_step_flow(data: dict):
    test_name = data.get("test_name", "unknown")
    step = data.get("step", "")
    test_steps_store.setdefault(test_name, [])
    if step and step not in test_steps_store[test_name]:
        test_steps_store[test_name].append(step)
        print(f"✅ Step added → {test_name}: {step}")
    return {"status": "ok", "test_name": test_name, "step_count": len(test_steps_store[test_name])}

async def reset_steps_flow():
    global test_steps_store, current_test_name
    test_steps_store  = {}
    current_test_name = "default"
    print("🧹 Step store cleared")
    return {"status": "cleared"}

async def receive_jira_payload_flow(req):
    payload = req.model_dump(exclude_none=False)

    # ── Step 1: Clean the raw description ────────────────────────────────────
    # The conftest may embed a "Steps Executed:" block directly in the
    # description string. Strip it out NOW so it never appears twice.
    raw_description = payload.get("description") or ""
    # Extract steps from the embedded block BEFORE stripping (used as fallback)
    steps_from_desc = extract_steps_from_numbered_list(raw_description)
    # Remove the embedded steps / metadata blocks from the description
    clean_description = strip_embedded_steps_from_description(raw_description).strip()
    payload["description"] = clean_description or "Test automation failure detected."

    # ── Step 2: Resolve steps_executed ────────────────────────────────────
    incoming_steps = [s for s in (payload.get("steps_executed") or []) if s]

    if not incoming_steps:
        test_name = req.test_name or "default"
        resolved  = resolve_steps_for_test(test_name)

        # Fallback: steps that conftest embedded in the description text
        if not resolved and steps_from_desc:
            resolved = steps_from_desc
            logger.info(
                "[/api/jira/payload] Steps recovered from description text for test=%s count=%d",
                test_name, len(resolved),
            )

        payload["steps_executed"] = resolved
        logger.info(
            "[/api/jira/payload] Injected %d steps for test=%s",
            len(resolved), test_name,
        )
    else:
        # Steps already present — just clean the store for the next test
        resolve_steps_for_test(req.test_name or "default")
        payload["steps_executed"] = incoming_steps
        logger.info(
            "[/api/jira/payload] Payload already has %d steps for test=%s",
            len(incoming_steps), req.test_name,
        )

    # ── Step 3: Rebuild description with metadata + steps ONCE ───────────
    payload["description"] = format_description_with_steps(
        description    = payload["description"],
        app_name       = payload.get("app_name"),
        app_version    = payload.get("app_version"),
        module         = payload.get("module"),
        test_name      = payload.get("test_name"),
        developer_name = payload.get("developer_name"),
        start_date     = payload.get("start_date"),
        end_date       = payload.get("end_date"),
        sprint         = payload.get("sprint"),
        steps_executed = payload.get("steps_executed"),
    )

    pending_payloads.append(payload)
    await manager.broadcast({"type": "JIRA_PAYLOAD", "payload": payload})

    logger.info(
        "[/api/jira/payload] %s module=%s test=%s steps=%d",
        req.issue_id, req.module, req.test_name,
        len(payload.get("steps_executed") or []),
    )

    return {"status": "received", "issue_id": req.issue_id, "module": req.module}
    payload = req.model_dump(exclude_none=False)

    incoming_steps = payload.get("steps_executed")

    if not incoming_steps:
        # Conftest got [] from the GET endpoint — inject from store now.
        # _resolve_steps_for_test POPS the bucket → next test starts clean.
        test_name = req.test_name or "default"
        resolved  = resolve_steps_for_test(test_name)
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
        resolve_steps_for_test(req.test_name or "default")
        logger.info("[/api/jira/payload] Payload already has %d steps for test=%s",
                    len(incoming_steps), req.test_name)

    pending_payloads.append(payload)
    await manager.broadcast({"type": "JIRA_PAYLOAD", "payload": payload})

    logger.info("[/api/jira/payload] %s module=%s test=%s steps=%d",
                req.issue_id, req.module, req.test_name,
                len(payload.get("steps_executed") or []))

    return {"status": "received", "issue_id": req.issue_id, "module": req.module}

async def get_pending_payloads_flow():
    active = [p for p in pending_payloads if make_dismiss_key(p) not in dismissed_keys]
    return {"payloads": active}

async def dismiss_payload_flow(data):
    key = make_dismiss_key(data)
    if key:
        dismissed_keys.add(key)
    return {"status": "dismissed", "key": key}


async def jira_create_flow(req):
    from .jira_config import config as jira_config

    if not jira_config.enabled:
        raise HTTPException(status_code=400, detail="Jira is disabled. Set JIRA_ENABLED=true in backend/.env")

    missing = [n for n, v in {
        "JIRA_URL": jira_config.url, "JIRA_EMAIL": jira_config.email,
        "JIRA_API_TOKEN": jira_config.api_token, "JIRA_PROJECT_KEY": jira_config.project_key,
    }.items() if not v]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing .env variables: {', '.join(missing)}.")

    summary = (req.title or req.issue_summary or "Automation Failure").strip()

    # ── FIX 3: Resolve steps from all available sources ───────────────────
    # Priority: (1) req.steps_executed, (2) server store, (3) description text
    steps_for_ticket: List[str] = [s for s in (req.steps_executed or []) if s]

    if not steps_for_ticket:
        # Try server store (non-destructive peek first, then pop)
        store_key = req.test_name or "default"
        steps_for_ticket = resolve_steps_for_test(store_key)

    if not steps_for_ticket and req.description:
        # Last resort: extract numbered list the conftest embedded in description
        steps_for_ticket = extract_steps_from_numbered_list(req.description)
        if steps_for_ticket:
            logger.info(
                "[/api/jira/create] Steps recovered from description for test=%s count=%d",
                req.test_name, len(steps_for_ticket),
            )

    # ── FIX 3: Always rebuild description with steps so Jira ticket always
    #    shows the STEPS EXECUTED block regardless of frontend payload state.
    raw_desc = req.description or "Automation Test Failure"
    description = format_description_with_steps(
        description    = strip_embedded_steps_from_description(raw_desc),
        app_name       = req.app_name,
        app_version    = req.app_version,
        module         = req.module or req.parent,
        test_name      = req.test_name,
        developer_name = req.developer_name,
        start_date     = req.start_date,
        end_date       = req.end_date,
        sprint         = req.sprint,
        steps_executed = steps_for_ticket,
    )

    logger.info(
        "[/api/jira/create] Creating ticket test=%s steps=%d",
        req.test_name, len(steps_for_ticket),
    )

    import io as _io, contextlib as _ctx
    _captured = _io.StringIO()
    try:
        with _ctx.redirect_stdout(_captured):
            print(f"[JIRA_CREATE] Creating ticket with MongoDB storage:")
            print(f"  Start Date:   {req.start_date}")
            print(f"  End Date:     {req.end_date}")
            print(f"  Sprint:       {req.sprint}")
            print(f"  Steps count:  {len(steps_for_ticket)}")
            print(f"  MongoDB:      {'Enabled' if is_mongodb_enabled() else 'Disabled'}")

            result = create_and_store_jira_issue(
                summary        = summary,
                description    = description,
                app_name       = req.app_name,
                app_version    = req.app_version,
                module         = req.module or req.parent,
                feature        = req.feature,
                issue_summary  = summary,
                test_name      = req.test_name,
                test_id        = req.test_id,
                steps_executed = steps_for_ticket,
                developer_name = req.developer_name,
                priority       = req.priority,
                start_date     = req.start_date,
                end_date       = req.end_date,
                sprint         = req.sprint,
            )

            if not result["success"]:
                raise Exception(result.get("error", "Unknown error"))

            issue_key = result["issue_id"]
            ticket_id = result["ticket_id"]
            issue_url = result["issue_url"]

    except Exception as exc:
        err = str(exc)
        logger.error("[/api/jira/create] Exception: %s", err)
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
        _status = "PAYLOAD" if any(_line.startswith(p) for p in PAYLOAD_PREFIXES) else "INFO"
        broadcast_async({"type": "LOG", "payload": {"message": _line, "status": _status}})

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
        "ticket_id":       ticket_id or req.ticket_id or "",
        "fix_version":     req.fix_version or [],
        "affects_version": req.affects_version or [],
        "priority":        req.priority or "High",
        "sprint":          req.sprint or "Automation",
        "start_date":      req.start_date or "",
        "end_date":        req.end_date or "",
        "steps_executed":  steps_for_ticket,
        "status":          "Assigned",
        "created_at":      datetime.datetime.now().isoformat(),
    }
    jira_history.append(entry)
    broadcast_async({"type": "JIRA_CREATED", "payload": entry})

    print(f"\n✓ JIRA Ticket Created and Stored: {issue_key}")
    print(f"  Ticket ID:    {ticket_id}")
    print(f"  Steps:        {len(steps_for_ticket)}")
    print(f"  MongoDB:      {'✅ Saved' if ticket_id != 'N/A' else '⚠️  Not saved (MongoDB may be disabled)'}")
    print(f"  Start Date:   {req.start_date}")
    print(f"  End Date:     {req.end_date}")
    print(f"  Sprint:       {req.sprint}")

    return {
        "issue_id":    issue_key,
        "issue_key":   issue_key,
        "issue_url":   issue_url,
        "ticket_id":   ticket_id,
        "mongodb_saved": ticket_id != "N/A",
        **entry
    }

async def add_comment_flow(issue_key: str, data: dict):
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Comment text required")
    comment = {"author": data.get("author") or "QA Automation",
               "text": text, "created_at": datetime.datetime.now().isoformat()}
    jira_comments.setdefault(issue_key, []).append(comment)
    broadcast_async({"type": "JIRA_COMMENT", "payload": {"issue_key": issue_key, "comment": comment}})
    return {"status": "ok", "comment": comment}



