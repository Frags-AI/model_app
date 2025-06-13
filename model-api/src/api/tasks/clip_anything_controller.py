from core import clip_anything as clip
import supervision as sv
import os
from celery_app.app import celery

@celery.task(bind=True)
def process_video(video_path: str, user_text_input: str):
    video_frames_batches_dir = 'video_frames'
    video_name = os.path.splitext(os.path.basename(video_path))[0]

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

    return {
        "segments": matching_segments,
        "output_video": output_video_path
    }
