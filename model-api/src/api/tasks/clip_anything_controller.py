from core import clip_anything as clip
import supervision as sv
import os
from celery_app.app import celery
from clients.aws import s3_service
from clients.filesystem import StorageSystem
from core.transfer import transfer_clips_to_backend
from config import settings

@celery.task(bind=True)
def process_video(s3_key: str, user_text_input: str):

    ss = StorageSystem()

    video_path = ss.create_download_path("videos", "s3_video.mp4")
    s3_service.download_file(s3_key, video_path)


    video_frames_batches_dir = ss.create_download_path("video_frames")

    sample_interval = clip.adjust_sample_interval(video_path)
    batch_size = clip.determine_chunk_size()
    video_info = sv.VideoInfo.from_video_path(video_path)

    clip.save_frames_and_indices_in_batches(
        video_path=video_path,
        total_frames=video_info.total_frames,
        batch_size=batch_size,
        base_dir=video_frames_batches_dir,
        sample_interval=sample_interval
    )

    frames_batches, frame_indices_batches = clip.fetch_frames_and_indices_from_batches(
        video_frames_batches_dir, video_path, True
    )

    matching_segments = clip.find_object_segments(
        video_path, frames_batches, frame_indices_batches, user_text_input
    )

    output_video_path = clip.edit_video(video_path, matching_segments)
    url = f"{settings.API_URL}/api/model/clip_anything"
    data = { "task_id": self.request.id, "status": "SUCCESS" }

    transfer_clips_to_backend(url, output_video_path, data)

    return {
        "segments": matching_segments,
        "output_video": output_video_path
    }
