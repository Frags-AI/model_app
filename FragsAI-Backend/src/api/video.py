from fastapi import UploadFile, File, Form, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from .tasks.video_controller import process_and_update_video
from celery_app.job_manager import manager
from config import settings
import logging


router = APIRouter()

@router.post("/upload/")
async def upload_video(video: UploadFile = File(...), video_name: str = Form(...)):
    if not video:
        raise HTTPException(status_code=400, detail="Please upload a file")
    
    ext = video_name.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Invalid file format, ensure that the file has the correct extension")

    
    task = process_and_update_video.delay(video, video_name)
    manager.add_job(task.id)
    logging.info(f"Enqueued video processing task {task.id} for video processing")

    return JSONResponse({
        "task_id":  task.id
    })