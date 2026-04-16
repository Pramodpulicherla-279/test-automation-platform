from pydantic import BaseModel

class APILog(BaseModel):
    method: str
    endpoint: str
    url: str
    status: int
    response_time_ms: float
    timestamp: str