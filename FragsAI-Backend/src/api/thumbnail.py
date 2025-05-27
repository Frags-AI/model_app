from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from .services.thumbnail_controller import thumbnail_generator
from typing import Annotated

router = APIRouter()

@router.post("/generate/")
def generate_thumbnail(mode: Annotated[int, Form(...)], file: Annotated[UploadFile, File(...)] = None, prompt: Annotated[str, Form(...)] = None, text: Annotated[str, Form(...)] = None):

    if None == file == prompt == text:
        return JSONResponse({"error": "Please pass in parameters"})

    path = thumbnail_generator(mode, file, prompt, text)
    return JSONResponse({"path": path})