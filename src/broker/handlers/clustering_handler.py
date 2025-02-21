from uuid import UUID 
from typing import TypedDict
import logging


from src.learning_materials.knowledge_base.clustering import cluster_document

logger = logging.getLogger(__name__)

class DocumentUploadMessage(TypedDict):
    """
    Document upload message from CDN
    """
    document_id: UUID
    dimensions: int


def handle_document_upload_rag(message: DocumentUploadMessage):
    """
    Handle document upload message from CDN
    """
    logger.info(f"Document upload message received for document_id: {message['document_id']}")
    cluster_document(document_id=message["document_id"], dimensions=message["dimensions"])