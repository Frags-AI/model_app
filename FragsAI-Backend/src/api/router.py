from fastapi import APIRouter
from api import video, thumbnail,aspect_ratio,editing,subtitles,background,transcription,voiceover,virality_ranking

router = APIRouter()

router.include_router(video.router, prefix="/video", tags=["Video"])
router.include_router(thumbnail.router, prefix="/thumbnail", tags=["Thumbnail"])
router.include_router(aspect_ratio.router,prefix="/aspect_ratio",tags=["Aspect_ratio"])
router.include_router(editing.router,prefix="/editing",tags=["Editing"])
router.include_router(subtitles.router,prefix="/subtitles",tags=["Subtitles"])
router.include_router(background.router, prefix="/background", tags=["Background"])
router.include_router(transcription.router, prefix="/transcription", tags=["Transcription"])
router.include_router(voiceover.router, prefix="/voiceover", tags=["Voiceover"])
router.include_router(virality_ranking.router, prefix="/virality_ranking", tags=["Virality_ranking"])