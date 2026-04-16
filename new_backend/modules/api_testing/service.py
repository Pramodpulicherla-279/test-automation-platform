api_logs_store = []

def save_api_log(log):
    api_logs_store.append(log)

def get_api_logs():
    return api_logs_store[-200:]  # limit for UI performance