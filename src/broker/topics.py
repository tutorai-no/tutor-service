from enum import StrEnum


class Topic(StrEnum):
    """
    All message broker topics shall be defined in this enum
    """

    USER_SIGNUP_SUCCESS = "user.signup.success"
    USER_ACTIVITY = "user.activity"
    DOCUMENT_UPLOAD_CDN = "document.upload.cdn"
    DOCUMENT_UPLOAD_RAG = "document.upload.rag"
