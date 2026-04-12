import subprocess
from typing import Dict, List, Any
import socket


appium_proc: subprocess.Popen | None = None
allure_proc: subprocess.Popen | None = None
allure_port: int | None = None
APPIUM_PORT = 4723

jira_history:      list[dict]           = []
pending_payloads:  list[dict]           = []
dismissed_keys:    set[str]             = set()
test_steps_store:  Dict[str, List[str]] = {}
current_test_name: str = "default"
jira_comments: dict = {}
runs: Dict[str, Dict[str, Any]] = {}
PAYLOAD_PREFIXES = ("AUTOMATION_PAYLOAD_JSON:", "JIRA_PAYLOAD_JSON:")
PROCESSED_EVENTS: set = set()

def reset_run_state():
    global pending_payloads, dismissed_keys, test_steps_store, current_test_name
    test_steps_store  = {}
    current_test_name = "default"
    pending_payloads  = []
    dismissed_keys    = set()

def is_appium_running() -> bool:
    global appium_proc
    if appium_proc is not None and appium_proc.poll() is None:
        return True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", APPIUM_PORT)) == 0


