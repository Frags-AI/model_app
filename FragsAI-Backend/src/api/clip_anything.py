import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import uuid
import shutil
from pathlib import Path

# Import the clip_anything service
from services.clip_anything import process_video_with_prompt

router = APIRouter()

@router.post("/clip_video/")
async def clip_video(file: UploadFile = File(...), text_prompt: str = Form(...)) -> Dict[Any, Any]:
    """
    Process a video file with a text prompt to extract relevant clips.
    
    Args:
        file: The uploaded video file
        text_prompt: Text description of content to extract from the video
        
    Returns:
        JSON response with the URL to the clipped video
    """
    try:
        # Create unique filename to avoid conflicts
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Ensure uploads directory exists
        upload_dir = Path("./uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded video
        video_path = upload_dir / unique_filename
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process the video using the clip_anything service
        try:
            output_path = process_video_with_prompt(str(video_path), text_prompt)
            
            # Generate URL for the output video
            output_filename = os.path.basename(output_path)
            clip_url = f"/uploads/{output_filename}"
            
            return {
                "status": "success",
                "message": "Video processed successfully",
                "clipUrl": clip_url
            }
        except Exception as e:
            # Clean up the uploaded file if processing fails
            if os.path.exists(video_path):
                os.remove(video_path)
            raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")