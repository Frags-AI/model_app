from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from moviepy.config import change_settings
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
    SANDBOX_DEVELOPMENT_KEY: str = "uxkEreSYgnrPj4q4hxVuJYqA0jwDoQ3SjIvwiEEV"
    SANDBOX_PRODUCTION_KEY: str = "xB9YvCM80apOAjKyfAJCwHKYsc0XuQq4dKpDv3Th"
    CFG_PATH: str | None = os.environ.get("CFG_PATH", os.path.abspath("models/pretrained/yolov3.cfg"))
    WEIGHT_PATH: str | None = os.environ.get("WEIGHT_PATH", os.path.abspath("models/pretrained/yolo.weights"))
    IMAGE_MAGICK_PATH: str = os.environ.get("MAGICK_PATH") # Path to magick.exe file

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

    # Make sure to install magick.exe
    def set_image_magick_path(self):
        change_settings({"IMAGEMAGICK_BINARY": self.IMAGE_MAGICK_PATH})

settings = Settings()
settings.generate_subdirectories()
settings.set_image_magick_path()
