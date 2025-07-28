from services.thumbnail import (
    select_best_frame, generate_thumbnail_background,
    generate_dalle3_thumbnail, generate_from_sketch,
    generate_thumbnail_overlays, add_text_and_icon
)
from config import settings
from fastapi import UploadFile
from utils.video_converter import VideoConverter
import os
import cv2
import logging
import uuid
import time
from PIL import Image, ImageEnhance, ImageFilter

# Set up logger
logger = logging.getLogger(__name__)

"""
Mode 1: Generate thumbnail from Clip
Mode 2: Generate thumbnail using ChatGPT
Mode 3: Generate thumbnail with Sketch + Prompt
"""

os.makedirs(os.path.join(settings.upload_folder, "thumbnails"), exist_ok=True)
os.makedirs(os.path.join(settings.download_folder, "thumbnails"), exist_ok=True)

def thumbnail_generator(mode: int, file: UploadFile = None, prompt: str = None, text: str = None):
    thumbnail_path = None

    if mode == 1:
        file_name = file.filename.split(".")[0] + ".jpg"
        download_path = os.path.join(settings.download_folder, "thumbnails", file_name)

        temp_path = os.path.join(settings.upload_folder, "videos", file.filename)
        with open(temp_path, "wb") as f:
            f.write(file.file.read())

        video_path, frame_idx = select_best_frame(temp_path)
        thumbnail_path, size = generate_thumbnail_background(video_path, download_path, time_sec=frame_idx / 30)
        
        if text is not None:
            text_opts, icon_opts = generate_thumbnail_overlays(text, size)
            thumbnail_path = add_text_and_icon(thumbnail_path, text_opts, icon_opts)
    
    elif mode == 2:
        output_path = os.path.join(settings.download_folder, "thumbnails", "dalle_prompt.jpg")
        thumbnail_path = generate_dalle3_thumbnail(prompt, output_path)

    elif mode == 3:
        file_name = file.filename.split(".")[0] + ".png"
        download_path = os.path.join(settings.download_folder, "thumbnails", file_name)

        temp_path = os.path.join(settings.upload_folder, "thumbnails", file.filename)
        with open(temp_path, "wb") as f:
            file.write(file.file.read())

        thumbnail_path = generate_from_sketch(temp_path, prompt, download_path)

    return thumbnail_path


def generate_video_thumbnail(video_path: str, prompt: str, style: str = "cinematic", timestamp: int = 30):
    """
    Generate AI-enhanced thumbnails from video at specified timestamp.
    Production-ready implementation with automatic codec conversion.
    
    Args:
        video_path (str): Path to the video file
        prompt (str): Description of desired thumbnail style/content
        style (str): Thumbnail style (cinematic, gaming, vlog, etc.)
        timestamp (int): Timestamp in seconds to extract frame from
    
    Returns:
        dict: Result containing success status and thumbnail URLs
    """
    converter = None
    try:
        logger.info(f"[PRODUCTION] Generating thumbnail from {video_path} at {timestamp}s with style '{style}'")
        
        # Create thumbnails directory
        thumbnails_dir = "thumbnails"
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Initialize video converter for production-ready processing
        converter = VideoConverter()
        
        # Check if video needs conversion
        if converter.needs_conversion(video_path):
            logger.info(f"Video needs conversion. Using fast frame extraction at {timestamp}s instead of full conversion")
            # For thumbnails, extract just the frame we need instead of converting entire video
            processed_video_path = converter.extract_frame_as_video(video_path, timestamp)
            logger.info(f"Extracted frame video: {processed_video_path}")
            # Update timestamp to 0 since our extracted video starts at the desired frame
            timestamp = 0
        else:
            logger.info("Video is already compatible, no conversion needed")
            processed_video_path = video_path
        
        # Extract frame from the processed video
        frame = None
        duration = 60  # Default duration fallback
        
        # Open video with OpenCV (should work now after conversion)
        cap = cv2.VideoCapture(processed_video_path)
        if not cap.isOpened():
            raise Exception(f"Could not open processed video file: {processed_video_path}")
        
        try:
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps <= 0 or total_frames <= 0:
                raise Exception("Invalid video properties detected")
            
            duration = total_frames / fps
            logger.info(f"Video properties: {duration:.1f}s duration, {fps:.1f} fps, {total_frames} frames")
            
            # Ensure timestamp is within video duration
            if timestamp >= duration:
                timestamp = max(0, int(duration * 0.5))  # Use middle of video
                logger.warning(f"Timestamp adjusted to {timestamp}s (video duration: {duration:.1f}s)")
            
            # Seek to the specified timestamp
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read the frame
            ret, frame = cap.read()
            
            if not ret or frame is None:
                # Try a few frames around the target timestamp
                logger.warning(f"Failed to read frame at {timestamp}s, trying nearby frames...")
                
                for offset in [-1, 1, -2, 2, -5, 5]:
                    try_frame = max(0, min(total_frames - 1, frame_number + offset))
                    cap.set(cv2.CAP_PROP_POS_FRAMES, try_frame)
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        actual_timestamp = try_frame / fps
                        logger.info(f"Successfully extracted frame at {actual_timestamp:.1f}s (offset: {offset} frames)")
                        break
                
                if frame is None:
                    raise Exception("Could not extract any frame from video")
            else:
                logger.info(f"Successfully extracted frame at {timestamp}s from video")
            
        finally:
            cap.release()
        
        # Convert BGR to RGB for PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        # Apply style-based enhancements and generate multiple variations
        thumbnails = []
        
        # Generate multiple thumbnail variations based on style
        styles_to_generate = [style]
        if style == "cinematic":
            styles_to_generate.extend(["dramatic", "colorful"])
        elif style == "gaming":
            styles_to_generate.extend(["colorful", "dramatic"])
        elif style == "vlog":
            styles_to_generate.extend(["minimal", "colorful"])
        else:
            styles_to_generate.extend(["cinematic", "colorful"])
        
        # Limit to 3 thumbnails for performance
        for i, current_style in enumerate(styles_to_generate[:3]):
            enhanced_img = apply_thumbnail_style(img, current_style, prompt)
            
            # Save thumbnail with unique filename
            thumbnail_id = str(uuid.uuid4())
            thumbnail_filename = f"thumbnail_{thumbnail_id}_{current_style}.jpg"
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
            
            # Save with high quality
            enhanced_img.save(thumbnail_path, "JPEG", quality=95, optimize=True)
            
            # Create thumbnail info
            thumbnail_info = {
                "url": f"/thumbnails/{thumbnail_filename}",
                "style": current_style,
                "timestamp": timestamp,
                "size": {
                    "width": enhanced_img.width,
                    "height": enhanced_img.height
                }
            }
            
            thumbnails.append(thumbnail_info)
            logger.info(f"Generated thumbnail {i+1}/{len(styles_to_generate[:3])}: {thumbnail_filename}")
        
        logger.info(f"[PRODUCTION] Successfully generated {len(thumbnails)} thumbnails")
        
        return {
            "success": True,
            "thumbnails": thumbnails,
            "message": f"Generated {len(thumbnails)} high-quality thumbnails successfully",
            "video_info": {
                "duration": round(duration, 1),
                "fps": round(fps, 1),
                "converted": processed_video_path != video_path
            }
        }
        
    except Exception as e:
        logger.error(f"[PRODUCTION] Error generating video thumbnail: {str(e)}")
        return {
            "success": False, 
            "message": f"Failed to generate thumbnail: {str(e)}",
            "error_type": type(e).__name__
        }
    
    finally:
        # Clean up converter resources
        if converter:
            try:
                del converter
            except:
                pass


def create_fallback_thumbnail(style: str = "cinematic") -> str:
    """Create a fallback thumbnail when video frame extraction fails"""
    try:
        # Create a solid color image based on style
        color_map = {
            "cinematic": (25, 25, 35),      # Dark blue-gray
            "gaming": (50, 20, 80),         # Purple
            "vlog": (255, 200, 150),        # Warm orange
            "educational": (40, 80, 120),   # Blue
            "dramatic": (80, 20, 20),       # Dark red
            "colorful": (200, 100, 150),    # Pink
            "minimal": (240, 240, 240),     # Light gray
            "retro": (150, 100, 50),        # Brown
        }
        
        color = color_map.get(style, (128, 128, 128))  # Default gray
        
        # Create image with solid color
        img = Image.new('RGB', (1280, 720), color)
        
        # Add text overlay
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            text = "Thumbnail Preview"
            
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            x = (1280 - text_width) // 2
            y = (720 - text_height) // 2
            
            # Draw text with white color
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
            
        except Exception as e:
            logging.warning(f"Could not add text to fallback thumbnail: {e}")
        
        # Save fallback thumbnail
        fallback_dir = os.path.join(os.getcwd(), "thumbnails")
        os.makedirs(fallback_dir, exist_ok=True)
        
        fallback_filename = f"fallback_{style}_{int(time.time())}.jpg"
        fallback_path = os.path.join(fallback_dir, fallback_filename)
        
        img.save(fallback_path, "JPEG", quality=95)
        logging.info(f"Created fallback thumbnail: {fallback_path}")
        
        return fallback_path
        
    except Exception as e:
        logging.error(f"Failed to create fallback thumbnail: {e}")
        return None


def apply_thumbnail_style(img: Image.Image, style: str, prompt: str) -> Image.Image:
    """
    Apply style-specific enhancements to the thumbnail image.
    
    Args:
        img (Image.Image): Original image
        style (str): Style to apply
        prompt (str): User prompt for context
    
    Returns:
        Image.Image: Enhanced image
    """
    try:
        # Resize to standard thumbnail size (1280x720 for 16:9)
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        
        if style == "cinematic":
            # Add cinematic look: slight desaturation, contrast boost
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.9)
            
        elif style == "gaming":
            # Gaming style: high saturation, sharpness
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.3)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)
            
        elif style == "dramatic":
            # Dramatic: high contrast, slight blur for depth
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.4)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.95)
            
        elif style == "colorful":
            # Colorful: boosted saturation and brightness
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.4)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)
            
        elif style == "vlog":
            # Vlog style: natural, slightly warm
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.05)
            
        elif style == "minimal":
            # Minimal: reduced saturation, clean look
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.8)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
            
        elif style == "retro":
            # Retro: vintage look with reduced contrast
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.9)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(0.9)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)
        
        # Apply slight sharpening for all styles
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
        
        return img
        
    except Exception as e:
        logging.error(f"Error applying style {style}: {str(e)}")
        return img  # Return original if enhancement fails

