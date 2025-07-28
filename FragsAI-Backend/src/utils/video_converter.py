"""
Video Codec Conversion Utility for Production-Ready Video Processing

This module provides robust video codec conversion capabilities to handle
AV1, HEVC, and other problematic codecs by converting them to H.264 format
which is widely supported by OpenCV and other video processing libraries.
"""

import os
import subprocess
import logging
import tempfile
import shutil
from pathlib import Path
import cv2

# Set up logger
logger = logging.getLogger(__name__)

class VideoConverter:
    """
    Handles video codec conversion for production-ready video processing.
    Converts problematic codecs (AV1, HEVC, etc.) to H.264 for compatibility.
    """
    
    SUPPORTED_CODECS = ['h264', 'avc1', 'mp4v']
    PROBLEMATIC_CODECS = ['av01', 'hev1', 'hvc1', 'vp9', 'vp8']
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="video_conversion_")
        logger.info(f"Video converter initialized with temp directory: {self.temp_dir}")
    
    def __del__(self):
        """Clean up temporary directory"""
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory: {e}")
    
    def check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available in the system"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def get_video_codec(self, video_path: str) -> str:
        """
        Get the codec of a video file using FFprobe
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            str: Codec name or 'unknown' if detection fails
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_name', '-of', 'csv=p=0',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                codec = result.stdout.strip().lower()
                logger.info(f"Detected codec for {video_path}: {codec}")
                return codec
            else:
                logger.warning(f"FFprobe failed for {video_path}: {result.stderr}")
                return 'unknown'
                
        except Exception as e:
            logger.error(f"Failed to detect codec for {video_path}: {e}")
            return 'unknown'
    
    def get_video_duration(self, video_path: str) -> float:
        """
        Get the duration of a video file using FFprobe
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            float: Duration in seconds, or 60.0 if detection fails
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'format=duration', '-of', 'csv=p=0',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                duration_str = result.stdout.strip()
                if duration_str and duration_str != 'N/A':
                    duration = float(duration_str)
                    logger.info(f"Detected duration for {video_path}: {duration:.1f}s")
                    return duration
                else:
                    logger.warning(f"Could not parse duration from FFprobe output: {duration_str}")
                    return 60.0
            else:
                logger.warning(f"FFprobe duration failed for {video_path}: {result.stderr}")
                return 60.0
                
        except Exception as e:
            logger.error(f"Failed to detect duration for {video_path}: {e}")
            return 60.0
    
    def needs_conversion(self, video_path: str) -> bool:
        """
        Check if a video needs codec conversion
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            bool: True if conversion is needed, False otherwise
        """
        # First try OpenCV to see if it can open the video
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                # Try to read a frame
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    logger.info(f"Video {video_path} is compatible with OpenCV")
                    return False
                else:
                    logger.warning(f"OpenCV can open {video_path} but cannot read frames")
                    return True
            else:
                logger.warning(f"OpenCV cannot open {video_path}")
                return True
                
        except Exception as e:
            logger.warning(f"OpenCV test failed for {video_path}: {e}")
            return True
    
    def convert_video(self, input_path: str, output_path: str = None) -> str:
        """
        Convert video to H.264 codec for maximum compatibility
        
        Args:
            input_path (str): Path to the input video file
            output_path (str): Path for the output video file (optional)
            
        Returns:
            str: Path to the converted video file
            
        Raises:
            Exception: If conversion fails
        """
        if not self.check_ffmpeg_availability():
            raise Exception("FFmpeg is not available. Cannot perform video conversion.")
        
        # Generate output path if not provided
        if output_path is None:
            input_name = Path(input_path).stem
            output_path = os.path.join(self.temp_dir, f"{input_name}_converted.mp4")
        
        logger.info(f"Converting video from {input_path} to {output_path}")
        
        # Get video duration to adjust timeout
        duration = self.get_video_duration(input_path)
        
        # Calculate timeout based on video duration (minimum 2 minutes, max 15 minutes)
        timeout_seconds = max(120, min(900, int(duration * 60)))  # 1 minute per minute of video
        logger.info(f"Video duration: {duration:.1f}s, conversion timeout: {timeout_seconds}s")
        
        # FFmpeg command optimized for speed while maintaining quality
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-i', input_path,  # Input file
            '-c:v', 'libx264',  # Video codec: H.264
            '-preset', 'fast',  # Faster encoding (was 'medium')
            '-crf', '26',  # Slightly lower quality for speed (was 23)
            '-c:a', 'aac',  # Audio codec
            '-b:a', '96k',  # Lower audio bitrate for speed (was 128k)
            '-movflags', '+faststart',  # Optimize for web streaming
            '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
            '-threads', '0',  # Use all available CPU threads
            '-max_muxing_queue_size', '1024',  # Handle large files better
            output_path
        ]
        
        try:
            # Run conversion with dynamic timeout
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout_seconds,  # Dynamic timeout based on video duration
                check=True
            )
            
            # Verify the output file exists and is valid
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully converted video to {output_path}")
                return output_path
            else:
                raise Exception("Conversion completed but output file is invalid")
                
        except subprocess.TimeoutExpired:
            raise Exception(f"Video conversion timed out after {timeout_seconds//60} minutes {timeout_seconds%60} seconds")
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg conversion failed: {e.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Video conversion failed: {e}")
            raise
    
    def extract_frame_as_video(self, video_path: str, timestamp: int = 30) -> str:
        """
        Extract a single frame and create a short video for thumbnail processing.
        This is much faster than converting the entire video.
        
        Args:
            video_path (str): Path to the input video file
            timestamp (int): Timestamp in seconds to extract frame from
            
        Returns:
            str: Path to the extracted frame video
        """
        logger.info(f"Extracting frame at {timestamp}s for fast thumbnail processing")
        
        # Generate output path
        input_name = Path(video_path).stem
        output_path = os.path.join(self.temp_dir, f"{input_name}_frame_{timestamp}s.mp4")
        
        # FFmpeg command to extract a single frame and create a 1-second video
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-ss', str(timestamp),  # Seek to timestamp
            '-i', video_path,  # Input file
            '-t', '1',  # Duration: 1 second
            '-c:v', 'libx264',  # Video codec: H.264
            '-preset', 'ultrafast',  # Fastest encoding
            '-crf', '30',  # Lower quality for speed
            '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
            '-an',  # No audio
            output_path
        ]
        
        try:
            # Run extraction with short timeout (30 seconds should be enough)
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                check=True
            )
            
            # Verify the output file exists and is valid
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully extracted frame to {output_path}")
                return output_path
            else:
                raise Exception("Frame extraction completed but output file is invalid")
                
        except subprocess.TimeoutExpired:
            raise Exception("Frame extraction timed out after 30 seconds")
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg frame extraction failed: {e.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            raise
    
    def process_video_for_compatibility(self, video_path: str) -> str:
        """
        Process a video file to ensure compatibility with OpenCV and other tools.
        Converts the video only if necessary.
        
        Args:
            video_path (str): Path to the input video file
            
        Returns:
            str: Path to the processed video (original if no conversion needed, 
                 converted if conversion was performed)
        """
        logger.info(f"Processing video for compatibility: {video_path}")
        
        # Check if conversion is needed
        if not self.needs_conversion(video_path):
            logger.info(f"Video {video_path} is already compatible, no conversion needed")
            return video_path
        
        # Get codec information for logging
        codec = self.get_video_codec(video_path)
        logger.info(f"Video uses codec '{codec}' which needs conversion")
        
        # Perform conversion
        try:
            converted_path = self.convert_video(video_path)
            logger.info(f"Successfully converted {video_path} to {converted_path}")
            return converted_path
        except Exception as e:
            logger.error(f"Failed to convert video {video_path}: {e}")
            raise Exception(f"Video conversion failed: {e}")


def convert_video_if_needed(video_path: str) -> str:
    """
    Convenience function to convert a video if needed.
    
    Args:
        video_path (str): Path to the input video file
        
    Returns:
        str: Path to the processed video
    """
    converter = VideoConverter()
    return converter.process_video_for_compatibility(video_path)


def is_video_compatible(video_path: str) -> bool:
    """
    Check if a video is compatible with OpenCV without conversion.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        bool: True if compatible, False otherwise
    """
    converter = VideoConverter()
    return not converter.needs_conversion(video_path)


# Example usage
if __name__ == "__main__":
    # Test the converter
    test_video = "test_video.mp4"
    if os.path.exists(test_video):
        converter = VideoConverter()
        processed_video = converter.process_video_for_compatibility(test_video)
        print(f"Processed video: {processed_video}")
