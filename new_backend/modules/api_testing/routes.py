from fastapi import APIRouter
from .models import APILog
from .service import save_api_log, get_api_logs, run_api_test_flow

router = APIRouter()

@router.post("/logs")
def add_log(log: APILog):
    save_api_log(log)
    return {"message": "log saved"}

@router.get("/logs")
def fetch_logs():
    return get_api_logs()

@router.post("/api-testing-run")
async def start_api_test():
    return await run_api_test_flow()