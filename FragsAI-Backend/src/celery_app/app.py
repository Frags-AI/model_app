from celery import Celery
from config import settings

app = Celery(
    "clipping_project",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
        include=["services.video_processing"]
)

app.conf.task_routes = {
    'services.video_processing.process_and_update_video': {'queue': 'videos'},
}