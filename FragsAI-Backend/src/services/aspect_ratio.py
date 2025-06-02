import moviepy.editor as mp
import logging
import os

def enhance_video_aspect_ratio(
    input_video: str,
    output_folder: str,
    desired_aspect_ratio: float,
    method: str,
    target_width: int = 720,
    target_height: int = 1280,
) -> str | None:
    """
    Enhances the video by adjusting its aspect ratio for platforms like TikTok/Shorts.
    Args:
        input_video (str): Path to the input video.
        output_folder (str): Folder to save the adjusted video.
        desired_aspect_ratio (float): Desired aspect ratio (e.g., 9/16 for TikTok).
        method (str): "crop" (center-crop overflow) or "pad" (add black bars).
        target_width (int): Target width for the output video.
        target_height (int): Target height for the output video.
    Returns:
        str | None: Path to the output video, or None on error.
    """
    try:
        video = mp.VideoFileClip(input_video)
        source_width, source_height = video.size
        current_aspect_ratio = source_width / source_height
        method = method if method else "crop"

        if desired_aspect_ratio == 1:
            min_size = min(target_height, target_width)
            target_width = min_size
            target_height = min_size
        if current_aspect_ratio < desired_aspect_ratio:
            # If video is too tall, then scale width up to target_width
            scale_factor = target_width / source_width
        else:
            # If video is too wide, scale height up to target_height
            scale_factor = target_height / source_height

        resized = video.resize(scale_factor)

        if method == "crop":
            fitted = resized.crop(
                x_center=resized.w / 2,
                y_center=resized.h / 2,
                width=target_width,
                height=target_height,
            )
        elif method == "pad":
            pad_left = max(0, (target_width - resized.w) / 2)
            pad_right = pad_left
            pad_top = max(0, (target_height - resized.h) / 2)
            pad_bottom = pad_top

            padded = resized.margin(
                left=int(pad_left),
                right=int(pad_right),
                top=int(pad_top),
                bottom=int(pad_bottom),
                color=(0, 0, 0),
            )
            fitted = padded.crop(
                x_center=padded.w / 2,
                y_center=padded.h / 2,
                width=target_width,
                height=target_height,
            )
        else:
            raise ValueError(f"Unknown method '{method}'. Use 'crop' or 'pad'.")

        base_name, ext = os.path.splitext(os.path.basename(input_video))
        output_name = f"{base_name}_aspect{ext}"
        output_video_path = os.path.join(output_folder, output_name)

        os.makedirs(output_folder, exist_ok=True)

        fitted.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            ffmpeg_params=["-crf", "23"],
        )

        logging.info(f"Saved aspect-adjusted video to: {output_video_path}")
        return output_video_path

    except Exception as e:
        logging.error(f"Error enhancing video aspect ratio: {e}")
        return None

    finally:
        try:
            video.close()
        except Exception:
            pass
        try:
            fitted.close()
        except Exception:
            pass