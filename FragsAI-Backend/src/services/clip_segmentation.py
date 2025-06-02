import os
import cv2
import numpy as np
import ffmpeg
import moviepy.editor as mp
import logging
from tqdm import tqdm
from celery_app.job_manager import Job

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def detect_motion(video_path, job: Job, segment_duration=60, fps_threshold=10):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 1.0
    frame_skip = max(1, int(fps / fps_threshold))

    prev_frame = None
    motion_scores = {}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    duration = total_frames / fps
    total_segments = int(duration // segment_duration)

    logging.info(f"Analyzing motion across {total_segments} segments...")

    if total_segments <= 0:
        job.set_motion_progress(100)
        cap.release()
        return motion_scores

    for segment_idx in tqdm(range(total_segments), desc="Detecting motion", leave=False):
        job.set_motion_progress(round(segment_idx / total_segments * 100))

        start_frame = int(segment_idx * segment_duration * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        motion_detected = 0
        checks_per_segment = int((segment_duration * fps) / frame_skip)
        for _ in range(checks_per_segment):
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            if prev_frame is not None:
                frame_diff = cv2.absdiff(prev_frame, gray)
                motion_score = np.sum(frame_diff) / (frame_diff.size + 1e-8)
                if motion_score > 10:
                    motion_detected += 1

            prev_frame = gray

        if motion_detected > 0:
            motion_scores[segment_idx] = motion_detected

    # Finalize motion progress
    job.set_motion_progress(100)
    cap.release()
    return motion_scores


def segment_video_and_audio(video_path, output_dir, job: Job, segment_duration=60, max_segments=30):
    if not os.path.exists(video_path):
        logging.error(f"Video file {video_path} not found.")
        job.set_status("completed")
        return

    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error("Failed to open video file.")
        job.set_status("completed")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

    if fps <= 0 or total_frames <= 0:
        logging.error("Invalid video file or unreadable metadata.")
        cap.release()
        job.set_status("completed")
        return

    duration = total_frames / fps
    total_segments = int(duration // segment_duration)

    if total_segments == 0:
        logging.warning("Video too short to segment. Skipping.")
        cap.release()
        job.set_status("completed")
        return

    motion_scores = detect_motion(video_path, job, segment_duration)

    if not motion_scores:
        logging.warning("No motion detected in any segments. Exiting.")
        cap.release()
        job.set_status("completed")
        return

    sorted_segments = sorted(
        motion_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    selected_segments = [seg_idx for seg_idx, _ in sorted_segments[:max_segments]]

    video_output_dir = os.path.join(output_dir, "videos")
    audio_output_dir = os.path.join(output_dir, "audios")
    os.makedirs(video_output_dir, exist_ok=True)
    os.makedirs(audio_output_dir, exist_ok=True)

    logging.info(f"Processing {len(selected_segments)} action-rich segments…")

    segment_count = 0
    total_to_process = len(selected_segments)

    for seg_index in selected_segments:
        job.set_video_progress(round(segment_count / total_to_process * 100))

        start_time = seg_index * segment_duration
        output_video_path = os.path.join(
            video_output_dir,
            f"{video_filename}_segment_{segment_count + 1}.mp4"
        )
        output_audio_path = os.path.join(
            audio_output_dir,
            f"{video_filename}_segment_{segment_count + 1}.mp3"
        )

        (
            ffmpeg
            .input(video_path, ss=start_time, t=segment_duration)
            .output(output_video_path, vcodec="libx264", acodec="aac")
            .run(overwrite_output=True)
        )

        video_clip = mp.VideoFileClip(output_video_path)
        video_clip.audio.write_audiofile(output_audio_path, codec="mp3")
        video_clip.close()

        logging.info(f"Saved segment {segment_count + 1}: {output_video_path}")
        segment_count += 1

    cap.release()

    logging.info(
        f"Completed video segmentation. Total segments created: {segment_count}"
    )

    job.set_video_progress(100)
    job.set_status("completed")
