from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import os
from config import settings
from services.background import replace_background

router = APIRouter()

@router.post("/replace_background/")
def replace_bg(file: UploadFile = File(...)):
    video_path = os.path.join(settings.upload_folder, file.filename)
    
    with open(video_path, "wb") as f:
        f.write(file.read())

    try:
        output_path = replace_background(video_path)
        return JSONResponse({"output_video": output_path})
    except Exception as e:
        return JSONResponse({"error": str(e)})