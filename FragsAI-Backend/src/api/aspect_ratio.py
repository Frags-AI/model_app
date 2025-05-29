from fastapi import APIRouter,UploadFile,File
from fastapi.responses import JSONResponse
from config import settings
from services.aspect_ratio import enhance_video_aspect_ratio
router=APIRouter()

@router.post('/aspect_ratio/')
def adjust_aspect_ratio(file:UploadFile=File(...)):
    input_video_path=f"{settings.upload_folder}/{file.filename}"
    with open(input_video_path,"wb") as f:
        f.write(file.read())
    
    output_video_path=enhance_video_aspect_ratio(input_video_path,"./processed_videos")
    if output_video_path:
        return JSONResponse({"output_video":output_video_path})
    else:
        return JSONResponse({"error":"Aspect ratio enhancement failed"})