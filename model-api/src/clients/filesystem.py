import os
from uuid import uuid4
import shutil

class StorageSystem:
    def __init__(self):
        self.BASE_PATH = f"media_{uuid4()}"
        self.UPLOAD_PATH = os.path.join(self.BASE_PATH, "uploads")
        self.DOWNLOAD_PATH = os.path.join(self.BASE_PATH, "downloads")
        self.FLORENCE_PATH = os.path.join(self.BASE_PATH, "florence")

        os.makedirs(self.UPLOAD_PATH, exist_ok=True)
        os.makedirs(self.DOWNLOAD_PATH, exist_ok=True)
        os.makedirs(self.FLORENCE_PATH, exist_ok=True)

    def create_upload_path(self, directory: str, file_name: str = ""):
        path = os.path.join(directory, file_name)
        full_path = os.path.join(self.UPLOAD_PATH, path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

    def create_download_path(self, directory: str, file_name: str = ""):
        path = os.path.join(directory, file_name)
        full_path = os.path.join(self.DOWNLOAD_PATH, path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path


    def __del__(self):
        shutil.rmtree(self.BASE_PATH)


