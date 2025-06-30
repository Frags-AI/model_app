from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from celery.result import AsyncResult
from celery_app.app import celery
import asyncio
import logging
router = APIRouter()

@router.websocket("/status/{task_id}")
async def websocket_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            task_result = AsyncResult(task_id, app=celery)
            if task_result.state == "PROGRESS":
                await websocket.send_json(task_result.result)
            elif task_result.state == "SUCCESS":
                await websocket.send_json(task_result.result)
                break
            elif task_result.state == "FAILURE":
                await websocket.send_json({"message": "Failed to process task"})
                break
            await asyncio.sleep(.2)
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected: {task_id}")
    except Exception as e:
        await websocket.send_json({"error": "Internal Server Error"})
