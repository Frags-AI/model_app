from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from .services import transcription_controller
import os
import uuid

router = APIRouter()

@router.post("/transcribe/")
async def transcribe_video(
    file: UploadFile = File(...),
    silence_thresh: int = Form(-50),
    min_silence_len: int = Form(500)
):
    """
    Transcribe audio from a video file
    """
    # Create a unique identifier for this transcription
    transcription_id = str(uuid.uuid4())
    
    # Create output directory
    output_dir = os.path.join("./uploads/transcriptions", transcription_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the uploaded video
    video_path = os.path.join(output_dir, file.filename)
    with open(video_path, "wb") as f:
        f.write(await file.read())
    
    # Process the transcription
    try:
        result = transcription_controller.transcribe_video(
            video_path, 
            output_dir=output_dir,
            silence_thresh=silence_thresh,
            min_silence_len=min_silence_len
        )
        
        if result.get("success"):
            return JSONResponse({
                "message": "Video transcribed successfully",
                "transcription_id": transcription_id,
                "transcription_text": result.get("transcription_text", ""),
                "status": "success"
            })
        else:
            return JSONResponse({
                "error": result.get("message", "Unknown error occurred"),
                "status": "error"
            }, status_code=500)
    except Exception as e:
        return JSONResponse({
            "error": f"Transcription failed: {str(e)}",
            "status": "error"
        }, status_code=500)

@router.get("/download/{transcription_id}")
async def download_transcription(transcription_id: str):
    """
    Download a generated transcription file
    """
    file_path = os.path.join("./uploads/transcriptions", transcription_id, "transcription.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/plain", filename="transcription.txt")
    else:
        return JSONResponse({"error": "Transcription file not found"}, status_code=404)
