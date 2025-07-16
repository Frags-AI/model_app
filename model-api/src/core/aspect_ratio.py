import moviepy.editor as mp
import subprocess

def convert_1to1_ratio(input_path: str, output_path: str, method: str = "crop") -> str | None:
    """
    Converts aspect ratio to 1:1 format.
    Args:
        input_path (str): Path to the input video.
        output_path (str): Pathh to save the adjusted video.
        method (str): "crop" (center-crop overflow) or "pad" (add black bars).
    Returns:
        str | None: Path to the output video, or None on error.
    """

    command = [
        "ffmpeg", "-y", "-i", input_path, "-vf", 
        "crop='if(gt(a,1),ih,iw)':'if(gt(a,1),ih,iw)',scale=720:720,setsar=1", 
        "-c:a", "copy", output_path
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("FFmpeg output:", result.stdout)
        print("FFmpeg completed successfully.")
    except subprocess.CalledProcessError as e:
        print("FFmpeg failed:", e.stderr)

def convert_9to16_ratio(input_path: str, output_path: str, method: str = "crop") -> str | None:
    """
    Converts aspect ratio to 9:16 format.
    Args:
        input_path (str): Path to the input video.
        output_path (str): Pathh to save the adjusted video.
        method (str): "crop" (center-crop overflow) or "pad" (add black bars).
    Returns:
        str | None: Path to the output video, or None on error.
    """

    command = [
        "ffmpeg", "-y", "-i", input_path, "-vf", 
        "scale=w='if(gt(a,9/16),720,-1)':h='if(gt(a,9/16),-1,1280)',pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1", 
        "-c:a", "copy", output_path
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("FFmpeg output:", result.stdout)
        print("FFmpeg completed successfully.")
    except subprocess.CalledProcessError as e:
        print("FFmpeg failed:", e.stderr)

def convert_16to9_ratio(input_path: str, output_path: str, method: str = "crop") -> str | None:
    """
    Converts aspect ratio to 16:9 format.
    Args:
        input_path (str): Path to the input video.
        output_path (str): Pathh to save the adjusted video.
        method (str): "crop" (center-crop overflow) or "pad" (add black bars).
    Returns:
        str | None: Path to the output video, or None on error.
    """
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf",
        "scale=w='if(gt(a,16/9),1280,-1)':h='if(gt(a,16/9),-1,720)',pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-c:a", "copy",
        output_path
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("FFmpeg output:", result.stdout)
        print("FFmpeg completed successfully.")
    except subprocess.CalledProcessError as e:
        print("FFmpeg failed:", e.stderr)
    

