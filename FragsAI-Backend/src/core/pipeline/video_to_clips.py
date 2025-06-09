import numpy as np
import os
import subprocess
import soundfile as sf

def extract_audio_ffmpeg(video_path, audio_path="temp_audio.wav", sample_rate=8000):
    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",  # Mono
        "-ar", str(sample_rate),
        "-acodec", "pcm_s16le",
        audio_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_path

def find_loudest_moments(audio, sr, num_clips=15, clip_length=5):
    hop = int(sr * clip_length)
    num_windows = len(audio) // hop
    rms_vals = [np.sqrt(np.mean(audio[i*hop:(i+1)*hop]**2)) for i in range(num_windows)]
    
    if len(rms_vals) == 0 or np.all(np.array(rms_vals) == 0):
        print("❌ No loud segments detected.")
        return []

    loudest_indices = np.argsort(rms_vals)[-num_clips:]
    loudest_times = sorted([i * clip_length for i in loudest_indices])
    return loudest_times

def save_clips_ffmpeg(video_path, times, output_dir, clip_length=5):
    os.makedirs(output_dir, exist_ok=True)

    for i, start in enumerate(times):
        output = os.path.join(output_dir, f"clip_{i+1}.mp4")
        command = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", video_path,
            "-t", str(clip_length),
            "-c", "copy",  # Fast copy without re-encoding
            output
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(output):
            print(f"✅ Saved: {output}")
        else:
            print(f"❌ Failed to save: {output}")

def main(video_path, output_dir="out_clips", num_clips=15, clip_length=5):
    print(f"🔍 Extracting audio...")
    audio_path = extract_audio_ffmpeg(video_path)
    
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        raise RuntimeError("❌ FFmpeg failed to extract audio.")

    audio, sr = sf.read(audio_path)
    os.remove(audio_path)

    print(f"🎧 Audio loaded: {len(audio)/sr:.2f}s at {sr}Hz")
    loudest_times = find_loudest_moments(audio, sr, num_clips, clip_length)
    print(f"🔊 Loudest timestamps: {loudest_times}")

    if not loudest_times:
        return

    print("🎬 Saving video clips using FFmpeg...")
    save_clips_ffmpeg(video_path, loudest_times, output_dir, clip_length)

if __name__ == "__main__":
    main("11.mp4")
