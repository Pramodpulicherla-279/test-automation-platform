# profiler.py
import time
import subprocess
import requests
import sys
sys.dont_write_bytecode = True

def get_cpu(package_name):
    # Run ADB command to get CPU usage
    cmd = f"adb shell dumpsys cpuinfo | grep {package_name}"
    # ... processing logic to get number ...
    return 12.5 # Example value

def start_profiling(package_name):
    while True:
        cpu = get_cpu(package_name)
        requests.post("http://localhost:8000/api/metric", json={
            "cpu": cpu,
            "time": time.time()
        })
        time.sleep(1) # Poll every second