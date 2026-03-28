# utils/test_flow_logger.py
import sys
sys.dont_write_bytecode = True

test_flow_log = []

def log_step(step_description):
    test_flow_log.append(step_description)

def get_logged_steps():
    return test_flow_log
