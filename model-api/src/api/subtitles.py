from fastapi import APIRouter,UploadFile,File
from fastapi.responses import JSONResponse
from .tasks.subtitles_controller import process_clip_subtitles
from clients.aws import s3_service
router = APIRouter()

@router.post("/clip/")
async def add_subtitles(file: UploadFile=File(...)):
    s3_key = s3_service.generate_s3_key(file.filename)
    s3_url = s3_service.upload_file(file.file, s3_key)

    task = process_clip_subtitles.delay(s3_key, file.filename)

    return JSONResponse({"task_id": task.id, "s3_url": s3_url}, 200)