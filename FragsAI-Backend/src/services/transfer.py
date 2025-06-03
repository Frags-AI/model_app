from celery_app.job_manager import Job
from config import settings
import requests
import os

def transfer_clips_to_backend(path: str, job: Job):
    files = []
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        files.append(("files", (filename, open(full_path, "rb"), "video/mp4")))

    headers = {
        "model_signing_secret": settings.SIGNING_SECRET
    }

    payload = {
        "job_id": job.get_id(),
        "status": job.get_status()
    }

    response = requests.post(
        f"{settings.API_URL}/api/video/project/upload",
        headers=headers,
        files=files,
        data=payload
    )

    for _, (fname, fh, _) in files:
        fh.close()

    return response
