from services.thumbnail import (
    select_best_frame, generate_thumbnail_background,
    generate_dalle3_thumbnail, generate_from_sketch,
    generate_thumbnail_overlays, add_text_and_icon
)
from config import settings
from fastapi import UploadFile
import os
import logging

"""
Mode 1: Generate thumbnail from Clip
Mode 2: Generate thumbnail using ChatGPT
Mode 3: Generate thumbnail with Sketch + Prompt
"""

os.makedirs(os.path.join(settings.upload_folder, "thumbnails"), exist_ok=True)
os.makedirs(os.path.join(settings.download_folder, "thumbnails"), exist_ok=True)

def thumbnail_generator(mode: int, file: UploadFile = None, prompt: str = None, text: str = None):
    thumbnail_path = None
    upload_path = os.path.join(settings.upload_folder, "thumbnails")
    download_path = os.path.join(settings.download_folder, "thumbnails")

    if mode == 1:
        temp_path = os.path.join(upload_path, file.filename)
        with open(temp_path, "wb") as f:
            f.write(file.file.read())

        video_path, frame_idx = select_best_frame(temp_path)
        thumbnail_path = generate_thumbnail_background(video_path, download_path, time_sec=frame_idx / 30)
        
        if text is not None:
            text_opts, icon_opts = generate_thumbnail_overlays(prompt)
            thumbnail_path = add_text_and_icon(thumbnail_path, text_opts, icon_opts)
    
    elif mode == 2:
        output_path = os.path.join(download_path, "dalle_prompt.jpg")
        thumbnail_path = generate_dalle3_thumbnail(output_path, text_opts, icon_opts)

    elif mode == 3:
        temp_path = os.path.join(upload_path, file.filename)
        with open(temp_path, "wb") as f:
            file.write(file.file.read())

        output_path = os.path.join(download_path, "sketch_generated.jpg")
        thumbnail_path = generate_from_sketch(temp_path, prompt, output_path)


