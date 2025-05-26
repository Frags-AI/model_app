from fastapi import UploadFile, File, Form, BackgroundTasks, HTTPException, APIRouter
from werkzeug.utils import secure_filename
from fastapi.responses import JSONResponse
from services.video_processing import process_and_update_video
from typing import Annotated
from config import settings
import logging
import os

router = APIRouter()

@router.post("/upload-video/")
async def upload_video(video: Annotated[UploadFile, File(...)], video_name: Annotated[str, Form()], job_id: Annotated[str, Form()], background_tasks: BackgroundTasks ):
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

    background_tasks.add_task(process_and_update_video, job_id, save_path)
    logging.info("File has been successfully uploaded. Video processing will begin shortly")

    return JSONResponse(content={"message": "File has been temporarily stored", "job_id": job_id}, media_type="application/json")