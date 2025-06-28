import os
import speech_recognition as sr
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment
from pydub.silence import split_on_silence
import io

def transcribe_video(video_path, silence_thresh=-40, min_silence_len=500):
    """
    Transcribes audio from a video file and returns structured data.

    Args:
        video_path (str): Path to the video file.
        silence_thresh (int): Silence threshold for splitting audio.
        min_silence_len (int): Minimum silence length in ms.

    Returns:
        list: A list of dictionaries, each with 'start', 'end', and 'text'.
    """
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio

        # Use an in-memory buffer for the audio file
        wav_buffer = io.BytesIO()
        audio_clip.write_audiofile(wav_buffer, codec='pcm_s16le', logger=None)
        wav_buffer.seek(0)

        audio = AudioSegment.from_wav(wav_buffer)
        silence_segments = split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=min_silence_len
        )

        recognizer = sr.Recognizer()
        transcription_data = []
        
        # Keep track of the total time elapsed
        total_time_ms = 0

        print("Transcribing audio segments...")
        for i, chunk in enumerate(silence_segments):
            start_time_s = total_time_ms / 1000.0
            total_time_ms += len(chunk)
            end_time_s = total_time_ms / 1000.0

            # Export chunk to a temporary in-memory file
            chunk_buffer = io.BytesIO()
            chunk.export(chunk_buffer, format="wav")
            chunk_buffer.seek(0)

            with sr.AudioFile(chunk_buffer) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    transcription_data.append({
                        'start': start_time_s,
                        'end': end_time_s,
                        'text': text
                    })
                    print(f"[{start_time_s:.2f}s - {end_time_s:.2f}s]: {text}")
                except sr.UnknownValueError:
                    # This segment was likely just silence
                    pass
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
                    # Stop if the API fails
                    break
        
        print(f"Transcription complete. Found {len(transcription_data)} segments.")
        return transcription_data
    
    except Exception as e:
        print(f"Error during transcription: {e}")
        return []

# Example usage if you run this file directly
if __name__ == '__main__':
    # You would need to place a video file named 'test.mp4' in the same directory
    # or provide a full path to a video file.
    video_file = 'test.mp4' 
    if os.path.exists(video_file):
        transcript = transcribe_video(video_file)
        if transcript:
            print("\n--- Final Transcript ---")
            for item in transcript:
                print(f"Start: {item['start']:.2f}, End: {item['end']:.2f}, Text: {item['text']}")
    else:
        print(f"Test video '{video_file}' not found. Skipping example usage.")
