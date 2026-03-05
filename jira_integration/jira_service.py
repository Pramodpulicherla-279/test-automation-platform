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
        "fields": ["summary"]
    }

    response = requests.post(
        config.search_endpoint,
        json=payload,
        auth=config.auth,
        headers=config.json_headers
    )

    if response.status_code == 200:
        issues = response.json().get("issues", [])
        if issues:
            return issues[0]["key"]

    return None


def create_jira_issue(summary, description, allure_url=None):
    """
    Create Jira issue with duplicate detection.
    """

    if not config.validate():
        return None

    # Step 1 — Check duplicates
    if config.dedup_enabled:
        existing_issue = search_duplicate_issue(summary)

        if existing_issue:
            print(f"Duplicate bug found: {existing_issue}")
            add_comment(existing_issue, "Automation detected this failure again.")
            return existing_issue

    # Step 2 — Build description
    text = description

    if allure_url:
        text += f"\n\nAllure Report:\n{allure_url}"

    # Atlassian Document Format
    description_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": text}
                ]
            }
        ]
    }

    payload = {
    "fields": {

        "project": {
            "key": config.project_key
        },

        "summary": summary,

        "description": description_adf,

        "issuetype": {
            "name": config.issue_type
        },

        "priority": {
            "name": config.priority
        },

        "assignee": {
            "id": config.assignee_id
        },

        "duedate": "2026-03-10",

        "labels": [
            "automation",
            "mobile-app",
            "krishivaas"
        ]
    }
}

    response = requests.post(
        config.issues_endpoint,
        json=payload,
        auth=config.auth,
        headers=config.json_headers
    )

    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"JIRA ISSUE CREATED: {issue_key}")
        return issue_key

    print("Jira creation failed:", response.text)
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
                    "content": [
                        {"type": "text", "text": comment}
                    ]
                }
            ]
        }
    }

    response = requests.post(
        config.comment_endpoint(issue_key),
        json=comment_adf,
        auth=config.auth,
        headers=config.json_headers
    )

    if response.status_code == 201:
        print(f"Comment added to {issue_key}")