import os
import speech_recognition as sr
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment
from pydub.silence import split_on_silence
import io
import tempfile
import logging

def transcribe_video(video_path, silence_thresh=-40, min_silence_len=500):
    """
    Transcribes audio from a video file and returns structured data.
    """
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio

        # Use a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            temp_audio_path = temp_audio_file.name
            audio_clip.write_audiofile(temp_audio_path, codec='pcm_s16le', fps=16000)

        audio = AudioSegment.from_wav(temp_audio_path)
        chunks = split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=100
        )

        r = sr.Recognizer()
        transcript_data = []
        
        # This is the critical part: process chunks in a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, chunk in enumerate(chunks):
                start_time_ms = sum(len(c) for c in chunks[:i])
                end_time_ms = start_time_ms + len(chunk)

                # Export each chunk to a temporary WAV file
                chunk_path = os.path.join(tmpdir, f"chunk{i}.wav")
                chunk.export(chunk_path, format="wav")

                try:
                    # Recognize speech from the temporary file path
                    with sr.AudioFile(chunk_path) as source:
                        audio_data = r.record(source)
                    
                    text = r.recognize_google(audio_data)
                    transcript_data.append({
                        'start': start_time_ms / 1000.0,
                        'end': end_time_ms / 1000.0,
                        'text': text
                    })
                except sr.UnknownValueError:
                    # Ignore segments that are just silence
                    pass
                except sr.RequestError as e:
                    logging.error(f"API request failed: {e}")

        # Clean up the temporary audio file
        os.remove(temp_audio_path)

        return transcript_data
    
    except Exception as e:
        logging.error(f"Error in transcribe_video: {e}")
        return []

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    # Use a raw string for the Windows path
    video_file = r'C:\Users\paras\model_app\clipping -base-files\test.mp4'
    if os.path.exists(video_file):
        transcript = transcribe_video(video_file)
        if transcript:
            logging.info("--- Final Transcript ---")
            for item in transcript:
                logging.info(f"Start: {item['start']:.2f}s, End: {item['end']:.2f}s, Text: {item['text']}")
    else:
        logging.warning(f"Test video not found: {video_file}")