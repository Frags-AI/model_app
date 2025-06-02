from fastapi import APIRouter, WebSocket
import asyncio
import logging
from celery_app.job_manager import manager

router = APIRouter()


@router.websocket("/status/{job_id}")
async def websocket_status(websocket: WebSocket, job_id: str):
    await websocket.accept()
    await websocket.send_json({"message": "Connected to Server", "ok": True, "status": "connection"})
    logging.info("Successfully connected to Client")

    if not manager.exists(job_id):
        await websocket.send_json({"message": "Invalid job ID", "ok": False, "status": "connection"})
        logging.error("Invalid Job ID or Job has expired")
        await websocket.close()
        return
    
    await websocket.send_json({"message": "Your job is currently being processed, we will let you know when it has finished!", "ok": True, "status": "connection"})
    logging.info("Model is currently processing video into clips")
    while True:
        await asyncio.sleep(2)
        job = manager.get_job(job_id)
        data = job.get_JSON()
        data["type"] = "progress"
        await websocket.send_json(data)
        status = manager.get_job_status(job_id)
        if status == "completed":
            await websocket.send_json({"message": "Video has finished processing!", "ok": True, "status": "connection"})
            break
    await websocket.close()
