from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from moviepy.config import change_settings
import os

load_dotenv()

class Settings(BaseSettings):
    upload_folder: str = "media/uploads"
    download_folder: str = "media/downloads"
    allowed_extensions: list[str] = ["mp4", "mov", "webm", "avi", "mkv"]
    environment: str = os.environ.get("ENVIRONMENT")
    host_name: str = os.environ.get("HOST_NAME")
    api_url: str = os.environ.get("API_URL")
    client_url: str = os.environ.get("CLIENT_URL")
    signing_secret: str = os.environ.get("MODEL_SIGNING_SECRET")
    openai_key: str = os.environ.get("OPENAI_API_KEY")
    sandbox_development_key: str = "uxkEreSYgnrPj4q4hxVuJYqA0jwDoQ3SjIvwiEEV"
    sandbox_production_key: str = "xB9YvCM80apOAjKyfAJCwHKYsc0XuQq4dKpDv3Th"
    cfg_path: str | None = os.environ.get("CFG_PATH", os.path.abspath("src/models/pretrained/yolov3.cfg"))
    weight_path: str | None = os.environ.get("WEIGHT_PATH", os.path.abspath("src/models/pretrained/yolo.weights"))
    image_magick_path: str = os.environ.get("MAGICK_PATH") # Path to magick.exe file
    elevenlabs_api_key: str = os.environ.get("ELEVENLABS_API_KEY")
    elevenlabs_url: str = os.environ.get("ELEVENLABS_URL", "https://api.elevenlabs.io/v1/text-to-speech/cgSgspJ2msm6clMCkdW9")
    stable_diffusion_key: str = os.environ.get("STABLE_DIFFUSION_KEY")
    stable_diffusion_url: str = os.environ.get("STABLE_DIFFUSION_URL", "https://api.stablediffusionapi.com/v1/generate")
    

    # Add subdirectories here
    def generate_subdirectories(self):
        subdirectories = ["videos", "thumbnails", "audios"]

        for subdirectory in subdirectories:
            upload_folder_path = os.path.join(self.upload_folder, subdirectory)
            download_folder_path = os.path.join(self.download_folder, subdirectory)
            os.makedirs(upload_folder_path, exist_ok=True)
            os.makedirs(download_folder_path, exist_ok=True)

    # Make sure to install magick.exe
    def set_image_magick_path(self):
        change_settings({"IMAGEMAGICK_BINARY": self.image_magick_path})

settings = Settings()
settings.generate_subdirectories()
settings.set_image_magick_path()
