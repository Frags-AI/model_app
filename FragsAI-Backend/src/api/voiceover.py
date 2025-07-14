from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse, FileResponse
from .services import voiceover_controller
import os
import uuid

router = APIRouter()

@router.post("/generate/")
async def generate_voiceover(text: str = Form(...), voice: str = Form("Jessica")):
    """
    Generate a voiceover from text using Elevenlabs API
    """
    # Create a unique filename for the output
    output_filename = f"voiceover_{uuid.uuid4()}.mp3"
    output_path = os.path.join("./uploads", output_filename)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate the voiceover
    result = voiceover_controller.generate_voiceover(text, voice, output_path)
    
    if "Error" in result:
        return JSONResponse({"error": result}, status_code=400)
    
    # Return the file path and a success message
    return JSONResponse({
        "message": "Voiceover generated successfully",
        "file_path": output_path,
        "status": "success"
    })

@router.get("/download/{filename}")
async def download_voiceover(filename: str):
    """
    Download a generated voiceover file
    """
    file_path = os.path.join("./uploads", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg", filename=filename)
    else:
        return JSONResponse({"error": "File not found"}, status_code=404)
