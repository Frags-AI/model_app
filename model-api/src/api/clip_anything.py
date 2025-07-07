from fastapi import APIRouter, UploadFile, File, Form
import os
from fastapi.responses import JSONResponse
from .tasks.clip_anything_controller import process_video
from clients.aws import s3_service

router=APIRouter()

@router.post("")
async def clip_video(file: UploadFile = File(...), prompt: str = Form(...)):
    
    s3_key = s3_service.generate_s3_key(file.filename)
    s3_url = s3_service.upload_file(file.file, s3_key, file.content_type)\

    task = process_video.delay(s3_key, prompt)

    return JSONResponse({"task_id": task.id, "url": s3_url})