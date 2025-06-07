from celery import Celery
from config import settings

celery = Celery(__name__)
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND
celery.autodiscover_tasks(["api.services"])

from api.tasks import (
    subtitles_controller,
    thumbnail_controller
)
