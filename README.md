# Fragss-AI
# Video Segmentation Tool

The Video Segmentation Tool is a Python-based application that allows users to segment long video files into smaller clips based on various criteria, such as shot boundaries, object detection, and audio event detection.

## Features

- **Shot Boundary Detection**: Identify transitions between shots or scenes in the input video using histogram-based comparison techniques.
- **Video Clip Generation**: Extract video segments based on the detected shot boundaries and save them as individual clips.
- **Audio Clipping (Optional)**: Clip the audio of the input video based on the detected shot boundaries and save the audio segments separately.
- **Video and Audio Combination**: Combine the generated video and audio clips into the final output files.
- **GUI-based Interface**: Provide a user-friendly graphical interface for selecting the input video, output directory, and configuring the segmentation options.
- **Filtering Options**: Allow users to enable or disable object detection and audio event detection as additional filtering criteria for the video segmentation process.

## Prerequisites

- Python 3.6 or newer
- The following Python libraries:
  - `opencv-python`
  - `tkinter`
  - `moviepy`
  - `numpy`


## Installation

### 1. Download repo through HTTPS or SSH
### 2. Create virtual environment
- Utilize VScode to automatically set up the .venv by Ctrl + Shift + P and typing "Create Environment". This will automatically create the .venv folder with the requirements.txt folder found at the root level
- To do so manually:
```bash
python3 -m venv .venv

# For Mac and Linux-based Systems
source .venv/bin/activate

# For Windows
.venv\Scripts\activate

# This will take around 5-15 minutes
pip install -r requirements.txt
```

This is import as it prevents adding excess dependencies to the project

### 3. Create .env file inside of Clipping-Project
Using the Frags AI Secrets Storage file, copy and paste the secrets into the .env at the root of Clipping-Project

### 4. Add Paths to Pretained Models (Optional)
- If your models are storage outside of the project scope, you can specify the absolute path to the model inside of the .env file.
- If not specified, the project will automatically search for it inside of the pretrained folder inside models.

### 5. Build the server
- Run the command (Assuming you're at the root level)
```bash
cd .\Clipping-project\
python run .\src\main.py
```

### 6. Testing the server
Assuming you have Postman or any API testing client
#### 1. Make a get request to localhost:8000
#### 2. Ensure that the request sends a 200 status code

## Contributing

Contributions to the Video Segmentation Tool are welcome! If you find any issues or have ideas for improvements, please feel free to submit a pull request or open an issue on the [GitHub repository]

## Acknowledgments

- The `shot_boundary_detection`, `clip_video`, `clip_audio`, and `combine_video_audio` functions were adapted from the `Video_Segmentation_Tool.py` file.
- The GUI implementation was based on the Tkinter library.

## Thing to remember before running main.py:
1. Download FFmpeg:
- Download the Files: https://drive.google.com/drive/folders/1Ku9nnmQfBpeNI9M1HyvEoFQlbZorIX2Y?usp=drive_link
- Once downloaded, extract it to a folder, for example, C:\ffmpeg-master-latest-win64-gpl-shared\bin.
- Add FFmpeg to the System PATH:
- Right-click on "This PC" or "Computer" and select "Properties".
- Click on "Advanced system settings" and then click on the "Environment Variables" button.
- Under "System variables", find and select the Path variable, then click "Edit".
- In the "Edit Environment Variable" window, click "New" and add the path to the bin folder where you extracted FFmpeg (e.g., C:\ffmpeg-master-latest-win64-gpl-shared\bin).
- Click "OK" to close all windows.

2. ImageMagick
- Download and Install ImageMagick
- Run the installer and follow the installation steps.
- During the installation, make sure to:
- Select the option to add ImageMagick to your system's PATH ex: C:\Program Files\ImageMagick-7.1.1-Q16.
- Choose the "Install legacy utilities (e.g., convert)" option if you need older commands like convert.

## Function to check for existing fonts in the system ("to be executed in seperate file"):
    from matplotlib import font_manager

    # Get all available font paths
    font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')

    # Print font names and their paths
    print("Available Fonts:")
    for font_path in font_paths:
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        print(f"{font_name} : {font_path}")

