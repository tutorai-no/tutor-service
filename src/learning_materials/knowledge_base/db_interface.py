from abc import ABC, abstractmethod
import uuid
import logging

from learning_materials.learning_resources import Citation, FullCitation

from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class Database(ABC):
    """
    Abstract class for Connecting to a Database
    """

    @classmethod
    def __instancecheck__(cls, instance: any) -> bool:
        return cls.__subclasscheck__(type(instance))

    @classmethod
    def __subclasscheck__(cls, subclass: any) -> bool:
        return (
            hasattr(subclass, "get_curriculum") and callable(subclass.get_curriculum)
        ) and (
            hasattr(subclass, "post_curriculum") and callable(subclass.post_curriculum)
        )

    @abstractmethod
    def get_curriculum(
        self, document_ids: list[uuid.UUID], embedding: list[float], top_k: int = 5
    ) -> list[Citation]:
        """
        Get the curriculum from the database

        Args:
            document_id (str): The id of the document to use
            embedding (list[float]): The embedding of the question

        Returns:
            list[str]: The curriculum related to the question
        """
        pass

    @abstractmethod
    def get_page_range(
        self, document_id: uuid.UUID, page_num_start: int, page_num_end: int
    ) -> list[Citation]:
        """
        Retrieves a range of pages from the knowledge base.

        Args:
            document_id (str): The ID of the document to retrieve the pages from.
            page_num_start (int): The starting page number (inclusive).
            page_num_end (int): The ending page number (inclusive).

        Returns:
            list[Curriculum]: A list of Curriculum objects representing pieces of content, like sentences, the specified page range.
        """
        pass

    @abstractmethod
    def post_curriculum(
        self,
        curriculum: str,
        page_num: int,
        document_name: str,
        embedding: list[float],
        document_id: uuid.UUID,
    ) -> bool:
        """
        Post the curriculum to the database

        Args:
            curriculum (str): The curriculum to be posted
            embedding (list[float]): The embedding of the question

        Returns:
            bool: True if the curriculum was posted, False otherwise
        """
        pass

    @abstractmethod
    def post_video(
        self,
        video_url: str,
        timestamp: str,
        video_name: str,
        embedding: list[float],
        document_id: uuid.UUID,
    ) -> bool:
        """
        Post the video to the database

        Args:
            video_url (str): The video url to be posted
            embedding (list[float]): The embedding of the question

        Returns:
            bool: True if the video was posted, False otherwise
        """
        pass

    @abstractmethod
    def is_reachable(self) -> bool:
        """
        Check if the database is reachable

        Returns:
            bool: True if the database is reachable, False otherwise
        """
        pass

    @abstractmethod
    def get_all_pages(self, document_id: uuid.UUID) -> list[FullCitation]:
        """
        Retrieves all pages from the knowledge base.

        Args:
            document_id (str): The ID of the document to retrieve the pages from.

        Returns:
            list[FullCitation]: A list of FullCitation objects representing pieces of content, like sentences, from the specified document.
        """
        pass



class MockDatabase(Database):
    """
    A mock database for testing purposes, storing data in memory.
    Singleton implementation to ensure only one instance exists.
    """

    _instance = None  # Class variable to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If no instance exists, create one
            cls._instance = super(MockDatabase, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Initialize only once (avoiding resetting on subsequent calls)
        if not hasattr(self, "initialized"):
            self.data = []  # In-memory storage for mock data
            self.similarity_threshold = 0.7
            self.initialized = True

    def get_curriculum(
        self, document_id: uuid.UUID, embedding: list[float], top_k: int = 5
    ) -> list[Citation]:
        if not embedding:
            raise ValueError("Embedding cannot be None")

        results = []

        # Filter documents based on similarity and document_name
        for document in self.data:
            if document["documentId"] == str(document_id):
                similarity = cosine_similarity(embedding, document["embedding"])
                if similarity > self.similarity_threshold:
                    results.append(
                        Citation(
                            text=document["text"],
                            page_num=document["pageNum"],
                            document_name=document["documentName"],
                        )
                    )
        return results

    def get_video(
        self, document_id: uuid.UUID, embedding: list[float]
    ) -> list[Citation]:
        if not embedding:
            raise ValueError("Embedding cannot be None")

        results = []

        # Filter documents based on similarity and document_name
        for document in self.data:
            if document["documentId"] == str(document_id):
                similarity = cosine_similarity(embedding, document["embedding"])
                if similarity > self.similarity_threshold:
                    results.append(
                        Citation(
                            video_url=document["videoUrl"],
                            timestamp=document["timestamp"],
                            video_name=document["videoName"],
                        )
                    )
        return results

    def get_page_range(
        self, document_id: uuid.UUID, page_num_start: int, page_num_end: int
    ) -> list[Citation]:
        results = []

        # Filter documents based on document_name and page range
        for document in self.data:
            if (
                document["documentId"] == str(document_id)
                and page_num_start <= document["pageNum"] <= page_num_end
            ):
                results.append(
                    Citation(
                        text=document["text"],
                        page_num=document["pageNum"],
                        document_name=document["documentName"],
                    )
                )
        return results

    def post_curriculum(
        self,
        curriculum: str,
        page_num: int,
        document_name: str,
        embedding: list[float],
        document_id: str,
    ) -> bool:
        if not curriculum or not document_name or page_num is None or not embedding:
            raise ValueError("All parameters are required and must be valid")

        # Append a new document to the in-memory storage
        self.data.append(
            {
                "text": curriculum,
                "pageNum": page_num,
                "documentName": document_name,
                "embedding": embedding,
                "documentId": str(document_id),
            }
        )
        return True

    def post_video(
        self,
        video_url: str,
        timestamp: str,
        video_name: str,
        embedding: list[float],
        document_id: uuid.UUID,
    ) -> bool:
        if not video_url or not timestamp or not video_name or not embedding or not document_id:
            raise ValueError("All parameters are required and must be valid")

        # Append a new video document to the in-memory storage
        self.data.append(
            {
                "videoUrl": video_url,
                "timestamp": timestamp,
                "videoName": video_name,
                "embedding": embedding,
                "documentId": str(document_id),
            }
        )
        return True

    def is_reachable(self) -> bool:
        return True

    def get_all_pages(self, document_id: uuid.UUID) -> list[FullCitation]:
        results = []

        for document in self.data:
            if document["documentId"] == str(document_id):
                results.append(
                    FullCitation(
                        text=document["text"],
                        page_num=document["pageNum"],
                        document_name=document["documentName"],
                        document_id=document["documentId"],
                        embedding=document["embedding"],
                    )
                )
        return results
