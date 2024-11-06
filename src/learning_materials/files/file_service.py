from uuid import UUID
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from django.core.files.uploadedfile import UploadedFile
from config import Config

# Load Azure configurations using Config
config = Config()
AZURE_CONNECTION_STRING = config.AZURE_STORAGE_CONNECTION_STRING
AZURE_CONTAINER_NAME = config.AZURE_STORAGE_CONTAINER_NAME

# Initialize Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

def upload_file_to_blob(file: UploadedFile, user_uuid: UUID, course_uuid: UUID) -> str:
    """
    Uploads a file to Azure Blob Storage and returns the URL.

    Args:
        file (UploadedFile): The uploaded file.
        user_uuid (UUID): The UUID of the user.
        course_uuid (UUID): The UUID of the course.

    Returns:
        str: The URL of the uploaded file in Azure Blob Storage.
    """
    # Modify the blob name path to avoid the extra "user-uploads" level
    blob_name = f"{user_uuid}/{course_uuid}/{file.name}"
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file, overwrite=True)
    return blob_client.url


def generate_sas_url(blob_name: str) -> str:
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=AZURE_CONTAINER_NAME,
        blob_name=blob_name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)  # Adjust expiry as needed
    )
    return f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob_name}?{sas_token}"

def list_files_in_course(user_uuid: UUID, course_uuid: UUID) -> list[str]:
    prefix = f"{user_uuid}/{course_uuid}/"
    blob_list = container_client.list_blobs(name_starts_with=prefix)
    file_urls = [
        generate_sas_url(blob.name)
        for blob in blob_list
    ]
    return file_urls
