from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from celery.result import AsyncResult
from celery_app.app import celery
import asyncio
router = APIRouter()

@router.websocket("/ws/{task_id}")
async def websocket_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            task_result = AsyncResult(task_id, app=celery)
            if task_result.state == "PROGRESS":
                await websocket.send_json({
                    "state": task_result.state,
                    "progress": task_result.info.get("progress")
                })
            elif task_result.state in ("SUCCESS", "FAILURE"):
                await websocket.send_json({
                    "state": task_result.state,
                    "result": task_result.result
                })
                break
            await asyncio.sleep(2.5)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {task_id}")
