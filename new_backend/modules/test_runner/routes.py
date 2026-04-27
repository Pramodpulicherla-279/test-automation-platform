from fastapi import APIRouter, BackgroundTasks, HTTPException
from .models import TestRequest, ExistingTestRequest, RunCompleteEvent, LogMessage
from .service import (
    start_test_flow, 
    stop_test_flow, 
    start_test_existing_flow, 
    list_apks_flow, 
    allure_start_flow, 
    device_status_flow, 
    run_complete_flow, 
    module_status_flow, 
    api_generate_report_flow, 
    run_tests_flow, 
    log_step_flow
)
from new_backend.core.websocket import manager

# ============================================================================
# 🚀 Test Runner Router
# ============================================================================
router = APIRouter(tags=["Test Runner"])


# ============================================================================
# 📋 Status & Device Endpoints
# ============================================================================

@router.get("/device-status")
async def device_status():
    """Get current device connection status"""
    return await device_status_flow()



@router.post("/module-status")
async def module_status(data: dict):
    """Update module execution status"""
    return await module_status_flow(data)


@router.post("/log-step")
async def log_step(msg: LogMessage):
    """Log individual test step"""
    await log_step_flow(msg)
    return {"status": "logged"}


# ============================================================================
# 🚀 Test Execution Endpoints
# ============================================================================

@router.post("/start-test")
async def start_test(request: TestRequest, background_tasks: BackgroundTasks):
    """
    Start test with APK URL (Google Drive)
    
    Request body:
    {
        "url": "https://drive.google.com/...",
        "tests_to_run": [{"name": "Login", "path": "..."}],
        "app_type": "regular_farmer"
    }
    """
    return await start_test_flow(request, background_tasks, manager)


@router.post("/start-test-existing")
async def start_test_existing(request: ExistingTestRequest, background_tasks: BackgroundTasks):
    """
    Start test with existing APK (already on server)
    
    Request body:
    {
        "apk_name": "Krishivaas Farmer.apk",
        "tests_to_run": [{"name": "Login", "path": "..."}],
        "app_type": "regular_farmer"
    }
    """
    print("🔥 API HIT → /test/start-test-existing")
    print(f"📦 APK: {request.apk_name}")
    print(f"🧪 Tests: {request.tests_to_run}")
    return await start_test_existing_flow(request, background_tasks, manager)
    

@router.post("/stop-test")
async def stop_test():
    """Stop currently running test"""
    stopped = stop_test_flow(manager)

    if stopped:
        return {"status": "stopped"}
    return {"status": "no-process"}


@router.post("/run-complete")
async def run_complete(event: RunCompleteEvent):
    """Handle test run completion event"""
    return await run_complete_flow(event)


# ============================================================================
# 📦 APK & Report Endpoints
# ============================================================================

@router.get("/apk-list")
async def list_apks():
    """Get list of available APKs on server"""
    return await list_apks_flow()


@router.post("/allure/start")
async def allure_start():
    """Initialize Allure report generation"""
    return await allure_start_flow()


@router.post("/generate-report")
async def generate_report():
    """Generate Allure HTML report from test results"""
    return await api_generate_report_flow()


@router.post("/run")
async def run_tests():
    """Execute test run"""
    return await run_tests_flow()


# ============================================================================
# ✅ Router Summary
# ============================================================================
"""
ENDPOINTS:
  
  GET  /test/device-status              → Check device connection status
  POST /test/module-status              → Update module execution status
  POST /test/log-step                   → Log individual test step
  
  POST /test/start-test                 → Start test with Google Drive APK
  POST /test/start-test-existing        → Start test with server APK
  POST /test/stop-test                  → Stop running test
  POST /test/run-complete               → Handle completion event
  
  GET  /test/apk-list                   → List available APKs
  POST /test/allure/start               → Initialize report
  POST /test/generate-report            → Generate HTML report
  POST /test/run                        → Run tests
"""