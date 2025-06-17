import requests
from config import Config

config = Config()
BASE_URL_SCRAPER = config.BASE_URL_SCRAPER


import asyncio
from typing import Iterable, Union, IO, List, Tuple
import requests

# Keep your constant import the same
# from settings import BASE_URL_SCRAPER

FileLike = Union[IO[bytes], "UploadFile"]  # type hint for common cases


def _sync_read(f: FileLike) -> bytes:
    """Read bytes from *f*, agnostic to UploadFile vs regular file object."""
    # If it's a FastAPI UploadFile we must grab the underlying .file attribute
    # when we're in a sync function (can't 'await').
    file_obj = getattr(f, "file", f)
    file_obj.seek(0)
    return file_obj.read()


def _filename(f: FileLike) -> str:
    return getattr(f, "filename", getattr(f, "name", "unknown.bin"))


def _content_type(f: FileLike) -> str:
    return getattr(f, "content_type", "application/octet-stream")


def create_file_embeddings(
    incoming_files: Iterable[FileLike], file_uuids: str, auth_header: str
) -> dict:
    """
    Upload multiple files to the scraper service and return the JSON response.

    Parameters
    ----------
    incoming_files : Iterable[FileLike]
        Any iterable yielding file objects or FastAPI/Django uploaded files.
    file_uuids : str
        Comma-separated UUID string the backend expects.
    auth_header : str
        Bearer token or other auth value sent as `Authorization`.

    Returns
    -------
    dict
        Parsed JSON response from the scraper.
    """
    endpoint = f"{BASE_URL_SCRAPER}/file/"

    # Build the multipart list: [("files", (<name>, <bytes>, <mime>)), ...]
    files_payload: List[Tuple[str, Tuple[str, bytes, str]]] = [
        (
            "files",
            (
                _filename(f),
                _sync_read(f),
                _content_type(f),
            ),
        )
        for f in incoming_files
    ]

    data = {"uuids": file_uuids}
    headers = {"Authorization": auth_header}

    response = requests.post(endpoint, headers=headers, files=files_payload, data=data)

    if response.status_code != 200:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}"
        )

    return response.json()



def create_url_embeddings(url: str, uuid: str, auth_header: str) -> dict:
    endpoint = f"{BASE_URL_SCRAPER}/url/"

    data = {"urls": [url], "uuids": [uuid]}

    headers = {"Authorization": auth_header}

    response = requests.post(endpoint, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}"
        )
    return response.json()
