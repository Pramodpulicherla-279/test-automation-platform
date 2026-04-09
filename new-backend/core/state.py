import subprocess
from typing import Dict, List


_appium_proc: subprocess.Popen | None = None
APPIUM_PORT = 4723

jira_history:      list[dict]           = []
pending_payloads:  list[dict]           = []
dismissed_keys:    set[str]             = set()
test_steps_store:  Dict[str, List[str]] = {}
current_test_name: str = "default"
jira_comments: dict = {}
PAYLOAD_PREFIXES = ("AUTOMATION_PAYLOAD_JSON:", "JIRA_PAYLOAD_JSON:")


def reset_run_state():
    global pending_payloads, dismissed_keys, test_steps_store, current_test_name
    test_steps_store  = {}
    current_test_name = "default"
    pending_payloads  = []
    dismissed_keys    = set()