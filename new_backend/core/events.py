import asyncio
from core.websocket import manager

def broadcast_async(message: dict) -> None:
    try:
        asyncio.create_task(manager.broadcast(message))
    except RuntimeError:
        pass
