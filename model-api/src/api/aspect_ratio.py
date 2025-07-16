from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from config import settings
from .tasks.aspect_ratio_controller import change_aspect_ratio
import os
from clients.aws import s3_service

router = APIRouter()

@router.post('')
async def adjust_aspect_ratio(ratio: str = Form(...), file: UploadFile = File(...), method: str = Form(...)):

    ratio_mapping = {"9:16": 9/16, "16:9": 16/9, "1:1": 1}
    ratio = ratio_mapping[ratio]

    s3_key = s3_service.generate_s3_key(file.filename)
    s3_url = s3_service.upload_file(file.file, s3_key)
    
    task = change_aspect_ratio.delay(s3_key, ratio, method)

    return JSONResponse({"task_id": task.id, "s3_url": s3_url}, 200)
