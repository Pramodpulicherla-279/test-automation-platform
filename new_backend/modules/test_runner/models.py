from pydantic import BaseModel
from typing import List, Dict, Optional

class RunCompleteEvent(BaseModel):
    report_url: str

class ExistingTestRequest(BaseModel):
    apk_name: str
    tests_to_run: Optional[List[Dict[str, str]]] = None

class LogMessage(BaseModel):
    message: str
    status: str = "INFO"

class TestRequest(BaseModel):
    url: str
    tests_to_run: Optional[List[Dict[str, str]]] = None
