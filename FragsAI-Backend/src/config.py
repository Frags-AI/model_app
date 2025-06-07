from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import os

load_dotenv()

class Settings(BaseSettings):
    CELERY_BROKER_URL: str = os.environ.get("CELERY_BROKER")
    CELERY_RESULT_BACKEND: str = os.environ.get("CELERY_BACKEND")
    UPLOAD_FOLDER: str = "media/uploads"
    DOWNLOAD_FOLDER: str = "media/downloads"
    ALLOWED_EXTENSIONS: list[str] = ["mp4", "mov", "webm", "avi", "mkv"]
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT")
    HOST_NAME: str = os.environ.get("HOST_NAME")
    API_URL: str = os.environ.get("API_URL")
    CLIENT_URL: str = os.environ.get("CLIENT_URL")
    SIGNING_SECRET: str = os.environ.get("MODEL_SIGNING_SECRET")
    OPENAI_KEY: str = os.environ.get("OPENAI_API_KEY")
    SANDBOX_API_KEY: str = os.environ.get("SANDBOX_API_KEY")
    CFG_PATH: str | None = os.environ.get("CFG_PATH", os.path.abspath("models/pretrained/yolov3.cfg"))
    WEIGHT_PATH: str | None = os.environ.get("WEIGHT_PATH", os.path.abspath("models/pretrained/yolo.weights"))
    ELEVENLABS_API_KEY: str = os.environ.get("ELEVENLABS_API_KEY")
    ELEVENLABS_URL: str = os.environ.get("ELEVENLABS_URL", "https://api.elevenlabs.io/v1/text-to-speech/cgSgspJ2msm6clMCkdW9")
    STABLE_DIFFUSION_KEY: str = os.environ.get("STABLE_DIFFUSION_KEY")
    STABLE_DIFFUSION_URL: str = os.environ.get("STABLE_DIFFUSION_URL", "https://api.stablediffusionapi.com/v1/generate")

    # Add subdirectories here
    def generate_subdirectories(self):
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(self.DOWNLOAD_FOLDER, exist_ok=True)
        subdirectories = ["videos", "thumbnails", "audios"]

        for subdirectory in subdirectories:
            upload_folder_path = os.path.join(self.UPLOAD_FOLDER, subdirectory)
            download_folder_path = os.path.join(self.DOWNLOAD_FOLDER, subdirectory)
            os.makedirs(upload_folder_path, exist_ok=True)
            os.makedirs(download_folder_path, exist_ok=True)

settings = Settings()
settings.generate_subdirectories()