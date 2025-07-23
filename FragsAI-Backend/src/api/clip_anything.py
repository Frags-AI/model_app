import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import uuid
import shutil
from pathlib import Path

# Import the clip_anything service
from services.clip_anything import process_video_with_prompt

router = APIRouter()

@router.post("/clip_video/")
async def clip_video(
    file: UploadFile = File(...), 
    text_prompt: str = Form(...),
    max_clips: int = Form(10)
) -> Dict[Any, Any]:
    """
    Process a video file with a text prompt to extract relevant clips.
    
    Args:
        file: The uploaded video file
        text_prompt: Text description of content to extract from the video
        max_clips: Maximum number of clips to generate (default: 10)
        
    Returns:
        JSON response with URLs to the clipped videos and their virality scores
    """
    try:
        # Create unique filename to avoid conflicts
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Ensure uploads directory exists
        upload_dir = Path("./uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Ensure clips directory exists
        clips_dir = Path("./uploads/clips")
        clips_dir.mkdir(exist_ok=True)
        
        # Save uploaded video
        video_path = upload_dir / unique_filename
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process the video using the clip_anything service
        try:
            result = process_video_with_prompt(str(video_path), text_prompt, max_clips)
            
            if not result or not result.get("clips"):
                return {
                    "status": "error",
                    "message": result.get("message", "No clips were generated"),
                    "clips": []
                }
            
            # Generate URLs for the output videos
            clips_with_urls = []
            for clip in result["clips"]:
                output_filename = os.path.basename(clip["path"])
                clip_url = f"/uploads/clips/{output_filename}"
                
                clips_with_urls.append({
                    "clipUrl": clip_url,
                    "viralityScore": clip["virality_score"],
                    "startTime": clip["start_time"],
                    "endTime": clip["end_time"],
                    "duration": clip["duration"]
                })
            
            # Sort clips by virality score in descending order
            clips_with_urls.sort(key=lambda x: x['viralityScore'], reverse=True)
            
            return {
                "status": "success",
                "message": f"Successfully generated {len(clips_with_urls)} clips",
                "clips": clips_with_urls
            }
        except Exception as e:
            # Clean up the uploaded file if processing fails
            if os.path.exists(video_path):
                os.remove(video_path)
            raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")