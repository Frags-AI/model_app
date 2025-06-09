import os
import numpy as np
import librosa
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import subprocess

# --- Step 1: Extract audio from video ---
from moviepy.editor import VideoFileClip
import subprocess

def extract_audio_ffmpeg(video_path, audio_path="extracted_audio.wav"):
    command = [
        "ffmpeg",
        "-y",  # overwrite output file if exists
        "-i", video_path,
        "-vn",  # no video
        "-acodec", "pcm_s16le",  # WAV PCM 16 bit
        "-ar", "22050",  # sampling rate to match librosa default (optional)
        audio_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_path


# --- Step 2: Analyze audio for gunshot sounds ---
def detect_gunshots(audio_path, sr=22050, threshold=0.3):
    print("Loading audio for gunshot detection...")
    y, sr = librosa.load(audio_path, sr=sr)
    hop_length = 512
    frame_length = 1024
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length, n_fft=frame_length)

    gunshot_times = []
    in_shot = False
    start_time = 0

    print("Detecting gunshots in audio frames...")
    for t, energy in tqdm(zip(times, rms), total=len(rms), mininterval=0.5, smoothing=0.1):
        if energy > threshold and not in_shot:
            in_shot = True
            start_time = t
        elif energy <= threshold and in_shot:
            in_shot = False
            end_time = t
            gunshot_times.append((start_time, end_time))

    # Merge very close intervals
    merged = []
    for interval in gunshot_times:
        if not merged:
            merged.append(interval)
        else:
            prev_start, prev_end = merged[-1]
            if interval[0] - prev_end < 0.5:
                merged[-1] = (prev_start, interval[1])
            else:
                merged.append(interval)
    return merged

# --- Step 3: Analyze laughter using pre-trained model (placeholder) ---
def detect_laughter(audio_path):
    print("Loading audio for laughter detection...")
    y, sr = librosa.load(audio_path, sr=22050)
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)

    laughter_times = []
    in_laugh = False
    start_time = 0
    threshold = 0.05

    print("Detecting laughter in audio frames...")
    for t, energy in tqdm(zip(times, rms), total=len(rms), mininterval=0.5, smoothing=0.1):
        if energy > threshold and not in_laugh:
            in_laugh = True
            start_time = t
        elif energy <= threshold and in_laugh:
            in_laugh = False
            end_time = t
            laughter_times.append((start_time, end_time))

    merged = []
    for interval in laughter_times:
        if not merged:
            merged.append(interval)
        else:
            prev_start, prev_end = merged[-1]
            if interval[0] - prev_end < 0.5:
                merged[-1] = (prev_start, interval[1])
            else:
                merged.append(interval)
    return merged

# --- Step 4: Merge segments from gunshots and laughs ---
def merge_segments(gunshots, laughs):
    segments = gunshots + laughs
    segments.sort(key=lambda x: x[0])

    if not segments:
        return []

    merged = [segments[0]]
    for current in segments[1:]:
        last = merged[-1]
        if current[0] <= last[1] + 0.5:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

# --- Step 5: Fast save clips using ffmpeg with stream copy in parallel ---
def ffmpeg_extract_clip(input_path, start, end, output_path):
    duration = end - start
    cmd = [
        "ffmpeg",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-c", "copy",               # Stream copy, no re-encode
        "-avoid_negative_ts", "make_zero",
        "-y",                      # Overwrite output file
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def save_clips_fast_parallel(video_path, segments, output_dir="clips", max_workers=4):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Saving {len(segments)} clips fast with ffmpeg (no re-encoding) in parallel...")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for idx, (start, end) in enumerate(segments):
            output_path = os.path.join(output_dir, f"clip_{idx+1}_{start:.2f}_{end:.2f}.mp4")
            futures.append(executor.submit(ffmpeg_extract_clip, video_path, start, end, output_path))

        for future in tqdm(as_completed(futures), total=len(futures)):
            clip_path = future.result()
            print(f"Saved clip: {clip_path}")

# --- Main pipeline ---
def main_pipeline(video_path):
    print("Step 1: Extracting audio...")
    audio_path = extract_audio_ffmpeg(video_path)  # use ffmpeg version here

    # rest of pipeline unchanged ...

    print("Step 2: Detecting gunshots...")
    gunshots = detect_gunshots(audio_path)
    print(f"Gunshot segments: {gunshots}")

    print("Step 3: Detecting laughter...")
    laughs = detect_laughter(audio_path)
    print(f"Laughter segments: {laughs}")

    print("Step 4: Merging segments...")
    segments = merge_segments(gunshots, laughs)
    print(f"Merged segments: {segments}")

    print("Step 5: Saving video clips...")
    save_clips_fast_parallel(video_path, segments, max_workers=8)  # Adjust max_workers based on your CPU cores

    print("Processing completed.")

if __name__ == "__main__":
    video_file = "9.mp4"  # Replace with your actual file path
    main_pipeline(video_file)
