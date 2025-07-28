from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from .services.thumbnail_controller import generate_video_thumbnail
from typing import Annotated
import os
import logging
import uuid

router = APIRouter()

@router.post("/generate/")
async def generate_thumbnail(
    video: Annotated[UploadFile, File(...)],
    prompt: Annotated[str, Form(...)],
    style: Annotated[str, Form()] = "cinematic",
    timestamp: Annotated[str, Form()] = "30"
):
    """
    Generate AI-enhanced thumbnails from video at specified timestamp.
    
    Args:
        video: Video file to extract thumbnail from
        prompt: Description of desired thumbnail style/content
        style: Thumbnail style (cinematic, gaming, vlog, etc.)
        timestamp: Timestamp in seconds to extract frame from
    
    Returns:
        JSON response with generated thumbnail URLs
    """
    try:
        # Convert timestamp to integer
        try:
            timestamp_int = int(timestamp)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp value")
        
        logging.info(f"Generating thumbnail for video: {video.filename}, prompt: '{prompt}', style: {style}, timestamp: {timestamp_int}s")
        
        if not video.filename:
            raise HTTPException(status_code=400, detail="Video file is required")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Save uploaded video temporarily
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        video_id = str(uuid.uuid4())
        video_extension = os.path.splitext(video.filename)[1]
        video_path = os.path.join(upload_dir, f"{video_id}{video_extension}")
        
        # Save video file
        with open(video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        logging.info(f"Video saved to: {video_path}")
        
        # Generate thumbnail
        result = generate_video_thumbnail(
            video_path=video_path,
            prompt=prompt,
            style=style,
            timestamp=timestamp_int
        )
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "thumbnails": result["thumbnails"],
                "message": "Thumbnails generated successfully"
            })
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating thumbnail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {str(e)}")