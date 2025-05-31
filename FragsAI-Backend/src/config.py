from dotenv import load_dotenv
from pydantic_settings import BaseSettings
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
    cfg_path: str | None = os.environ.get("CFG_PATH", os.path.abspath("src/models/pretrained/yolov3.cfg"))
    weight_path: str | None = os.environ.get("WEIGHT_PATH", os.path.abspath("src/models/pretrained/yolo.weights"))        

settings = Settings()