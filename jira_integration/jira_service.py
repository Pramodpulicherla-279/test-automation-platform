import json
import requests
from jira_integration.jira_config import config


def search_duplicate_issue(summary):
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
    """
    Payload in the business format for logging / audit.
    """
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


def create_jira_issue(
    summary,
    description,
    allure_url=None,
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
    """
    Create Jira issue with duplicate detection.
    """
    if not config.validate():
        return None

    effective_summary = issue_summary or summary or "Automation Failure"

    business_payload = _build_business_payload(
        app_name=app_name,
        app_version=app_version,
        module=module,
        feature=feature,
        issue_summary=effective_summary,
        test_name=test_name,
        test_id=test_id,
        steps_executed=steps_executed,
        developer_name=developer_name,
    )

    # One-line JSON log so timestamped consoles do not break JSON copy/paste.
    print("AUTOMATION_PAYLOAD_JSON:" + json.dumps(business_payload, ensure_ascii=False))

    # Step 1 - Duplicate check
    if config.dedup_enabled:
        existing_issue = search_duplicate_issue(effective_summary)
        if existing_issue:
            print(f"Duplicate bug found: {existing_issue}")
            add_comment(existing_issue, "Automation detected this failure again.")
            return existing_issue

    # Step 2 - Description
    base_description = (description or "").strip()
    if not base_description:
        base_description = "Automation Test Failure"

    description_text = (
        f"{base_description}\n\n"
        f"Automation Payload:\n"
        f"{json.dumps(business_payload, ensure_ascii=False, indent=2)}"
    )

    if allure_url:
        description_text += f"\n\nAllure Report:\n{allure_url}"

    description_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": description_text}],
            }
        ],
    }

    jira_payload = {
        "fields": {
            "project": {"key": config.project_key},
            "summary": effective_summary,
            "description": description_adf,
            "issuetype": {"name": config.issue_type},
            "priority": {"name": config.priority},
            "assignee": {"id": config.assignee_id},
            "duedate": "2026-03-10",
            "labels": ["automation", "mobile-app", "krishivaas"],
        }
    }

    response = requests.post(
        config.issues_endpoint,
        json=jira_payload,
        auth=config.auth,
        headers=config.json_headers,
    )

    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"JIRA ISSUE CREATED: {issue_key}")
        return issue_key

    print(f"Jira creation failed ({response.status_code}): {response.text}")
    return None


def add_comment(issue_key, comment):
    """
    Add comment to existing Jira issue.
    """
    comment_adf = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment}],
                }
            ],
        }
    }

    response = requests.post(
        config.comment_endpoint(issue_key),
        json=comment_adf,
        auth=config.auth,
        headers=config.json_headers,
    )

    if response.status_code == 201:
        print(f"Comment added to {issue_key}")