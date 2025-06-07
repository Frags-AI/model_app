from fastapi import APIRouter
from fastapi.responses import JSONResponse
from core.editing import edit_video

router=APIRouter()

@router.post('/edit_video/')
def edit_video(clip_url: str, soundtrack_url: str = None, title: str = "Gaming Stream Clip", resolution: str = "hd", length: int = 10):
    result=edit_video(clip_url,soundtrack_url,title,resolution,length)
    return JSONResponse(result)