from fastapi import UploadFile, File, Form, HTTPException, APIRouter
from werkzeug.utils import secure_filename
from fastapi.responses import JSONResponse
from services.video_processing import process_and_update_video
from celery_app.job_manager import manager
from config import settings
import logging
import os

router = APIRouter()

@router.post("/upload-video/")
async def upload_video(
    video: UploadFile = File(...),
    video_name: str = Form(...),
    job_id: str = Form(...)
):
    if not video:
        raise HTTPException(status_code=400, detail="Please upload a file")

    ext = video_name.split(".")[-1].lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=422,
            detail="Invalid file format; ensure correct extension"
        )

    base_name = video_name.rsplit(".", 1)[0]
    secure_name = secure_filename(f"{base_name}.{ext}")
    save_dir = os.path.join(settings.upload_folder, "videos")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, secure_name)

    with open(save_path, "wb") as f:
        while chunk := await video.read(1024 * 1024):
            f.write(chunk)

    manager.add_job(job_id)
    task = process_and_update_video.delay(job_id, save_path)
    logging.info(f"Enqueued video processing task {task.id} for job {job_id}")

    return JSONResponse({
        "message": "File stored; processing started",
        "job_id": job_id,
        "task_id": task.id
    })
