from uuid import UUID
from pydantic import BaseModel
import logging


from learning_materials.knowledge_base.clustering import cluster_document

logger = logging.getLogger(__name__)


class DocumentUploadMessage(BaseModel):
    """
    Document upload message from CDN
    """

    document_id: UUID
    dimensions: int


def handle_document_upload_rag(raw_message: dict):
    """
    Handle document upload message from CDN
    """
    message = DocumentUploadMessage.model_validate(raw_message)
    logger.info(
        f"Document upload message received for document_id: {message.document_id}"
    )
    cluster_document(
        document_id=message.document_id, dimensions=message.dimensions
    )
