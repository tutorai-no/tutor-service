import os
from typing import Tuple
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta
from django.core.files.uploadedfile import UploadedFile
from django.utils.text import get_valid_filename
from uuid import UUID
from config import Config

config = Config()
AZURE_CONNECTION_STRING = config.AZURE_STORAGE_CONNECTION_STRING
AZURE_CONTAINER_NAME = config.AZURE_STORAGE_CONTAINER_NAME

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

def upload_file_to_blob(file: UploadedFile, user_uuid: UUID, course_uuid: UUID, file_uuid: UUID) -> Tuple[str, str]:
    """
    Uploads a file to Azure Blob Storage and returns the blob name and URL.

    Args:
        file (UploadedFile): The uploaded file.
        user_uuid (UUID): The UUID of the user.
        course_uuid (UUID): The UUID of the course.
        file_uuid (UUID): The UUID of the file.

    Returns:
        Tuple[str, str]: The blob name and the URL of the uploaded file in Azure Blob Storage.
    """
    _, file_extension = os.path.splitext(file.name)
    blob_name = f"{user_uuid}/{course_uuid}/{file_uuid}{file_extension}"
    blob_client = container_client.get_blob_client(blob_name)
    content_settings = ContentSettings(content_type=file.content_type)
    blob_client.upload_blob(file, overwrite=True, content_settings=content_settings)
    return blob_name, blob_client.url

def generate_sas_url(blob_name: str) -> str:
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=AZURE_CONTAINER_NAME,
        blob_name=blob_name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    return f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob_name}?{sas_token}"