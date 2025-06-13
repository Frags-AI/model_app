from celery_app.app import celery
import os
from config import settings
from core.subtitles import (
    transcribe,extract_audio,generate_subtitle_file,
    add_subtitle_to_video,
)
from core.transfer import transfer_clips_to_backend
from celery_app.job_manager import manager
import uuid
from clients.aws import s3_service

@celery.task(bind=True)
def process_clip_subtitles(self, s3_key: str, filename: str) -> str:
    video_path = os.path.join(settings.UPLOAD_FOLDER, "videos", f"{uuid.uuid4()}_{filename}")

    s3_service.download_file(s3_key, video_path)

    if not manager.exists(self.request.id):
        manager.add_job(self.request.id)

    self.update_state(state="PROGRESS", meta={"step": "Audio extraction"})
    audio_path = extract_audio(video_path)

    self.update_state(state="PROGRESS", meta={"step": "Transcribing audio"})
    language, segments = transcribe(audio_path)

    self.update_state(state="PROGRESS", meta={"step": "Generating subtitles"})
    subtitle_file = generate_subtitle_file(language, segments, video_path)

    self.update_state(state="PROGRESS", meta={"step": "Overlaying subtitles"})
    output_video_path = add_subtitle_to_video(video_path, subtitle_file, audio_path, font='Ariel', color='Red')

    self.update_state(state="SUCCESS", meta={"step": "Done", "output_path": output_video_path})

    data = { "task_id": self.request.id, "state": "SUCCESS" }
    url = f"{settings.API_URL}/api/model/subtitles"

    data = transfer_clips_to_backend(url, output_video_path, data)
    manager.remove_job(self.request.id)
    
    return data
    