from fastapi import APIRouter,UploadFile,File
from fastapi.responses import JSONResponse
from services.subtitles import (
    transcribe,extract_audio,generate_subtitle_file,
    add_subtitle_to_video,
)
from config import settings
router=APIRouter()

@router.post("/add_subtiles/")
def add_subtitles(file:UploadFile=File(...)):
    video_path=os.path.join(settings.upload_folder, file.filename)

    ## Extract audio
    audio=extract_audio(video_path)

    ## Transcribe audio
    language,segments=transcribe(audio)

    ## Create srt file
    subtitle_file=generate_subtitle_file(language,segments)

    ## Overlay Subtitles on clip
    output_video=add_subtitle_to_video(video_path,subtitle_file,font='Ariel',color='Red')


    return JSONResponse({"output_video":output_video})