from core.aspect_ratio import convert_16to9_ratio, convert_1to1_ratio, convert_9to16_ratio
from clients.filesystem import StorageSystem
from clients.aws import s3_service
from celery_app.app import celery
from core.transfer import transfer_clips_to_backend
from config import settings

@celery.task(bind=True)
def change_aspect_ratio(self, s3_key: str, ratio: float, method: str):

    ss = StorageSystem()
    input_path = ss.create_upload_path("videos", "video.mp4")
    output_path = ss.create_download_path("videos", "video.mp4")

    s3_service.download_file(s3_key, input_path)
    
    if ratio == 1:
        convert_1to1_ratio(input_path, output_path)
    elif ratio == 9/16:
        convert_9to16_ratio(input_path, output_path)
    else:
        convert_16to9_ratio(input_path, output_path)
    
    data = {"task_id": self.request.id, "status": "SUCCESS"}
    url = f"{settings.API_URL}/api/model/ratio"
    transfer_clips_to_backend(url, output_path, data)

    