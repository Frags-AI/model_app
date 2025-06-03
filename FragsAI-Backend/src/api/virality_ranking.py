from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
from uuid import uuid4
from virality_ranking import rank_clips, get_video_clips_from_folder, VIRALITY_FOLDER_PATH

app = FastAPI()

UPLOAD_DIR = "uploaded_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/rank-virality")
async def rank_virality(file: UploadFile = File(...)):
    try:
        #save uploaded file
        file_id = f"{uuid4().hex}_{file.filename}"
        video_path = os.path.join(UPLOAD_DIR, file_id)
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        #rank clip
        ranked = rank_clips([video_path])
        score, path = ranked[0]

        return JSONResponse(content={
            "filename": file.filename,
            "score": score,
            "ranked_filename": os.path.basename(path)
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})