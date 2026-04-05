import subprocess

_appium_proc: subprocess.Popen | None = None
APPIUM_PORT = 4723

def reset_run_state():
    global _pending_payloads, _dismissed_keys, _test_steps_store, _current_test_name
    _test_steps_store  = {}
    _current_test_name = "default"
    _pending_payloads  = []
    _dismissed_keys    = set()