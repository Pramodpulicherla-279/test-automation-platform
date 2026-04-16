from fastapi import APIRouter
from .models import APILog
from .service import save_api_log, get_api_logs

router = APIRouter()

@router.post("/logs")
def add_log(log: APILog):
    save_api_log(log)
    return {"message": "log saved"}

@router.get("/logs")
def fetch_logs():
    return get_api_logs()