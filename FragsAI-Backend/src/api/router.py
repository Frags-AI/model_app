from fastapi import APIRouter
from api import video, thumbnail, aspect_ratio, editing, subtitles, clip_anything
from api import voiceover, script, transcription, background

router = APIRouter()

router.include_router(video.router, prefix="/video", tags=["Video"])
router.include_router(thumbnail.router, prefix="/thumbnail", tags=["Thumbnail"])
router.include_router(aspect_ratio.router, prefix="/aspect_ratio", tags=["Aspect_ratio"])
router.include_router(editing.router, prefix="/editing", tags=["Editing"])
router.include_router(subtitles.router, prefix="/subtitles", tags=["Subtitles"])
router.include_router(clip_anything.router, prefix="/clip_anything", tags=["Clip_anything"])

# Add new feature routers
router.include_router(voiceover.router, prefix="/voiceover", tags=["Voiceover"])
router.include_router(script.router, prefix="/script", tags=["Script"])
router.include_router(transcription.router, prefix="/transcription", tags=["Transcription"])
router.include_router(background.router, prefix="/background", tags=["Background"])