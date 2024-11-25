import requests
from config import Config

config = Config()
BASE_URL_SCRAPER = config.BASE_URL_SCRAPER

def create_file_embeddings(file, file_uuid: str, auth_header: str) -> dict:
    endpoint = f"{BASE_URL_SCRAPER}/file/"
    file.seek(0)
    file_content = file.read()

    files = {
        "files": (file.name, file_content, file.content_type)
    }

    data = {
        "uuids": [file_uuid]
    }

    headers = {
        "Authorization": auth_header
    }

    response = requests.post(endpoint, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")

    return response.json()