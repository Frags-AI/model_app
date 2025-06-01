from fastapi import APIRouter,UploadFile,File
from fastapi.responses import JSONResponse, StreamingResponse
import os
from services.subtitles import (
    transcribe,extract_audio,generate_subtitle_file,
    add_subtitle_to_video,
)
from config import settings
router=APIRouter()

@router.post("/clip/")
async def add_subtitles(file:UploadFile=File(...)):
    print(file)
    video_path = os.path.join(settings.upload_folder, "videos", file.filename)

    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)

    ## Extract audio
    audio_path = extract_audio(video_path)

    ## Transcribe audio
    language,segments=transcribe(audio_path)

    ## Create srt file
    subtitle_file=generate_subtitle_file(language,segments, video_path)

    ## Overlay Subtitles on clip
    output_video_path = add_subtitle_to_video(video_path, subtitle_file, audio_path, font='Ariel',color='Red')

    return StreamingResponse(
        open(output_video_path, "rb"),
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=processed_{file.filename}"}
    )