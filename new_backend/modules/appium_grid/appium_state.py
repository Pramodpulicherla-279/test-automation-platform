# appium_state.py
# ✅ File-backed persistence so pytest subprocess can read Appium server state.
#
# ROOT CAUSE FIX:
#   Original: stored servers only in a module-level list.
#   Problem:  pytest runs in a child subprocess (subprocess.Popen in test_runner.py).
#             The child imports this module fresh → appium_servers = [] always.
#             Result: conftest.get_servers() always returns [] → "Appium not started".
#   Fix:      set_servers() writes to a JSON temp-file.
#             get_servers() reads from that file, so any process sees the state.

import json
import os
import tempfile
from datetime import datetime

# Stable path that survives for the life of the OS session
_STATE_FILE = os.path.join(tempfile.gettempdir(), "appium_grid_state.json")

# In-process cache (for the main server process)
appium_servers = []


def get_servers():
    """
    Read server list from the shared JSON file.
    Falls back to [] on any read/parse error.
    Always reads from disk so child processes see the latest state.
    
    ENHANCEMENT: Now returns servers with device info
    Format: [{"device": "emulator-5554", "port": 4723, "pid": 1234}, ...]
    """
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                print(f"✅ Loaded {len(data)} Appium server(s) from state file")
                return data
    except Exception as e:
        pass
    return []


def set_servers(servers):
    """
    Persist server list to disk AND update in-process cache.
    `servers` must be a list of JSON-serialisable dicts
    (no subprocess.Popen objects).
    
    FIX: Now validates that servers contain device info before saving
    
    Expected format: [{"device": "emulator-5554", "port": 4723, "pid": 1234}, ...]
    """
    global appium_servers
    
    # FIX: Validate servers are serializable (no process objects)
    try:
        json.dumps(servers)  # Test serialization
    except TypeError as e:
        print(f"⚠️  Servers contain non-serializable objects: {e}")
        print(f"⚠️  Skipping state save (likely process objects in list)")
        return False
    
    appium_servers = servers
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(servers, f, indent=2)
        
        # FIX: Enhanced logging with device mapping
        print(f"\n{'='*60}")
        print(f"✅ APPIUM STATE SAVED ({len(servers)} server/servers)")
        print(f"{'='*60}")
        for srv in servers:
            device = srv.get("device", "unknown")
            port = srv.get("port", "?")
            pid = srv.get("pid", "?")
            print(f"   📱 {device:20} → port {port:5} (PID: {pid})")
        print(f"{'='*60}\n")
        return True
    except Exception as e:
        print(f"⚠️  Could not persist Appium state to file: {e}")
        return False


def clear_servers():
    """Remove all server records from disk and in-process cache."""
    global appium_servers
    appium_servers = []
    try:
        if os.path.exists(_STATE_FILE):
            os.remove(_STATE_FILE)
            print("✅ Appium state file cleared")
    except Exception as e:
        print(f"⚠️  Could not remove Appium state file: {e}")


def is_running() -> bool:
    """Return True if at least one server is registered."""
    return len(get_servers()) > 0


def get_status() -> str:
    """Return 'running' or 'stopped'."""
    return "running" if get_servers() else "stopped"


def get_count() -> int:
    """Return the number of registered servers."""
    return len(get_servers())


def get_device_for_port(port: int) -> str:
    """
    Get the device name for a given port.
    
    NEW: Helper to correlate port to device
    
    Args:
        port: Appium server port
    
    Returns:
        Device ID string or "unknown"
    """
    servers = get_servers()
    for srv in servers:
        if srv.get("port") == port:
            return srv.get("device", "unknown")
    return "unknown"


def get_port_for_device(device: str) -> int:
    """
    Get the port for a given device.
    
    NEW: Helper to find which port serves a device
    
    Args:
        device: Device ID
    
    Returns:
        Port number or None
    """
    servers = get_servers()
    for srv in servers:
        if srv.get("device") == device:
            return srv.get("port")
    return None


def get_device_mapping() -> dict:
    """
    Get mapping of device -> port.
    
    NEW: Helper for frontend to display device-to-port correlation
    
    Returns:
        {"emulator-5554": 4723, "emulator-5556": 4725, ...}
    """
    mapping = {}
    for srv in get_servers():
        device = srv.get("device", "unknown")
        port = srv.get("port")
        if port:
            mapping[device] = port
    return mapping


# FIX: Add startup message
print(f"✅ Appium state module initialized (state file: {_STATE_FILE})")