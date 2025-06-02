import os
import sys
import cv2
import numpy as np
import librosa
import subprocess
import logging
import shutil
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from tensorflow.keras.models import load_model
from scipy.stats import variation

# Constants
IMAGE_HEIGHT, IMAGE_WIDTH = 64, 64
TIMESTEPS = 10
MAX_PIXEL_VALUE = 255
NO_OF_CHANNELS = 3
FIXED_CLIP_LENGTH = 15  # seconds per clip

# --- Suppress stderr context manager ---
class suppress_stderr:
    def __enter__(self):
        self.stderr_fileno = sys.stderr.fileno()
        self.devnull = os.open(os.devnull, os.O_WRONLY)
        self.old_stderr = os.dup(self.stderr_fileno)
        os.dup2(self.devnull, self.stderr_fileno)
    def __exit__(self, exc_type, exc_val, exc_tb):
        os.dup2(self.old_stderr, self.stderr_fileno)
        os.close(self.devnull)

# --- Step 1: Extract audio ---
def extract_audio_ffmpeg(video_path, audio_path="extracted_audio.wav"):
    command = [
        "ffmpeg", "-y", "-i", video_path, "-vn",
        "-acodec", "pcm_s16le", "-ar", "22050", audio_path
    ]
    with suppress_stderr():
        subprocess.run(command)
    return audio_path

# --- Step 2: Detect gunshots & laughter ---
def detect_audio_events(audio_path, sr=22050, gunshot_threshold=0.3, laughter_threshold=0.05):
    y, sr = librosa.load(audio_path, sr=sr)
    hop_length = 512
    frame_length = 1024
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length, n_fft=frame_length)

    gunshot_times, laughter_times = [], []
    in_gunshot = in_laughter = False
    gunshot_start = laughter_start = 0

    for t, energy in zip(times, rms):
        # Gunshot detection
        if energy > gunshot_threshold and not in_gunshot:
            in_gunshot = True
            gunshot_start = t
        elif energy <= gunshot_threshold and in_gunshot:
            in_gunshot = False
            gunshot_times.append((gunshot_start, t))

        # Laughter detection
        if energy > laughter_threshold and not in_laughter:
            in_laughter = True
            laughter_start = t
        elif energy <= laughter_threshold and in_laughter:
            in_laughter = False
            laughter_times.append((laughter_start, t))

    return gunshot_times, laughter_times

# --- Step 3: Extract frames for model ---
def extract_frames(video_path):
    frames_list = []
    with suppress_stderr():
        videoObj = cv2.VideoCapture(video_path)
        if not videoObj.isOpened():
            logging.error(f"Cannot open video file: {video_path}")
            return np.zeros((TIMESTEPS, IMAGE_HEIGHT, IMAGE_WIDTH, NO_OF_CHANNELS))
        frame_count = 0
        while True:
            success, image = videoObj.read()
            if not success:
                logging.info(f"Finished reading frames at count: {frame_count}")
                break
            resized_frame = cv2.resize(image, (IMAGE_HEIGHT, IMAGE_WIDTH))
            normalized_frame = resized_frame / MAX_PIXEL_VALUE
            frames_list.append(normalized_frame)
            frame_count += 1
            if frame_count > 1000:  # safety stop after 1000 frames
                logging.warning("Read 1000 frames, stopping to avoid infinite loop.")
                break
        videoObj.release()

    while len(frames_list) < TIMESTEPS and len(frames_list) > 0:
        frames_list.append(frames_list[-1])
    return np.zeros((TIMESTEPS, IMAGE_HEIGHT, IMAGE_WIDTH, NO_OF_CHANNELS)) if not frames_list else np.array(frames_list[:TIMESTEPS])

# --- Step 4: Load action model ---
def load_action_model(model_path):
    return load_model(model_path)

# --- Step 5: Detect actions in video ---
def detect_actions(video_path, model, action_threshold=0.5):
    logging.info("Detecting actions")
    frames = extract_frames(video_path)
    if frames.shape[0] < TIMESTEPS:
        logging.warning(f"Not enough frames ({frames.shape[0]}) for action detection")
        return []
    input_data = frames.reshape(1, TIMESTEPS, IMAGE_HEIGHT, IMAGE_WIDTH, NO_OF_CHANNELS)
    logging.info(f"Input data shape: {input_data.shape}")
    predictions = model.predict(input_data, verbose=0)
    logging.info(f"Predictions: {predictions}")
    predicted_class = np.argmax(predictions, axis=1)[0]
    confidence = predictions[0][predicted_class]
    if confidence >= action_threshold:
        fps = 30
        return [(0, TIMESTEPS / fps)]
    return []
# --- Step 6: Merge overlapping segments ---
def merge_segments(audio_segments, video_segments, merge_threshold=0.5):
    segments = audio_segments + video_segments
    segments.sort(key=lambda x: x[0])
    if not segments:
        return []
    merged = [segments[0]]
    for current in segments[1:]:
        last = merged[-1]
        if current[0] <= last[1] + merge_threshold:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

# --- Step 7: Extract & save clips using ffmpeg ---
def ffmpeg_extract_clip(input_path, start, output_path):
    clip_duration = FIXED_CLIP_LENGTH
    cmd = [
        "ffmpeg", "-ss", str(start), "-i", input_path, "-t", str(clip_duration),
        "-c", "copy", "-avoid_negative_ts", "make_zero", "-y", output_path
    ]
    with suppress_stderr():
        subprocess.run(cmd)
    return output_path


def batch_predict(model, frames_list):
    # frames_list: list of np.arrays shaped (TIMESTEPS, H, W, C)
    batch = np.stack([f.reshape(TIMESTEPS, IMAGE_HEIGHT, IMAGE_WIDTH, NO_OF_CHANNELS) for f in frames_list])
    preds = model.predict(batch, verbose=0)
    return preds


# --- Find loudest moments ---
def find_loudest_moments(audio, sr, num_clips=15, clip_length=FIXED_CLIP_LENGTH):
    hop = int(sr * clip_length)
    rms_vals = [np.sqrt(np.mean(audio[i*hop:(i+1)*hop]**2)) for i in range(len(audio) // hop)]
    if not rms_vals or np.all(np.array(rms_vals) == 0):
        print("❌ No loud segments detected.")
        return []
    loudest_indices = np.argsort(rms_vals)[-num_clips:]
    return sorted([i * clip_length for i in loudest_indices])

# --- Calculate brightness and blur ---
def compute_quality_metrics(frames):
    brightness_vals = []
    blur_vals = []

    for frame in frames:
        gray = cv2.cvtColor((frame * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        brightness_vals.append(np.mean(gray))
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_vals.append(1 / (laplacian_var + 1e-5))  # invert: higher laplacian var = sharper

    mean_brightness = np.mean(brightness_vals)
    mean_blur = np.mean(blur_vals)

    return mean_brightness, mean_blur

# --- Calculate virality score ---
def calculate_virality(predictions, quality_metrics):
    mean_confidence = np.mean(np.max(predictions, axis=1))
    variance_confidence = variation(np.max(predictions, axis=1))
    low_confidence_penalty = np.sum(np.max(predictions, axis=1) < 0.5)

    mean_brightness, mean_blur = quality_metrics

    score = (mean_confidence * 100) - (variance_confidence * 10) - (low_confidence_penalty * 5)
    score += mean_brightness * 0.01
    score -= mean_blur * 0.01

    return score

# --- Compute clip virality score with updated scoring ---
def compute_clip_score(args):
    clip_path, start, end, gunshot_segments, laughter_segments, loud_segments, model = args

    try:
        frames = extract_frames(clip_path)
        if frames.shape[0] < TIMESTEPS:
            return (clip_path, 0)

        input_data = frames.reshape(1, TIMESTEPS, IMAGE_HEIGHT, IMAGE_WIDTH, NO_OF_CHANNELS)
        predictions = model.predict(input_data, verbose=0)

        quality_metrics = compute_quality_metrics(frames)

        score = calculate_virality(predictions, quality_metrics)

        # Add audio event boosts
        for gs in gunshot_segments:
            if start <= gs[0] <= end:
                score += 1.5
        for ls in laughter_segments:
            if start <= ls[0] <= end:
                score += 1.2
        for loud_time in loud_segments:
            if start <= loud_time <= end:
                score += 1.0

        return (clip_path, round(score, 3))

    except Exception as e:
        logging.warning(f"Error computing score for {clip_path}: {e}")
        return (clip_path, 0)

def pre_filter_segments(audio_path, segments, max_clips=20, sr=22050):
    y, sr = librosa.load(audio_path, sr=sr)
    scores = []
    for start, end in segments:
        start_sample = int(start * sr)
        end_sample = int(min(len(y), end * sr))
        segment_audio = y[start_sample:end_sample]
        if len(segment_audio) == 0:
            score = 0
        else:
            score = np.mean(np.abs(segment_audio))  # average absolute amplitude as quick proxy
        scores.append((start, end, score))
    # Sort descending by quick score and keep top max_clips
    scores.sort(key=lambda x: x[2], reverse=True)
    filtered = [(s, e) for s, e, sc in scores[:max_clips]]
    return filtered

def save_clips_parallel(video_path, segments, output_dir="clips", max_workers=8, max_clips=40, min_time_gap=1.0):
    os.makedirs(output_dir, exist_ok=True)
    results = []
    saved_starts = []

    # Sort segments by start time to ensure chronological order
    segments = sorted(segments, key=lambda x: x[0])

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        idx = 0
        for start, end in segments:
            # Check if start is sufficiently far from already saved clips
            if any(abs(start - s) < min_time_gap for s in saved_starts):
                continue  # Skip duplicate/overlapping clip

            if idx >= max_clips:
                break

            output_path = os.path.join(output_dir, f"clip_{idx+1}_{start:.2f}_{start+FIXED_CLIP_LENGTH:.2f}.mp4")
            futures.append(executor.submit(ffmpeg_extract_clip, video_path, start, output_path))
            results.append((output_path, start, start + FIXED_CLIP_LENGTH))  # metadata
            saved_starts.append(start)
            idx += 1

        for _ in tqdm(as_completed(futures), total=len(futures), desc="Saving clips"):
            pass  # progress bar, no print inside

    return results

def rank_clips_by_virality(clip_info, gunshot_segments, laughter_segments, loud_segments, model, output_path="virality_ranks.txt", max_workers=16, max_clips=40, top_clip_count=20):
    clip_info = clip_info[:max_clips]  # Score up to 40 clips

    frames_list = []
    valid_clip_info = []

    for clip_path, start, end in clip_info:
        frames = extract_frames(clip_path)
        if frames.shape[0] == TIMESTEPS:
            frames_list.append(frames)
            valid_clip_info.append((clip_path, start, end))

    predictions = batch_predict(model, frames_list)

    scores = []
    for i, (clip_path, start, end) in enumerate(valid_clip_info):
        quality_metrics = compute_quality_metrics(frames_list[i])
        score = calculate_virality(predictions[i:i+1], quality_metrics)

        # Add audio event boosts
        for gs in gunshot_segments:
            if start <= gs[0] <= end:
                score += 1.5
        for ls in laughter_segments:
            if start <= ls[0] <= end:
                score += 1.2
        for loud_time in loud_segments:
            if start <= loud_time <= end:
                score += 1.0

        scores.append((clip_path, start, end, round(score, 3)))

    # Sort descending by score
    scores.sort(key=lambda x: x[3], reverse=True)

    # Save ranks to file
    with open(output_path, "w") as f:
        for rank, (clip_path, start, end, score) in enumerate(scores, 1):
            f.write(f"{rank}. {os.path.basename(clip_path)} - Virality Score: {score}\n")

    # Copy top unique clips avoiding duplicates (based on start times close within 1 second)
    top_dir = "top_clips"
    os.makedirs(top_dir, exist_ok=True)

    copied_starts = []
    copied_count = 0
    for rank, (clip_path, start, end, score) in enumerate(scores, 1):
        # Check for duplicates by start time closeness
        if any(abs(start - cs) < 1.0 for cs in copied_starts):
            continue  # skip duplicate clips starting within 1 second of a copied clip

        base = os.path.basename(clip_path)
        new_name = f"{rank:02d}_score_{score:.3f}_{base}"
        new_path = os.path.join(top_dir, new_name)
        shutil.copy2(clip_path, new_path)

        copied_starts.append(start)
        copied_count += 1
        if copied_count >= top_clip_count:
            break

    return scores

def process_video(video_path, model_path):
    logging.info(f"Starting processing for video: {video_path}")

    audio_path = extract_audio_ffmpeg(video_path)
    logging.info(f"Audio extracted to: {audio_path}")

    gunshot_segments, laughter_segments = detect_audio_events(audio_path)
    logging.info(f"Detected {len(gunshot_segments)} gunshot and {len(laughter_segments)} laughter segments.")

    y, sr = librosa.load(audio_path, sr=22050)
    loud_segments = find_loudest_moments(y, sr, num_clips=30)
    logging.info(f"Found {len(loud_segments)} loud segments.")

    model = load_action_model(model_path)
    logging.info("Model loaded.")

    logging.info("Starting detect_actions")
    video_segments = detect_actions(video_path, model)
    logging.info(f"detect_actions returned {video_segments}")

    merged_segments = merge_segments(gunshot_segments, video_segments)
    if not merged_segments:
        logging.warning("No segments detected, falling back to loud segments.")
        merged_segments = [(start, start + FIXED_CLIP_LENGTH) for start in loud_segments]

    # Get up to 40 best segments
    merged_segments = pre_filter_segments(audio_path, merged_segments, max_clips=40)
    logging.info(f"Filtered segments to {len(merged_segments)} best candidates.")

    clip_info = save_clips_parallel(video_path, merged_segments, max_workers=8, max_clips=40)
    logging.info(f"Saved {len(clip_info)} clips.")

    # Rank clips and save top 20 unique clips
    scores = rank_clips_by_virality(
        clip_info,
        gunshot_segments,
        laughter_segments,
        loud_segments,
        model,
        max_workers=16,
        max_clips=40,
        top_clip_count=20
    )
    logging.info("Ranking completed.")
    logging.info("Processing complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    video_file = "9.mp4"  # Your video file path
    model_file = "Model___Date_Time_2024_07_13__17_00_43___Loss_0.12093261629343033___Accuracy_0.9838709831237793.h5"  # Your model path
    process_video(video_file, model_file)
