from fastapi import UploadFile, File, Form, BackgroundTasks, HTTPException, APIRouter
from werkzeug.utils import secure_filename
from fastapi.responses import JSONResponse
from services.video_processing import process_and_update_video
from typing import Annotated
from config import settings
import logging
import os

router = APIRouter()

@router.post("/upload/")
async def upload_video(
    video: Annotated[UploadFile, File(...)], 
    video_name: Annotated[str, Form()] = None, 
    job_id: Annotated[str, Form()] = None, 
    background_tasks: BackgroundTasks = None
):
    if not video:
        raise HTTPException(status_code=400, detail="Please upload a file")
    
    # Use the original filename if video_name is not provided
    if not video_name:
        video_name = video.filename
    
    # Generate a job_id if not provided
    if not job_id:
        import uuid
        job_id = str(uuid.uuid4())
    
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

    # Only process the video if background_tasks is provided
    if background_tasks:
        background_tasks.add_task(process_and_update_video, job_id, save_path)
        logging.info("File has been successfully uploaded. Video processing will begin shortly")
    else:
        logging.info("File has been successfully uploaded without background processing")

    return JSONResponse(content={"message": "File has been temporarily stored", "job_id": job_id, "file_path": save_path}, media_type="application/json")