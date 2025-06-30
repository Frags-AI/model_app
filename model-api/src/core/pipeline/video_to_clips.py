import numpy as np
import os
import subprocess

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
        print("No loud segments detected.")
        return []

    # Get the indices of the loudest clips (sorted)
    loudest_indices = np.argsort(rms_vals)[-num_clips:]
    
    # Sort the indices to get the corresponding times in order
    loudest_indices = sorted(loudest_indices)
    
    # Initialize the list for loudest times
    loudest_times = []

    for i in range(len(loudest_indices)):
        start_time = loudest_indices[i].item() * clip_length
        # If it's the first element, append it
        if i == 0:
            loudest_times.append(start_time)
        # If it's the second element, compare it with the first one
        elif i == 1:
            prev_time = loudest_indices[i-1].item() * clip_length
            if start_time > prev_time + clip_length:
                loudest_times.append(start_time)
        # If it's the third or subsequent elements, compare with the two previous ones
        elif i >= 2:
            prev_time1 = loudest_indices[i-1] * clip_length
            prev_time2 = loudest_indices[i-2] * clip_length
            if start_time == prev_time1+clip_length:
                if start_time == prev_time2+2*clip_length:   
                    loudest_times.append(start_time)
            else: 
                loudest_times.append(start_time)
    
    count = 1
    while len(loudest_times) < num_clips: 
        idx = -(num_clips+count)
        loudest_index = np.argsort(rms_vals)[idx]
        start_time = loudest_index.item()*clip_length
        prev_time1 = np.argsort(rms_vals)[idx-1].item() * clip_length
        prev_time2 = np.argsort(rms_vals)[idx-2].item() * clip_length
        if start_time == prev_time1+clip_length:
            if start_time == prev_time2+2*clip_length:
                loudest_times.append(start_time)
            else: 
                loudest_times.append(start_time)
        count += 1     

    return sorted(loudest_times)

def save_clips_ffmpeg(video_path, times, output_dir, clip_length=5):
    os.makedirs(output_dir, exist_ok=True)
    
    video_name = os.path.splitext(os.path.basename(video_path))[0] # edited line
    for i, start in enumerate(times):
        
        output = os.path.join(output_dir, f"{video_name}_clip_{i+1}.mp4") # edited line
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
            print(f"Saved: {output}")
        else:
            print(f"Failed to save: {output}")

