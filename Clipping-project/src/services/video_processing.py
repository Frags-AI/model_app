import os
from config import settings
from models.job_manager import manager
from services.transfer import transfer_clips_to_backend
from services.clip_segmentation import segment_video_and_audio
from fastapi.responses import JSONResponse

def process_and_update_video(job_id, path):
    if not manager.exists(job_id):
        manager.add_job(job_id)
        job = manager.get_job(job_id)

        segment_video_and_audio(path, settings.download_folder, job)
        path = os.path.join(settings.download_folder, "videos")

        response = transfer_clips_to_backend(path, job)
        manager.remove_job(job_id)
        data = response.json()
        return JSONResponse(data)