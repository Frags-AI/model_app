from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import os
from config import settings
from core.voiceover import generate_voiceover

router = APIRouter()

@router.post('')
def voiceover(text: str = Form(...), voice: str = Form("default")):
    try:
        output_path = os.path.join(settings.DOWNLOAD_FOLDER, "audios", "voiceover.mp3")
        output_audio_path = generate_voiceover(text, voice, output_path)
        return JSONResponse({"voiceover_audio": output_audio_path})
    except Exception as e:
        return JSONResponse({"error": str(e)})