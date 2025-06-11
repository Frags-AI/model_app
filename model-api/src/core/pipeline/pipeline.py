import os
import cv2
import numpy as np
import logging
import soundfile as sf
from tensorflow.keras.models import load_model

# --- Import all your utility modules ---
from .audio_analysis import extract_audio_ffmpeg, detect_gunshots, detect_laughter, merge_segments
from .video_to_clips import find_loudest_moments
from .shot_sift import adjust_sample_interval, extract_frames_sequential, detect_shot_boundaries
from .preprocessing import extract_frames, process_frames, adjust_sample_interval as preprocess_interval, determine_chunk_size
from config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ----------- ACTION DETECTION CONFIG -----------
MODEL_PATH = os.path.abspath(os.path.join("models", "pretrained", "MODEL.h5"))
IMAGE_HEIGHT, IMAGE_WIDTH = 64, 64
TIMESTEPS = 10
NO_OF_CHANNELS = 3
CLASS_CATEGORIES_LIST = ["Nunchucks", "Punch"] # Edit as per your model
NUM_CLASSES = len(CLASS_CATEGORIES_LIST)

# ----------- 1. PREPROCESSING -----------------
def preprocess_video(video_path, tmp_dir=os.path.join(settings.DOWNLOAD_FOLDER, "frames")):
    os.makedirs(tmp_dir, exist_ok=True)
    sample_interval = preprocess_interval(video_path)
    chunk_size = determine_chunk_size()
    logging.info(f"Sampling every {sample_interval} frames, batch size {chunk_size}")
    extract_frames(video_path, tmp_dir, sample_interval, downscale_factor=2, batch_size=chunk_size)
    processed_dir = tmp_dir + "_processed"
    os.makedirs(processed_dir, exist_ok=True)
    process_frames(tmp_dir, processed_dir, resize_dim=(IMAGE_HEIGHT, IMAGE_WIDTH), augment=False)
    return processed_dir

# ----------- 2. ACTION DETECTION (INFERENCE) ---------
def sliding_window_predict(video_path, model_path=MODEL_PATH, window=TIMESTEPS, stride=5, threshold=0.7):
    model = load_model(model_path)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = []
    timestamps = []
    segments = []
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (IMAGE_HEIGHT, IMAGE_WIDTH))
        frame = frame.astype(np.float32) / 255.0
        frames.append(frame)
        idx += 1

    cap.release()

    if len(frames) < window:
        return []

    frames = np.array(frames)
    for i in range(0, len(frames) - window + 1, stride):
        clip = frames[i:i+window]
        if clip.shape[0] < window:
            continue
        input_clip = np.expand_dims(clip, axis=0)
        preds = model.predict(input_clip)
        pred_class_idx = np.argmax(preds)
        pred_score = float(np.max(preds))
        pred_label = CLASS_CATEGORIES_LIST[pred_class_idx] if 0 <= pred_class_idx < NUM_CLASSES else None

        if pred_score >= threshold:
            start_sec = i / fps
            end_sec = (i+window) / fps
            segments.append((start_sec, end_sec, pred_label, pred_score))
    return segments

# ----------- 3. AUDIO ANALYSIS --------------
def audio_events(video_path):
    audio_path = extract_audio_ffmpeg(video_path)
    gunshots = detect_gunshots(audio_path)
    laughs = detect_laughter(audio_path)
    merged = merge_segments(gunshots, laughs)
    audio, sr = sf.read(audio_path)
    loudest = find_loudest_moments(audio, sr, num_clips=30, clip_length=5)
    return merged, loudest

# ----------- 4. SHOT BOUNDARY ---------------
def shot_boundaries(video_path):
    frame_skip = adjust_sample_interval(video_path)
    frames, frame_indices = extract_frames_sequential(video_path, frame_skip)
    if not frames or not frame_indices:
        return []
    shots = detect_shot_boundaries(frames, method='orb', match_threshold=30.0)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    to_sec = lambda idx: idx / fps
    shot_times = [to_sec(frame_indices[i]) for i in shots]
    return shot_times

# ----------- 5. CLIP SEGMENTATION -----------
def segment_clips(action_segs, audio_segs, loudest_times, shot_times, clip_length=8):
    starts = set()
    for (start, end, *_ ) in action_segs:
        starts.add(int(start))
    for (start, end) in audio_segs:
        starts.add(int(start))
    for t in loudest_times:
        starts.add(int(t))
    for t in shot_times:
        starts.add(int(t))
    starts = sorted(list(starts))
    segments = [(start, start + clip_length) for start in starts]
    return segments

# ----------- 6. VIRALITY RANKING ------------
def rank_virality(segments, action_segs, audio_segs):
    ranked = []
    for (start, end) in segments:
        score = 0
        score += sum(1 for (s, e, *_ ) in action_segs if s < end and e > start) * 2
        score += sum(1 for (s, e) in audio_segs if s < end and e > start)
        ranked.append((start, end, score))
    ranked.sort(key=lambda x: x[2], reverse=True)
    return ranked

# ----------- 7. SAVE CLIPS ------------------
def save_top_clips(video_path, ranked_segments, out_dir="clips", top_n=20, clip_length=8):
    os.makedirs(out_dir, exist_ok=True)
    for i, (start, end, score) in enumerate(ranked_segments[:top_n]):
        out_file = os.path.join(out_dir, f"clip_{i+1}_{start:.2f}_{end:.2f}_score{score}.mp4")
        cmd = (
            f'ffmpeg -ss {start} -i "{video_path}" -t {clip_length} -c copy -avoid_negative_ts make_zero -y "{out_file}"'
        )
        os.system(cmd)
        logging.info(f"✅ Saved: {out_file} (score: {score})")

# ----------- MAIN PIPELINE -------------------
def main_pipeline(video_path, output_folder="clips", progress_callback=None):
    logging.info("===== Opus Clip for Gaming Videos Pipeline START =====")

    # if progress_callback: progress_callback("Preprocessing video", 5)
    # processed_frames_dir = preprocess_video(video_path)

    if progress_callback: progress_callback("Running action detection", 20)
    action_segs = sliding_window_predict(video_path, model_path=MODEL_PATH, window=TIMESTEPS, stride=5, threshold=0.7)

    if progress_callback: progress_callback("Analyzing audio", 30)
    audio_segs, loudest_times = audio_events(video_path)

    if progress_callback: progress_callback("Detecting shot boundaries", 45)
    shot_times = shot_boundaries(video_path)

    if progress_callback: progress_callback("Segmenting clips", 80)
    segments = segment_clips(action_segs, audio_segs, loudest_times, shot_times, clip_length=8)

    if progress_callback: progress_callback("Ranking virality", 85)
    ranked = rank_virality(segments, action_segs, audio_segs)

    if progress_callback: progress_callback("Saving top 20 clips", 95)
    save_top_clips(video_path, ranked, out_dir=output_folder, top_n=20, clip_length=8)

    if progress_callback: progress_callback("Pipeline complete", 100, "SUCCESS")
    logging.info("===== Pipeline COMPLETE! Top clips are saved. =====")
    return output_folder




