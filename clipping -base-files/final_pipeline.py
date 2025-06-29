import os
import sys
import cv2
import numpy as np
import logging
import soundfile as sf
from tqdm import tqdm
from tensorflow.keras.models import load_model

# --- Import all your utility modules ---
from audio_analysis import extract_audio_ffmpeg, detect_gunshots, detect_laughter, merge_segments
from video_to_clips import find_loudest_moments
from shot_sift_updated import adjust_sample_interval, extract_frames_sequential, detect_shot_boundaries
from preprocessing_final import extract_frames, process_frames, adjust_sample_interval as preprocess_interval, determine_chunk_size

# --- New Storytelling & Image Gen Imports ---
from transcription import transcribe_video
import io
import time
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from moviepy.editor import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ----------- ACTION DETECTION CONFIG -----------
MODEL_PATH = "Model_Latest.h5" # Change to your model's filename
IMAGE_HEIGHT, IMAGE_WIDTH = 64, 64
TIMESTEPS = 10
NO_OF_CHANNELS = 3
CLASS_CATEGORIES_LIST = ["Nunchucks", "Punch"] # Edit as per your model

# ----------- 1. PREPROCESSING -----------------
def preprocess_video(video_path, tmp_dir="tmp_frames"):
    os.makedirs(tmp_dir, exist_ok=True)
    sample_interval = preprocess_interval(video_path)
    chunk_size = determine_chunk_size()
    logging.info(f"Sampling every {sample_interval} frames, batch size {chunk_size}")
    extract_frames(video_path, tmp_dir, sample_interval, downscale_factor=2, batch_size=chunk_size)
    processed_dir = tmp_dir + "_processed"
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
        pred_label = CLASS_CATEGORIES_LIST[pred_class_idx]

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

# ----------- 5. CLIP SEGMENTATION & DEDUPLICATION -----------
def merge_overlapping_clips(segments, min_time_diff=4):
    """Merges overlapping clips to avoid duplicates based on start times."""
    if not segments:
        return []

    # Segments are expected to be sorted by start time
    merged = [segments[0]]
    last_start_time = segments[0][0]

    for current_start, current_end in segments[1:]:
        if current_start - last_start_time >= min_time_diff:
            merged.append((current_start, current_end))
            last_start_time = current_start
            
    return merged


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

# ===================================================================
# ==================== NEW STORYTELLING PIPELINE ====================
# ===================================================================

# ----------- HELPER: AI IMAGE GENERATION ----------------
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

def generate_image_for_prompt(prompt, output_path):
    if not REPLICATE_API_TOKEN:
        logging.warning("REPLICATE_API_TOKEN not set. Falling back to placeholder image.")
        safe_prompt = requests.utils.quote(prompt)
        placeholder_url = f"https://via.placeholder.com/512x512.png?text={safe_prompt}"
        try:
            response = requests.get(placeholder_url)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download placeholder image: {e}")
            return None
    # (Implementation for Replicate API would go here)
    logging.info(f"Image generation for '{prompt}' completed.")
    return None # Placeholder

# ----------- HELPER: SEMANTIC ANALYSIS ----------------
def summarize_and_cluster_transcript(transcript, num_clusters=5):
    if not transcript or len(transcript) < num_clusters:
        return {0: transcript} if transcript else {}
    texts = [item['text'] for item in transcript]
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    kmeans.fit(tfidf_matrix)
    clusters = {i: [] for i in range(num_clusters)}
    for i, item in enumerate(transcript):
        clusters[kmeans.labels_[i]].append(item)
    return clusters

def select_story_clips(clusters, clips_per_cluster=2):
    selected_clips = []
    for cluster_id, segments in clusters.items():
        if not segments:
            continue
        segments.sort(key=lambda x: len(x['text']), reverse=True)
        selected_clips.extend(segments[:clips_per_cluster])
    selected_clips.sort(key=lambda x: x['start'])
    return selected_clips

# ----------- 8. STORYTELLING PIPELINE ----------------
def create_story_video(video_path, out_dir="story_output", num_topics=3, clips_per_topic=2):
    logging.info("===== Storytelling Pipeline START ====")
    os.makedirs(out_dir, exist_ok=True)

    logging.info("[1] Transcribing video...")
    transcript = transcribe_video(video_path)
    if not transcript:
        logging.error("Transcription failed. Aborting.")
        return

    logging.info("[2] Analyzing transcript...")
    clusters = summarize_and_cluster_transcript(transcript, num_clusters=num_topics)
    story_clips_info = select_story_clips(clusters, clips_per_cluster=clips_per_topic)
    if not story_clips_info:
        logging.error("Could not select story clips. Aborting.")
        return

    logging.info(f"[3] Generating story from {len(story_clips_info)} clips...")
    final_video_segments = []
    video_clip = VideoFileClip(video_path)
    for i, clip_info in enumerate(story_clips_info):
        start, end, text = clip_info['start'], clip_info['end'], clip_info['text']
        logging.info(f"  - Processing clip: '{text}'")
        
        img_path = os.path.join(out_dir, f"temp_image_{i}.png")
        generate_image_for_prompt(f"cinematic, {text}", img_path)

        if os.path.exists(img_path):
            ai_image_clip = ImageClip(img_path).set_duration(3).set_pos('center')
            txt_clip = TextClip(text, fontsize=24, color='white', bg_color='black', size=ai_image_clip.size).set_pos('center', 'bottom').set_duration(3)
            title_card = CompositeVideoClip([ai_image_clip, txt_clip])
            final_video_segments.append(title_card)

        if end > start:
            clip = video_clip.subclip(start, end)
            final_video_segments.append(clip)

    video_clip.close() # Close the main video clip

    if not final_video_segments:
        logging.error("No segments generated. Aborting.")
        return

    logging.info("[4] Stitching final video...")
    final_video = concatenate_videoclips(final_video_segments, method="compose")
    output_path = os.path.join(out_dir, "final_story_video.mp4")
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    final_video.close() # Close the final composite clip

    # Clean up individual clips
    for clip in final_video_segments:
        clip.close()

    logging.info(f"===== Storytelling Pipeline COMPLETE! Video saved to {output_path} =====")

# ----------- MAIN PIPELINE -------------------
def main_pipeline(video_path, out_dir="clips"):
    logging.info("===== Opus Clip for Gaming Videos Pipeline START =====")
    processed_frames_dir = preprocess_video(video_path, "frames")
    logging.info("[2] Running action detection...")
    action_segs = sliding_window_predict(video_path, model_path=MODEL_PATH, window=TIMESTEPS, stride=5, threshold=0.7)
    logging.info("[3] Analyzing audio...")
    audio_segs, loudest_times = audio_events(video_path)
    logging.info("[4] Detecting shot boundaries...")
    shot_times = shot_boundaries(video_path)
    logging.info("[5] Segmenting clips...")
    segments = segment_clips(action_segs, audio_segs, loudest_times, shot_times, clip_length=8)
    logging.info(f"Generated {len(segments)} initial clips. Merging duplicates...")
    segments = merge_overlapping_clips(segments, min_time_diff=4) # clip_length/2
    logging.info(f"Reduced to {len(segments)} unique clips.")

    logging.info("[6] Ranking clip virality...")
    ranked = rank_virality(segments, action_segs, audio_segs)
    logging.info("[7] Saving top 20 clips...")
    save_top_clips(video_path, ranked, out_dir=out_dir, top_n=20, clip_length=8)
    logging.info("===== Pipeline COMPLETE! Top clips are saved. =====")

# ----------- ENTRY POINT ---------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python final_pipeline.py <pipeline_type> <path_to_video.mp4> [output_dir]")
        print("  pipeline_type: 'clips' or 'story'")
        sys.exit(1)

    pipeline_type = sys.argv[1]
    video_path = sys.argv[2]
    out_dir = sys.argv[3] if len(sys.argv) > 3 else None

    if pipeline_type == 'clips':
        main_pipeline(video_path, out_dir=out_dir or "clips")
    elif pipeline_type == 'story':
        create_story_video(video_path, out_dir=out_dir or "story_output")
    else:
        print(f"Error: Unknown pipeline type '{pipeline_type}'. Choose 'clips' or 'story'.")
        sys.exit(1)
