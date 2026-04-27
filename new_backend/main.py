import os
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from new_backend.modules.appium_grid.manager import start_appium_servers

# ✅ Existing modules
from new_backend.modules.test_runner.routes import router as test_router
from new_backend.modules.jira.routes import router as jira_router
from new_backend.modules.llm.routes import router as llm_router
from new_backend.modules.slack.routes import router as slack_router
from new_backend.core.websocket import router as websocket_router
from fastapi import Request

# 🔥 NEW: Appium module (PARALLEL SUPPORT)
from new_backend.modules.appium_grid.routes import router as appium_router


# -----------------------------
# 🚀 FastAPI App Init
# -----------------------------
app = FastAPI(title="Automation Platform", version="2.0")


# -----------------------------
# 🌐 CORS Setup
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# 🔗 ROUTERS
# -----------------------------
app.include_router(websocket_router, prefix="/ws")
app.include_router(test_router, prefix="/test")
app.include_router(jira_router, prefix="/jira")
app.include_router(llm_router, prefix="/llm")
app.include_router(slack_router, prefix="/slack")

# ✅ FIXED: Appium router - ONLY ONE REGISTRATION
app.include_router(appium_router, prefix="/appium")


# -----------------------------
# 🪟 Windows asyncio fix
# -----------------------------
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# -----------------------------
# ▶️ Run Server
# -----------------------------
if __name__ == "__main__":
    uvicorn.run(
    "new_backend.main:app",
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="debug",        # 🔥 ADD THIS
    access_log=True           # 🔥 ADD THIS
)
    
# ============================================
# 🔥 GLOBAL API LOGGER (FIX FOR NO LOG ISSUE)
# ============================================
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"\n🔥 API CALL → {request.method} {request.url}")
    response = await call_next(request)
    print(f"✅ RESPONSE → {response.status_code}\n")
    return response

@app.on_event("startup")
async def auto_start_appium():
    try:
        print("🚀 AUTO STARTING APPIUM...")
        servers = start_appium_servers()

        from new_backend.modules.appium_grid.appium_state import set_servers
        set_servers(servers)

    except Exception as e:
        print(f"❌ AUTO APPIUM FAILED: {e}")