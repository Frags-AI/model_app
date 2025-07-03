from celery_app.app import celery
import os
from core.pipeline.pipeline import main_pipeline
from core.pipeline.semantic_story import semantic_pipeline
from core.transfer import transfer_clips_to_backend
import logging
from config import settings
from uuid import uuid4
from clients.aws import s3_service
from clients.filesystem import StorageSystem

@celery.task(bind=True)
def create_video_pipeline(self, s3_key: str, filename: str):
    
    def update_progress(stage: str, progress: int, state: str = "PROGRESS"):
        self.update_state(state=state, meta={"stage": stage, "progress": progress, "state": state})

    storage_system = StorageSystem()

    input_path = storage_system.create_upload_path("videos", filename)
    s3_service.download_file(s3_key, input_path)

    output_folder = main_pipeline(input_path, storage_system, update_progress)
    self.update_state(state="SUCCESS", meta={"stage": "Finalizing Changes", "progress": 100, "state": "COMPLETE"})

    url = f"{settings.API_URL}/api/model/project"
    data = { "task_id": self.request.id, "status": "SUCCESS" }
    
    data = transfer_clips_to_backend(url, output_folder, data)

    logging.info(data["message"])
    return data

@celery.task(bind=True)
def create_semantic_video_pipeline(self, s3_key: str, prompt: str, filename: str):
    def update_progress(stage: str, progress: int, state: str = "PROGRESS"):
        self.update_state(state=state, meta={"stage": stage, "progress": progress, "state": state})

    storage_system = StorageSystem()

    input_path = storage_system.create_upload_path("videos", filename)
    s3_service.download_file(s3_key, input_path)

    output_folder = semantic_pipeline(input_path, storage_system, update_progress)
    self.update_state(state="SUCCESS", meta={"stage": "Finalizing Changes", "progress": 100, "state": "COMPLETE"})

    url = f"{settings.API_URL}/api/model/project"
    data = { "task_id": self.request.id, "status": "SUCCESS" }
    
    data = transfer_clips_to_backend(url, output_folder, data)

    logging.info(data["message"])
    return data