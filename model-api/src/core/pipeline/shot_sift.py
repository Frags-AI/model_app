import cv2
import numpy as np
import logging
import psutil
from tqdm import tqdm
import os
import sys
import io
from concurrent.futures import ThreadPoolExecutor

# suppress_stderr class (same as before)
class suppress_stderr:
    def __enter__(self):
        try:
            self.stderr_fileno = sys.stderr.fileno()
            self.devnull = os.open(os.devnull, os.O_WRONLY)
            self.old_stderr = os.dup(self.stderr_fileno)
            os.dup2(self.devnull, self.stderr_fileno)
        except (AttributeError, io.UnsupportedOperation):
            self.stderr_fileno = None  # stderr can't be suppressed in this environment

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stderr_fileno is not None:
            os.dup2(self.old_stderr, self.stderr_fileno)
            os.close(self.devnull)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def adjust_sample_interval(video_path):
    with suppress_stderr():
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

    duration = total_frames / fps
    # Increase frame skip aggressively for longer videos
    if duration <= 3600:       # <= 1 hour
        return 20             # sample every 20th frame
    elif duration <= 18000:    # <= 5 hours
        return 30
    else:
        return 40             # sample every 40th frame

def extract_frames_sequential(video_path, frame_skip, resize_dim=(320, 180)):
    with suppress_stderr():
        cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Failed to open video: {video_path}")
        return [], []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_indices = []
    gray_frames = []

    logging.info(f"Total frames: {total_frames}, Sampling every {frame_skip} frames")

    frame_pos = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_pos % frame_skip == 0:
            # resize for speed
            small_frame = cv2.resize(frame, resize_dim)
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            gray_frames.append(gray)
            frame_indices.append(frame_pos)
        frame_pos += 1

    cap.release()
    logging.info(f"Extracted and converted {len(gray_frames)} frames to grayscale")
    return gray_frames, frame_indices

def compute_descriptors(frame, method):
    if method == 'sift':
        sift = cv2.SIFT_create()
        kp, des = sift.detectAndCompute(frame, None)
    else:
        orb = cv2.ORB_create()
        kp, des = orb.detectAndCompute(frame, None)
    return des

def detect_shot_boundaries(frames, method='orb', match_threshold=30.0, num_threads=8):
    """
    Faster shot detection by:
    - Precompute all descriptors in parallel
    - Use ORB by default (faster)
    - Use multithreading to compute matches & distances
    """
    bf = None
    if method == 'sift':
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
    else:
        method = 'orb'
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # Precompute descriptors in parallel
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        descriptors = list(executor.map(lambda f: compute_descriptors(f, method), frames))

    shot_boundaries = []

    def compare_pair(i):
        if descriptors[i] is None or descriptors[i+1] is None:
            return None
        matches = bf.match(descriptors[i], descriptors[i+1])
        if not matches:
            return None
        avg_distance = sum(m.distance for m in matches) / len(matches)
        if avg_distance > match_threshold:
            return i+1
        return None

    # Compare pairs in parallel
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(compare_pair, range(len(frames)-1)))

    for r in results:
        if r is not None:
            shot_boundaries.append(r)

    logging.info(f"Detected {len(shot_boundaries)} shot boundaries using {method.upper()}")
    return shot_boundaries

def main():
    video_path = "9.mp4"
    method = 'orb'  # use ORB for speed
    frame_skip = adjust_sample_interval(video_path)

    logging.info("Starting frames extraction")
    frames, frame_indices = extract_frames_sequential(video_path, frame_skip)

    if not frames:
        logging.error("No frames extracted, aborting")
        return

    logging.info("Starting shot boundary detection")
    shot_boundaries = detect_shot_boundaries(frames, method=method, match_threshold=30.0)

    # Map boundaries back to original frame numbers
    original_frame_boundaries = [frame_indices[i] for i in shot_boundaries]

    print("Detected shot boundaries at frames:", original_frame_boundaries)

if __name__ == "__main__":
    main()
