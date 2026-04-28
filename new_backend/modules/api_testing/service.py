import subprocess
api_logs_store = []

def save_api_log(log):
    api_logs_store.append(log)

def get_api_logs():
    return api_logs_store[-200:]  # limit for UI performance

async def run_api_test_flow():
    command = [
        "k6",
        "run",
        "load_test.js",
        "--out",
        "influxdb=http://localhost:8086/k6"
    ]

    result = subprocess.Popen(command)

    return {
        "status": "started"
    }