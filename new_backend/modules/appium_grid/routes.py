from fastapi import APIRouter, HTTPException
from .manager import start_appium_servers, stop_appium_servers
# Import from the dedicated state module — survives module reloads
from .appium_state import (
    get_servers, 
    set_servers, 
    clear_servers, 
    get_status, 
    get_count,
    get_device_for_port,  # NEW
    get_port_for_device,  # NEW
    get_device_mapping    # NEW
)
import asyncio

router = APIRouter()


@router.post("/start")
async def start():
    """
    Start Appium servers with retry logic for devices.
    Uses persistent state storage.

    FIXES:
    - Line 28-35: Better validation of return value from start_appium_servers()
    - Line 36-47: Enhanced response with device mapping
    
    Returns: 
    {
        "status": "running",
        "servers": [{"device": "emulator-5554", "port": 4723, "pid": 1234}],
        "device_mapping": {"emulator-5554": 4723},
        "message": "Appium started with X device(s)",
        "count": 1
    }
    """
    try:
        max_retries = 5
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                # Get fresh device list and start Appium servers
                safe_servers = start_appium_servers()
                
                # FIX: Validate returned servers have required fields
                if not safe_servers:
                    raise Exception("start_appium_servers() returned empty list")
                
                # Verify all servers have device info
                for srv in safe_servers:
                    if not srv.get("device") or not srv.get("port"):
                        raise Exception(f"Invalid server data: {srv}")

                # FIX: Save to persistent state with validation
                if not set_servers(safe_servers):
                    raise Exception("Failed to persist server state")

                # FIX: Enhanced response with device mapping
                device_mapping = get_device_mapping()
                
                print(f"✅ Appium servers started on attempt {attempt + 1}")
                return {
                    "status": "running",
                    "servers": get_servers(),
                    "device_mapping": device_mapping,  # NEW: Device -> Port mapping
                    "message": f"Appium started with {len(get_servers())} device(s)",
                    "count": get_count()
                }
            except Exception as device_error:
                if attempt < max_retries - 1:
                    print(f"⏳ Attempt {attempt + 1} failed: {str(device_error)}. "
                          f"Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"❌ Failed to start Appium after {max_retries} attempts: "
                          f"{str(device_error)}")
                    raise device_error

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Appium start error: {error_msg}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to start Appium: {error_msg}. "
                   f"Ensure emulator/devices are running. Check ADB devices."
        )


@router.post("/stop")
def stop():
    """Stop all Appium servers and clear state."""
    try:
        stop_appium_servers()
        clear_servers()
        return {
            "status": "stopped",
            "message": "All Appium servers stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping Appium: {str(e)}")


@router.get("/status")
def status():
    """
    Get current Appium server status from persistent state.
    
    FIXES:
    - Line 109-128: Enhanced response with device mapping and detailed info
    - Returns lowercase status for consistent frontend comparison
    - Now shows which device is on which port
    
    Returns:
    {
        "status": "running" | "stopped",
        "servers": [{"device": "emulator-5554", "port": 4723, "pid": 1234}],
        "device_mapping": {"emulator-5554": 4723},
        "count": 1,
        "is_ready": True  // NEW: Whether tests can start
    }
    """
    try:
        current_servers = get_servers()
        current_status  = get_status()
        device_mapping  = get_device_mapping()

        # FIX: Add is_ready flag - tests can only start if servers exist
        is_ready = len(current_servers) > 0

        return {
            "status": current_status,              # Always lowercase: "running" | "stopped"
            "servers": current_servers,            # Safe dicts from appium_state
            "device_mapping": device_mapping,      # NEW: Device -> Port mapping
            "count": get_count(),                  # Number of servers
            "is_ready": is_ready,                  # NEW: Can tests start?
            "message": (
                f"Appium running with {get_count()} device(s)"
                if is_ready
                else "No Appium servers running"
            )
        }
    except Exception as e:
        print(f"❌ Status check error: {str(e)}")
        return {
            "status": "unknown",
            "servers": [],
            "device_mapping": {},
            "count": 0,
            "is_ready": False,
            "error": str(e)
        }


@router.get("/device-info/{port}")
def device_info(port: int):
    """
    Get device info for a specific Appium server port.
    
    NEW: Helper endpoint to get which device is on which port
    
    Args:
        port: Appium server port (e.g., 4723)
    
    Returns:
    {
        "port": 4723,
        "device": "emulator-5554",
        "found": True
    }
    """
    device = get_device_for_port(port)
    return {
        "port": port,
        "device": device,
        "found": device != "unknown"
    }


@router.get("/devices")
def devices_list():
    """
    Get list of all connected devices with their Appium ports.
    
    NEW: Helper endpoint for frontend to display all devices
    
    Returns:
    {
        "devices": [
            {"id": "emulator-5554", "port": 4723, "status": "ready"},
            {"id": "emulator-5556", "port": 4725, "status": "ready"}
        ],
        "total": 2
    }
    """
    servers = get_servers()
    devices = []
    for srv in servers:
        devices.append({
            "id": srv.get("device", "unknown"),
            "port": srv.get("port"),
            "pid": srv.get("pid"),
            "status": "ready"
        })
    
    return {
        "devices": devices,
        "total": len(devices)
    }


print("✅ Appium router loaded with persistent state storage and device tracking")