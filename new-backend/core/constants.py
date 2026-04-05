import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.abspath(__file__))))
ALLURE_CMD = r"C:\Users\Pramo\scoop\shims\allure"
ALLURE_REPORT_DIR = os.path.join(BASE_DIR, "allure-report")
PAYLOAD_PREFIXES = ("AUTOMATION_PAYLOAD_JSON:", "JIRA_PAYLOAD_JSON:")

