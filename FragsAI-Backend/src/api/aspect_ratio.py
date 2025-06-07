from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from config import settings
from .tasks.aspect_ratio_controller import change_aspect_ratio
import os

router=APIRouter()

@router.post('')
async def adjust_aspect_ratio(ratio: str = Form(...), file: UploadFile = File(...), method: str = Form(...)):
    input_video_path = os.path.join(settings.UPLOAD_FOLDER, "videos", file.filename)
    output_folder_path = os.path.join(settings.DOWNLOAD_FOLDER, "videos")

    ratio_mapping = {"9:16": 9/16, "16:9": 16/9, "1:1": 1}
    
    bytes = await file.read()

    task = change_aspect_ratio.delay(bytes, input_video_path, output_folder_path, ratio_mapping[ratio], method)

    return JSONResponse({"task_id": task.id}, 200)
