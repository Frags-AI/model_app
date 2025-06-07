from config import settings
from contextlib import ExitStack
import requests
import os

def transfer_clips_to_backend(url: str, output_path: str, data: dict):
    print(url)
    headers = {"model_signing_secret": settings.SIGNING_SECRET}
    files = []

    with ExitStack() as stack:
        if os.path.isfile(output_path):
            filename = os.path.basename(output_path)
            file = stack.enter_context(open(output_path, "rb"))
            files.append(("files", (filename, file, "video/mp4")))
        else:
            for filename in os.listdir(output_path):
                full_path = os.path.join(output_path, filename)
                if os.path.isfile(full_path):
                    file = stack.enter_context(open(full_path, "rb"))
                    files.append(("files", (filename, file, "video/mp4")))

        response = requests.post(url, headers=headers, files=files, data=data)

    return response.json()
