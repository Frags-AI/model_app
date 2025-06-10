from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import os
from config import settings
from core.background import generate_background

router = APIRouter()

@router.post("/replace_background/")
def replace_bg(prompt: str, file: UploadFile = File(...)):
    video_path = os.path.join(settings.UPLOAD_FOLDER, file.filename)
    
    with open(video_path, "wb") as f:
        f.write(file.read())

    try:
        output_path = generate_background(prompt, video_path)
        return JSONResponse({"output_video": output_path})
    except Exception as e:
        return JSONResponse({"error": str(e)})