from fastapi import APIRouter,UploadFile,File
from fastapi.responses import JSONResponse
from .tasks.subtitles_controller import process_clip_subtitles
router = APIRouter()

@router.post("/clip/")
async def add_subtitles(file: UploadFile=File(...)):
    bytes = await file.read()
    task = process_clip_subtitles.delay(bytes, file.filename)

    return JSONResponse({"task_id": task.id}, 200)