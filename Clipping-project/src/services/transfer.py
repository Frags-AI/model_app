from models.job_manager import Job
from config import settings
import requests
import os

def transfer_clips_to_backend(path: str, job: Job):
        files = []
        for filename in os.listdir(path):
            full_path = os.path.join(path, filename)
            files.append(("files", (filename, open(full_path, "rb"), "video/mp4")))

        headers = {
            "model_signing_secret": settings.signing_secret
        }

        return requests.post(f"{settings.api_url}/api/video/project/upload", headers=headers, files=files, data={"job_id": job.get_id(), "status": job.get_status()})