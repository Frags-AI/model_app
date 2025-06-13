from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
from .tasks.thumbnail_controller import thumbnail_generator
from clients.aws import s3_service

router = APIRouter()

@router.post("/generate/")
def generate_thumbnail(mode: int, file: UploadFile = None, prompt: str = None, text: str = None):

    if None == file == prompt == text:
        return JSONResponse({"error": "Please pass in parameters"})
    
    s3_key = None
    s3_url = None
    if file:
        s3_key = s3_service.generate_s3_key(file.filename)
        s3_url = s3_service.upload_file(file.file, s3_key)

    task = thumbnail_generator(mode, s3_key, prompt, text)
    return JSONResponse({"task_id": task.id, "s3_url": s3_url})