from fastapi import APIRouter, UploadFile, File, Form
import os
from fastapi.responses import JSONResponse
from .tasks.clip_anything_controller import process_video

router=APIRouter()

@router.post("/clip_video/")
async def clip_video(file: UploadFile = File(...), prompt: str = Form(...)):
    video_path = f"./uploads/{file.filename}"
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    with open(video_path, "wb") as f:
        f.write(await file.read())

    task = process_video.delay(video_path, prompt)
    return JSONResponse({"task_id": task.id})