from fastapi import APIRouter,UploadFile,File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from config import settings
from services.aspect_ratio import enhance_video_aspect_ratio
import os
router=APIRouter()

@router.post('')
async def adjust_aspect_ratio(ratio: str = Form(...), file: UploadFile = File(...)):
    input_video_path = os.path.join(settings.upload_folder, "videos", file.filename)
    output_folder_path = os.path.join(settings.download_folder, "videos")

    ratio_mapping = {"9:16": 9/16, "16:9": 16/9, "1:1": 1}

    # Save uploaded video to disk
    with open(input_video_path, "wb") as f:
        f.write(await file.read())

    # Process the video
    output_video_path = enhance_video_aspect_ratio(input_video_path, output_folder_path, ratio_mapping[ratio])

    if output_video_path and os.path.exists(output_video_path):
        return StreamingResponse(
            open(output_video_path, "rb"),
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename=processed_{file.filename}"}
        )
    else:
        return JSONResponse({"error": "Aspect ratio enhancement failed"}, status_code=400)