from fastapi import APIRouter
from api import video, thumbnail,aspect_ratio,editing,subtitles

router = APIRouter()

router.include_router(video.router, prefix="/video", tags=["Video"])
router.include_router(thumbnail.router, prefix="/thumbnail", tags=["Thumbnail"])
router.include_router(aspect_ratio.router,prefix="/aspect_ratio",tags=["Aspect_ratio"])
router.include_router(editing.router,prefix="/editing",tags=["Editing"])
router.include_router(subtitles.router,prefix="/subtitles",tags=["Subtitles"])