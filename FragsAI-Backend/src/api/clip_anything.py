from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .services import clip_anything_controller

router=APIRouter()

@router.post("/clip_video/")
async def clip_video(file: UploadFile = File(...), text_prompt: str = Form(...)):
    video_path = f"./uploads/{file.filename}"
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    with open(video_path, "wb") as f:
        f.write(await file.read())

    result = clip_anything_controller.process_clip_video(video_path, text_prompt)
    return JSONResponse(result)