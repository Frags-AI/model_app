from celery_app.app import celery
from fastapi import UploadFile
import os
from core.pipeline.pipeline import main_pipeline
from core.transfer import transfer_clips_to_backend
import logging
from config import settings
from clients.aws import s3_service

@celery.task(bind=True)
def create_video_pipeline(self, s3_key: str, filename: str):
    
    def update_progress(stage: str, progress: int):
        self.update_state(state="PROGRESS", meta={"stage": stage, "progress": progress})

    input_path = os.path.join(settings.UPLOAD_FOLDER, "videos", filename)
    s3_service.download_file(s3_key, input_path)
    output_path = os.path.join(settings.DOWNLOAD_FOLDER, "clips")

    output_folder = main_pipeline(input_path, output_path, update_progress)
    self.update_state(state="SUCCESS", meta={"stage": "Finalizing Changes", "progress": 100})

    url = f"{settings.API_URL}/api/model/project"
    data = { "task_id": self.request.id, "status": "SUCCESS" }
    
    data = transfer_clips_to_backend(url, output_folder, data)
    logging.info(data["message"])
    return data