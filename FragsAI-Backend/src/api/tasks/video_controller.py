import os
import logging
from celery_app.app import celery
from celery.utils.log import get_task_logger
from config import settings
from celery_app.job_manager import manager
from core.clip_segmentation import segment_video_and_audio
from core.transfer import transfer_clips_to_backend
from werkzeug.utils import secure_filename

logger = get_task_logger(__name__)

@celery.task(bind=True)
def process_and_update_video(self, video_bytes: bytes, filename: str):
    job_id: str = self.request.id

    filename = secure_filename(filename)
    save_path = os.path.join(settings.UPLOAD_FOLDER, "videos", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Save uploaded video content
    with open(save_path, "wb") as f:
        f.write(video_bytes)

    # Track progress via job manager
    if not manager.exists(job_id):
        manager.add_job(job_id)
    job = manager.get_job(job_id)

    self.update_state(state="PROGRESS", meta=job.get_JSON())

    segment_video_and_audio(save_path, settings.DOWNLOAD_FOLDER, job)

    self.update_state(state="SUCCESS", meta=job.get_JSON())
    output_dir = os.path.join(settings.DOWNLOAD_FOLDER, "videos")

    url = f"{settings.API_URL}/api/model/project"
    payload = {
        "task_id": job.get_id(),
        "status": job.get_status()
    }
    response = transfer_clips_to_backend(url, output_dir, payload)
    manager.remove_job(job_id)
    
    return response