from fastapi.responses import StreamingResponse
from core.aspect_ratio import enhance_video_aspect_ratio
import os
from clients.aws import s3_service
from celery_app.app import celery

@celery.task(bind=True)
def change_aspect_ratio(self, s3_key: str, input_path: str, output_path: str, ratio: float, method: str):
    
    s3_service.download_file(s3_key, input_path)

    # Process the video
    output_video_path = enhance_video_aspect_ratio(input_path, output_path, ratio, method)

    if output_video_path and os.path.exists(output_video_path):
        return StreamingResponse(
            open(output_video_path, "rb"),
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename=processed_video.mp4"}
        )
    