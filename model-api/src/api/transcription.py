from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import os
from config import settings
from core.transcription import transcribe_video

router = APIRouter()

@router.post("/transcribe/")
def transcribe(file: UploadFile = File(...)):
    video_path = os.path.join(settings.UPLOAD_FOLDER, file.filename)
    
    with open(video_path, "wb") as f:
        f.write(file.read())
    
    try:
        transcription = transcribe_video(video_path)
        return JSONResponse({"transcription": transcription})
    except Exception as e:
        return JSONResponse({"error": str(e)})