import os
from jira_integration.jira_config import config
from typing import Optional, List, Dict, Any
from requests.auth import HTTPBasicAuth
import requests
import json
from datetime import datetime
from .jira_config import config


def search_duplicate_issue(summary: str):
    """
    Search Jira for existing bug with same summary.
    """
    jql = f'project={config.project_key} AND summary~"{summary}" AND statusCategory!=Done'

    payload = {
        "jql": jql,
        "maxResults": 5,
        "fields": ["summary"],
    }

    response = requests.post(
        config.search_endpoint,
        json=payload,
        auth=config.auth,
        headers=config.json_headers,
        timeout=30,
    )

    if response.status_code == 200:
        issues = response.json().get("issues", [])
        if issues:
            return issues[0]["key"]

    return None


def _normalize_steps(steps_executed):
    if not steps_executed:
        return []
    return [str(step).strip() for step in steps_executed if str(step).strip()]


def _is_unknown(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return True
        if s.lower().startswith("unknown"):
            return True
    return False


def _extract_nodeid_from_description(description_text: str) -> str | None:
    """
    Looks for:
      Test Case:
      <nodeid>
    """
    if not description_text:
        return None

    lines = [ln.rstrip("\r") for ln in description_text.splitlines()]
    for i, ln in enumerate(lines):
        if ln.strip().lower() == "test case:":
            for j in range(i + 1, min(i + 10, len(lines))):
                candidate = lines[j].strip()
                if candidate:
                    return candidate
            return None
    return None


def _parse_environment_kv_from_description(description_text: str) -> dict:
    """
    Extracts simple key/value lines if present, e.g:
      App: Krishivaas Farmer
      Version: 1.4.8
      APK Version: 1.4.8
      App Version: 1.4.8
      Developer: Ram
      Module: Login
      Feature: Login
    """
    if not description_text:
        return {}

    out: dict[str, str] = {}
    lines = [ln.strip() for ln in description_text.splitlines()]
    key_map = {
        "app": "app_name",
        "version": "app_version",
        "apk version": "app_version",
        "app version": "app_version",
        "developer": "developer_name",
        "module": "module",
        "feature": "feature",
        "test": "test_name",
        "test id": "test_id",
    }

    for ln in lines:
        if ":" not in ln:
            continue
        left, right = ln.split(":", 1)
        k = left.strip().lower()
        v = right.strip()
        if not v:
            continue
        if k in key_map:
            out[key_map[k]] = v

    return out


def _extract_app_name_from_environment_block(description_text: str) -> str | None:
    """
    If description contains:
      Environment:
      Krishivaas Farmer APK

    return "Krishivaas Farmer".
    """
    if not description_text:
        return None

    lines = [ln.strip() for ln in description_text.splitlines()]
    for i, ln in enumerate(lines):
        if ln.lower() == "environment:":
            for j in range(i + 1, min(i + 10, len(lines))):
                candidate = lines[j].strip()
                if not candidate:
                    continue
                if candidate.lower().startswith("automation payload"):
                    return None
                if candidate.lower().endswith(" apk"):
                    return candidate[:-4].strip()
                return candidate
    return None


def _infer_module_from_nodeid(nodeid: str) -> str | None:
    if not nodeid:
        return None
    s = nodeid.lower()
    if "login" in s:
        return "Login"
    if "onboarding" in s or "addfarm" in s:
        return "Onboarding"
    if "marketplace" in s:
        return "Marketplace"
    if "cart" in s:
        return "Cart"
    return None


def _infer_feature_from_nodeid(nodeid: str) -> str | None:
    return _infer_module_from_nodeid(nodeid)


def _infer_test_name_from_nodeid(nodeid: str) -> str | None:
    """
    nodeid example:
      tests/.../test_login_pytest.py::TestLogin::test_login_success
    """
    if not nodeid:
        return None
    parts = [p for p in str(nodeid).split("::") if p]
    return parts[-1] if parts else None


def _build_business_payload(
    app_name=None,
    app_version=None,
    module=None,
    feature=None,
    issue_summary=None,
    test_name=None,
    test_id=None,
    steps_executed=None,
    developer_name=None,
):
    return {
        "app_name": app_name or "Unknown App",
        "app_version": app_version or "Unknown Version",
        "module": module or "Unknown Module",
        "feature": feature or "Unknown Feature",
        "issue_summary": issue_summary or "Automation Failure",
        "test_name": test_name or "Unknown Test",
        "test_id": test_id or "Unknown Test ID",
        "steps_executed": _normalize_steps(steps_executed),
        "developer_name": developer_name or "Unknown Developer",
    }


def get_jira_user_display_name(account_id: str) -> str | None:
    if not account_id:
        return None

    resp = requests.get(
        f"{config.url}/rest/api/3/user",
        params={"accountId": account_id},
        auth=config.auth,
        headers={"Accept": "application/json"},
        timeout=20,
    )
    if resp.status_code == 200:
        return (resp.json() or {}).get("displayName")
    return None


def _adf_to_text(adf: dict | None) -> str:
    if not isinstance(adf, dict):
        return ""

    out: list[str] = []

    def walk(node):
        if not isinstance(node, dict):
            return
        t = node.get("type")

        if t == "text":
            out.append(node.get("text", ""))
            return

        if t in {"paragraph", "heading", "blockquote"}:
            for c in node.get("content", []) or []:
                walk(c)
            out.append("\n")
            return

        if t in {"bulletList", "orderedList"}:
            for c in node.get("content", []) or []:
                walk(c)
            out.append("\n")
            return

        if t == "listItem":
            out.append("- ")
            for c in node.get("content", []) or []:
                walk(c)
            out.append("\n")
            return

        for c in node.get("content", []) or []:
            walk(c)

    walk(adf)
    text = "".join(out)
    lines = [ln.rstrip() for ln in text.splitlines()]
    return "\n".join([ln for ln in lines if ln.strip()]).strip()


def _extract_embedded_automation_payload(description_text: str) -> dict | None:
    """
    Parses the JSON block embedded under:
      Automation Payload:
      { ...json... }
    """
    if not description_text:
        return None

    marker = "Automation Payload:"
    idx = description_text.find(marker)
    if idx == -1:
        return None

    after = description_text[idx + len(marker):].strip()
    after = after.split("\n\nAllure Report:", 1)[0].strip()

    try:
        return json.loads(after)
    except Exception:
        start = after.find("{")
        end = after.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(after[start:end + 1])
            except Exception:
                return None

    return None


def fetch_issue_from_jira(issue_key: str, *, fields: list[str] | None = None) -> dict | None:
    if not issue_key:
        return None

    params = {}
    if fields:
        params["fields"] = ",".join(fields)

    resp = requests.get(
        f"{config.url}/rest/api/3/issue/{issue_key}",
        params=params,
        auth=config.auth,
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def _fix_env_label() -> str:
    """
    Your rule: fix version must be Production or Staging.
    Controlled via env var APP_ENV (or JIRA_FIX_ENV).
    """
    env = (os.getenv("JIRA_FIX_ENV") or os.getenv("APP_ENV") or "production").strip().lower()
    return "Staging" if env in {"stage", "staging", "uat", "test"} else "Production"


def build_extended_jira_payload(issue_key: str, business_payload: dict) -> dict:
    """
    Extended payload for console/frontend.

    Your mapping rules:
      1) app_version = APK version (must be passed from runner/CLI or embedded payload)
      2) affects_version = [app_name]
         fix_version = [Production|Staging]
      3) start_date = today's date
      4) parent = module
         sprint = "Automation" (hardcoded)
    """
    issue = fetch_issue_from_jira(
        issue_key,
        fields=["summary", "description", "assignee", "duedate"],
    ) or {}

    fields_obj = issue.get("fields", {}) or {}
    summary = fields_obj.get("summary") or ""
    description_text = _adf_to_text(fields_obj.get("description"))

    # Prefer embedded payload from Jira description if present
    embedded = _extract_embedded_automation_payload(description_text) or {}

    merged = dict(business_payload or {})
    for k in [
        "app_name",
        "app_version",
        "module",
        "feature",
        "issue_summary",
        "test_name",
        "test_id",
        "steps_executed",
        "developer_name",
    ]:
        if k in embedded and embedded.get(k) not in (None, "", [], {}):
            merged[k] = embedded[k]

    # Extra fallback: if app_name still unknown, try to parse from "Environment:\n<name> APK"
    if _is_unknown(merged.get("app_name")):
        env_app = _extract_app_name_from_environment_block(description_text)
        if env_app:
            merged["app_name"] = env_app

    # Developer name preference: Jira assignee displayName
    assignee = fields_obj.get("assignee") or {}
    assignee_name = assignee.get("displayName") if isinstance(assignee, dict) else None
    if assignee_name:
        merged["developer_name"] = assignee_name

    app_name = merged.get("app_name") or "Unknown App"
    app_version = merged.get("app_version") or "Unknown Version"
    module = merged.get("module") or "Unknown Module"

    affects_versions = [app_name] if not _is_unknown(app_name) else []
    fix_versions = [_fix_env_label()]
    sprint_val = "Automation"
    start_date_val = datetime.date.today().isoformat()

    end_date_val = fields_obj.get("duedate")
    if not end_date_val:
        end_date_val = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    merged.update(
        {
            "issue_id": issue_key,
            "issue_url": f"{config.url}/browse/{issue_key}",
            "title": summary,
            "description": description_text,

            "app_version": app_version,
            "affects_version": affects_versions,
            "fix_version": fix_versions,
            "parent": module,
            "sprint": sprint_val,
            "start_date": start_date_val,
            "end_date": end_date_val,
        }
    )

    return merged


def create_jira_issue(
    summary: str,
    description: str,
    app_name: Optional[str] = None,
    app_version: Optional[str] = None,
    module: Optional[str] = None,
    feature: Optional[str] = None,
    issue_summary: Optional[str] = None,
    test_name: Optional[str] = None,
    test_id: Optional[str] = None,
    steps_executed: Optional[List[str]] = None,
    developer_name: Optional[str] = None,
    fix_version: Optional[str] = None,
    affects_version: Optional[str] = None,
    start_date: Optional[str] = None,     # ISO format: 2026-03-29T08:43:00
    end_date: Optional[str] = None,       # ISO format: 2026-03-29T08:44:00
    sprint: Optional[str] = None,         # Sprint name: "Automation"
) -> Optional[str]:
    """
    Create a JIRA issue with all metadata including test execution dates and sprint.
    
    Args:
        summary: Issue summary/title
        description: Issue description
        app_name: App name (e.g., "Krishivaas Farmer")
        app_version: App version (e.g., "1.3.96")
        module: Module being tested (Login, Onboarding, etc.)
        feature: Feature name
        issue_summary: Another summary field
        test_name: Name of the test that failed
        test_id: ID of the test
        steps_executed: List of automation steps executed
        developer_name: Developer responsible
        start_date: Test start time (ISO format)
        end_date: Test end time (ISO format)
        sprint: Sprint name for JIRA sprint field
    
    Returns:
        JIRA issue key (e.g., "AT-87") or None if creation failed
    """
    
    if not all([config.url, config.email, config.api_token, config.project_key]):
        raise Exception(
            f"JIRA config incomplete: url={config.url}, email={config.email}, "
            f"token_set={bool(config.api_token)}, project_key={config.project_key}"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Prepare issue fields
    # ═══════════════════════════════════════════════════════════════════════════
    
    fields = {
        "project": {"key": config.project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": "Bug"},
        "priority": {"name": "High"},
    }

    # Add optional fields
    if app_name:
        fields["labels"] = fields.get("labels", []) + ["automation", app_name.lower()]
    if module:
        fields["labels"] = fields.get("labels", []) + [module.lower()]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # *** KEY FIX: Map dates and sprint to JIRA custom fields ***
    # ═══════════════════════════════════════════════════════════════════════════
    # These custom field IDs MUST match your JIRA instance
    # Get them from: Project Settings → Issue Types → Bug → Configure Fields
    
    custom_fields = {
        # Test execution dates (date type fields)
        'customfield_10000': start_date,           # Test Start Date
        'customfield_10001': end_date,             # Test End Date
        
        # Test metadata (text fields)
        'customfield_10002': f"{_calculate_duration(start_date, end_date)}",  # Duration
        'customfield_10003': module or "",         # Test Module
        'customfield_10004': app_version or "",    # App Version
        'customfield_10005': test_name or "",      # Test Name
        
        # Sprint (this is CRITICAL for board display)
        # Note: Sprint field might be different in your JIRA — check actual field ID
        'customfield_10006': sprint or "Automation",  # Sprint Name
    }
    
    # Merge custom fields (remove None values to avoid API errors)
    for field_id, value in custom_fields.items():
        if value is not None and value != "":
            fields[field_id] = value
    
    print(f"[JIRA] Fields prepared:")
    print(f"  Summary: {summary}")
    print(f"  Module: {module}")
    print(f"  Start Date: {start_date}")
    print(f"  End Date: {end_date}")
    print(f"  Sprint: {sprint}")
    print(f"  Custom fields: {list(custom_fields.keys())}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Create issue via JIRA REST API
    # ═══════════════════════════════════════════════════════════════════════════
    
    auth = HTTPBasicAuth(config.email, config.api_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    url = f"{config.url}/rest/api/3/issue"
    
    try:
        print(f"\n[JIRA] POST {url}")
        print(f"[JIRA] Auth: {config.email}")
        print(f"[JIRA] Project: {config.project_key}")
        
        response = requests.post(
            url,
            auth=auth,
            headers=headers,
            json={"fields": fields},
            timeout=15,
        )
        
        print(f"[JIRA] Response status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            issue_key = data.get("key")
            issue_id = data.get("id")
            
            print(f"✓ JIRA Issue Created: {issue_key}")
            print(f"  ID: {issue_id}")
            print(f"  URL: {config.url}/browse/{issue_key}")
            print(f"  Start Date Field: {start_date}")
            print(f"  End Date Field: {end_date}")
            print(f"  Sprint Field: {sprint}")
            
            return issue_key
        
        elif response.status_code == 400:
            error = response.json()
            print(f"✗ JIRA 400 Bad Request")
            print(f"  Error: {error}")
            
            # Check if it's a custom field error
            errors = error.get("errors", {})
            if any("customfield" in str(k) for k in errors.keys()):
                print(f"\n⚠️  Custom field error detected!")
                print(f"  You may need to update the custom field IDs in jira_service.py")
                print(f"  Current IDs: {list(custom_fields.keys())}")
                print(f"  Check: Project Settings → Issue Types → Bug → Configure Fields")
            
            raise Exception(f"JIRA 400: {error}")
        
        elif response.status_code == 401:
            raise Exception(f"JIRA 401 Unauthorized: Check JIRA_EMAIL and JIRA_API_TOKEN in .env")
        
        elif response.status_code == 403:
            raise Exception(f"JIRA 403 Forbidden: No permission to create issues in {config.project_key}")
        
        else:
            raise Exception(f"JIRA {response.status_code}: {response.text[:500]}")
    
    except requests.exceptions.Timeout:
        raise Exception("JIRA request timed out (15s). Check JIRA_URL and network connectivity.")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Cannot connect to JIRA at {config.url}. Check JIRA_URL in .env")
    except Exception as e:
        print(f"✗ Error creating JIRA issue: {e}")
        raise


def _calculate_duration(start_date: Optional[str], end_date: Optional[str]) -> str:
    """Calculate test duration from ISO format dates."""
    if not start_date or not end_date:
        return "Unknown"
    
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        duration = (end - start).total_seconds()
        return f"{int(duration)} seconds"
    except Exception as e:
        print(f"[WARN] Could not calculate duration: {e}")
        return "Unknown"


def get_jira_issue(issue_key: str) -> Optional[Dict[str, Any]]:
    """Fetch JIRA issue details."""
    if not all([config.url, config.email, config.api_token]):
        raise Exception("JIRA config incomplete")
    
    auth = HTTPBasicAuth(config.email, config.api_token)
    headers = {"Accept": "application/json"}
    
    url = f"{config.url}/rest/api/3/issue/{issue_key}"
    
    try:
        response = requests.get(url, auth=auth, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch {issue_key}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching issue: {e}")
        return None
    """
    Create Jira issue with duplicate detection + payload logs.
    """
    if not config.validate():
        return None

    effective_summary = issue_summary or summary or "Automation Failure"
    description_text_input = (description or "").strip() or "Automation Test Failure"

    inferred_env = _parse_environment_kv_from_description(description_text_input)
    inferred_nodeid = _extract_nodeid_from_description(description_text_input)

    # Infer missing app/module/test fields from description (so fewer Unknowns)
    if _is_unknown(app_name):
        app_name = inferred_env.get("app_name") or _extract_app_name_from_environment_block(description_text_input) or app_name

    if _is_unknown(app_version):
        # App version should come from runner/CLI (APK metadata). If you add "APK Version: x" in description, it will be picked.
        app_version = inferred_env.get("app_version") or app_version

    if _is_unknown(test_id):
        test_id = inferred_env.get("test_id") or inferred_nodeid or test_id
    if _is_unknown(test_name):
        test_name = inferred_env.get("test_name") or _infer_test_name_from_nodeid(inferred_nodeid or "") or test_name

    if _is_unknown(module):
        module = inferred_env.get("module") or _infer_module_from_nodeid(inferred_nodeid or "") or module
    if _is_unknown(feature):
        feature = inferred_env.get("feature") or _infer_feature_from_nodeid(inferred_nodeid or "") or feature
        if _is_unknown(feature) and not _is_unknown(module):
            feature = module

    # Prefer Jira assignee display name if developer_name not provided
    if _is_unknown(developer_name):
        developer_name = inferred_env.get("developer_name") or developer_name
    if _is_unknown(developer_name):
        developer_name = get_jira_user_display_name(config.assignee_id) or developer_name

    business_payload = _build_business_payload(
        app_name=None if _is_unknown(app_name) else app_name,
        app_version=None if _is_unknown(app_version) else app_version,
        module=None if _is_unknown(module) else module,
        feature=None if _is_unknown(feature) else feature,
        issue_summary=effective_summary,
        test_name=None if _is_unknown(test_name) else test_name,
        test_id=None if _is_unknown(test_id) else test_id,
        steps_executed=steps_executed,
        developer_name=None if _is_unknown(developer_name) else developer_name,
    )

    print("AUTOMATION_PAYLOAD_JSON:" + json.dumps(business_payload, ensure_ascii=False))

    if config.dedup_enabled:
        existing_issue = search_duplicate_issue(effective_summary)
        if existing_issue:
            print(f"Duplicate bug found: {existing_issue}")
            add_comment(existing_issue, "Automation detected this failure again.")
            try:
                extended = build_extended_jira_payload(existing_issue, business_payload)
                print("JIRA_PAYLOAD_JSON:" + json.dumps(extended, ensure_ascii=False))
            except Exception as e:
                print(f"Failed to build extended payload for duplicate issue {existing_issue}: {e}")
            return existing_issue

    # Embed payload in description so Jira API can be the source of truth later
    desc_with_payload = (
        f"{description_text_input}\n\n"
        f"Automation Payload:\n"
        f"{json.dumps(business_payload, ensure_ascii=False, indent=2)}"
    )
    if allure_url:
        desc_with_payload += f"\n\nAllure Report:\n{allure_url}"

    description_adf = {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": desc_with_payload}]}],
    }

    due_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    jira_payload = {
        "fields": {
            "project": {"key": config.project_key},
            "summary": effective_summary,
            "description": description_adf,
            "issuetype": {"name": config.issue_type},
            "priority": {"name": config.priority},
            "assignee": {"id": config.assignee_id},
            "duedate": due_date,
            "labels": ["automation", "mobile-app", "krishivaas"],
        }
    }

    response = requests.post(
        config.issues_endpoint,
        json=jira_payload,
        auth=config.auth,
        headers=config.json_headers,
        timeout=30,
    )

    if response.status_code == 201:
        issue_key = response.json()["key"]
        # build_extended_jira_payload does a GET /rest/api/3/issue/{key}
        # which can fail on restricted projects — wrap it so it never blocks ticket creation
        try:
            extended = build_extended_jira_payload(issue_key, business_payload)
            print("JIRA_PAYLOAD_JSON:" + json.dumps(extended, ensure_ascii=False))
        except Exception as e:
            print(f"[WARN] Could not build extended payload for {issue_key}: {e}")
        return issue_key

    # ── Surface the exact Jira error so the caller can show it to the user ──
    status  = response.status_code
    try:
        body    = response.json()
        messages = body.get("errorMessages", [])
        errors   = body.get("errors", {})
        detail   = "; ".join(messages) if messages else str(errors) if errors else response.text
    except Exception:
        detail = response.text or f"HTTP {status}"

    error_msg = f"Jira API {status}: {detail}"
    print(f"Jira creation failed ({status}): {response.text}")
    raise RuntimeError(error_msg)


def add_comment(issue_key, comment):
    comment_adf = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}],
        }
    }

    response = requests.post(
        config.comment_endpoint(issue_key),
        json=comment_adf,
        auth=config.auth,
        headers=config.json_headers,
        timeout=20,
    )

    if response.status_code == 201:
        print(f"Comment added to {issue_key}")