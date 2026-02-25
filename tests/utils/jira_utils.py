from jira import JIRA
import os

JIRA_SERVER = 'https://agribridge.atlassian.net'
JIRA_EMAIL = 'ram18253ee028@gmail.com'
JIRA_API_TOKEN = 'ATATT3xFfGF0TsXImU9TN7N9qRwguEoXIGyeKTi85XwPlye4jVRgZVF89m2_ksI2wgnydsnpklUrDfynE8Hbg78_1aXdbOrasd6lFa68nTblUfXWWMD8akF13leEKiB6zY30sSE4RUauUlDnydwy4qVorEsu0Xx5rYNKrxlatyKK157I0w-bXzA=4E7F35BC'
JIRA_PROJECT_KEY = 'AIzaSyB5IyZOn9mZDJUBIYu5A3wP4OdD2FCEa8g' # The prefix of your Jira tickets

def create_jira_bug(test_name, error_message, screenshot_path=None):
    try:
        # 1. Connect to Jira
        jira_options = {'server': JIRA_SERVER}
        jira = JIRA(options=jira_options, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))

        # 2. Format the Description
        description = f"""
        *Automated Test Failure*
        The test '{test_name}' has failed in the automation pipeline.
        
        *Error Traceback:*
        {{code}}
        {error_message}
        {{code}}
        """

        # 3. Define the Issue payload
        issue_dict = {
            'project': {'key': JIRA_PROJECT_KEY},
            'summary': f'Automation Failure: {test_name}',
            'description': description,
            'issuetype': {'name': 'Bug'},
            # You can add custom fields here like Environment, Assignee, etc.
        }

        # 4. Create the Issue
        new_issue = jira.create_issue(fields=issue_dict)
        print(f"\n[JIRA] Created bug ticket: {new_issue.key} - {JIRA_SERVER}/browse/{new_issue.key}")

        # 5. Attach Screenshot if available
        if screenshot_path and os.path.exists(screenshot_path):
            jira.add_attachment(issue=new_issue, attachment=screenshot_path)
            print(f"[JIRA] Attached screenshot to {new_issue.key}")

        return new_issue.key

    except Exception as e:
        print(f"Failed to create Jira ticket: {e}")
        return None