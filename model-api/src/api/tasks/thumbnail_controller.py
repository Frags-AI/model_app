from core.thumbnail import (
    select_best_frame, generate_thumbnail_background,
    generate_dalle3_thumbnail, generate_from_sketch,
    generate_thumbnail_overlays, add_text_and_icon
)
from config import settings
import os
from uuid import uuid4
from celery_app.app import celery
from clients.aws import s3_service


"""
Mode 1: Generate thumbnail from Clip
Mode 2: Generate thumbnail using ChatGPT
Mode 3: Generate thumbnail with Sketch + Prompt
"""

@celery.task(bind=True)
def thumbnail_generator(self, mode: int, s3_key: str = None, prompt: str = None, text: str = None):

    thumbnail_path: str = None
    file_name = f"{uuid4()}_thumbnail.png"
    input_path: str = os.path.join(settings.UPLOAD_FOLDER, "thumbnails", file_name)

    if s3_key: s3_service.download_file(s3_key, input_path)

    if mode == 1:
        download_path = os.path.join(settings.DOWNLOAD_FOLDER, "thumbnails", file_name)
        video_path, frame_idx = select_best_frame(input_path)
        thumbnail_path, size = generate_thumbnail_background(video_path, download_path, time_sec=frame_idx / 30)
        
        if text:
            text_opts, icon_opts = generate_thumbnail_overlays(text, size)
            thumbnail_path = add_text_and_icon(thumbnail_path, text_opts, icon_opts)
    
    elif mode == 2:
        output_path = os.path.join(settings.DOWNLOAD_FOLDER, "thumbnails", "dalle_prompt.jpg")
        thumbnail_path = generate_dalle3_thumbnail(prompt, output_path)

    elif mode == 3:
        download_path = os.path.join(settings.DOWNLOAD_FOLDER, "thumbnails", file_name)
        thumbnail_path = generate_from_sketch(input_path, prompt, download_path)

    return thumbnail_path


