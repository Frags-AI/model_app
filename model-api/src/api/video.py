from fastapi import UploadFile, File, Form, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from .tasks.pipeline_controller import create_video_pipeline
from celery_app.job_manager import manager
from config import settings
import uuid
from clients.aws import s3_service


router = APIRouter()

@router.post("/upload/")
async def upload_video(video: UploadFile = File(...)):
    if not video:
        raise HTTPException(status_code=400, detail="Please upload a file")
    
    ext = video.filename.split(".")[-1].lower()
    if not video.content_type.startswith("video/") or ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Invalid file format, ensure that the file has the correct extension")
    
    s3_key = s3_service.generate_s3_key(video.filename)
    s3_url = s3_service.upload_file(video.file, s3_key, video.content_type)
    
    task = create_video_pipeline.delay(s3_key, video.filename)
    manager.add_job(task.id)

    return JSONResponse({
        "task_id":  task.id,
        "video_name": video.filename,
        "url": s3_url
    })