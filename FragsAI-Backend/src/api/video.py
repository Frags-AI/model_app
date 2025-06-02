from fastapi import UploadFile, File, Form, HTTPException, APIRouter
from werkzeug.utils import secure_filename
from fastapi.responses import JSONResponse
from services.video_processing import process_and_update_video
from celery_app.job_manager import manager
from typing import Annotated
from config import settings
import logging
import os
import requests

router = APIRouter()

@router.post("/upload/")
async def upload_video(video: UploadFile = File(...), video_name: str = Form(...), job_id: str = Form(...)):
    if not video:
        raise HTTPException(status_code=400, detail="Please upload a file")
    
    ext = video_name.split(".")[-1].lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(status_code=422, detail="Invalid file format, ensure that the file has the correct extension")
    
    if video_name.find(".") != -1:
        video_name = video_name.split(".")[0]

    secure_name = secure_filename(video_name + "." + ext)
    save_path = os.path.join(settings.upload_folder, "videos", secure_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, "wb") as f:
        while chunk := await video.read(1024 * 1024):
            f.write(chunk)

    
    manager.add_job(job_id)
    task = process_and_update_video.delay(job_id, save_path)
    logging.info(f"Enqueued video processing task {task.id} for job {job_id}")

    return JSONResponse({
        "message": "File stored; processing started",
        "job_id":   job_id,
        "task_id":  task.id
    })