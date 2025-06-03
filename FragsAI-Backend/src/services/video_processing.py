import os
import logging
from celery_app.app import celery
from celery.utils.log import get_task_logger
from config import settings
from celery_app.job_manager import manager
from services.clip_segmentation import segment_video_and_audio
from services.transfer import transfer_clips_to_backend

logger = get_task_logger(__name__)

@celery.task(bind=True)
def process_and_update_video(self, job_id: str, path: str):
    if not manager.exists(job_id):
        manager.add_job(job_id)
    job = manager.get_job(job_id)

    segment_video_and_audio(path, settings.DOWNLOAD_FOLDER, job)
    self.update_state(state="PROGRESS", meta=job.get_JSON())

    output_dir = os.path.join(settings.DOWNLOAD_FOLDER, "videos")
    response = transfer_clips_to_backend(output_dir, job)

    manager.remove_job(job_id)
    logger.info(f"Completed job {job_id}; removed from manager.")
    return response.json()
