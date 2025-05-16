from fastapi import APIRouter
from api import video, thumbnail

router = APIRouter()

router.include_router(video.router, prefix="/video", tags=["Video"])
router.include_router(thumbnail.router, prefix="/thumbnail", tags=["Thumbnail"])