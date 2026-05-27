import os
import asyncio
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from new_backend.modules.test_runner.routes import router as test_router
from new_backend.modules.jira.routes import router as jira_router
from new_backend.modules.llm.routes import router as llm_router
from new_backend.modules.api_testing.routes import router as api_testing_router
from new_backend.core.websocket import router as websocket_router
from new_backend.modules.slack.routes import router as slack_router
from new_backend.modules.network_simulate.routes import router as network_simulate_router
from new_backend.core.events import lifespan

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )

app = FastAPI(
    title="Testing Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(websocket_router, prefix="/ws")
app.include_router(test_router, prefix="/test")
# app.include_router(jira_router, prefix="/jira")
# app.include_router(llm_router, prefix="/llm")
# app.include_router(slack_router, prefix="/slack")
# app.include_router(api_testing_router, prefix="/api-testing")
# app.include_router(network_simulate_router, prefix="/network-simulate")

# Health Check

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Testing Platform API"
    }

# ── Windows asyncio subprocess fix ──────────────────────────────────────────
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)