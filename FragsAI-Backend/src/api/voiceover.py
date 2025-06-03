from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
from config import settings
from services.voiceover import generate_voiceover

router = APIRouter()

@router.post("/voiceover/")
def voiceover(text: str = Form(...), voice: str = Form("default")):
    try:
        output_audio_path = generate_voiceover(text, voice)
        return JSONResponse({"voiceover_audio": output_audio_path})
    except Exception as e:
        return JSONResponse({"error": str(e)})