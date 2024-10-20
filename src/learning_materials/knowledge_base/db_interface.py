from abc import ABC, abstractmethod
import uuid
from config import Config
from pymongo import MongoClient
import logging

from learning_materials.learning_resources import Citation
from learning_materials.knowledge_base.embeddings import (
    OpenAIEmbedding,
    cosine_similarity,
)

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
        self, document_id: uuid.UUID, embedding: list[float]
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


class MongoDB(Database):
    def __init__(self):
        self.client = MongoClient(Config().MONGODB_URI)
        self.db = self.client["test-curriculum-database"]
        self.collection = self.db["test-curriculum-collection"]
        self.similarity_threshold = 0.7
        self.embeddings = OpenAIEmbedding()

    def get_curriculum(
        self, document_id: uuid.UUID, embedding: list[float]
    ) -> list[Citation]:
        # Checking if embedding consists of decimals or "none"
        if not embedding:
            raise ValueError("Embedding cannot be None")

        # Define the MongoDB query that utilizes the search index "embeddings".
        query = {
            "$vectorSearch": {
                "index": "embeddings",
                "path": "embedding",
                "queryVector": embedding,
                # MongoDB suggests using numCandidates=10*limit or numCandidates=20*limit
                "numCandidates": 30,
                "limit": 3,
            }
        }

        # Execute the query
        documents = self.collection.aggregate([query])

        if not documents:
            raise ValueError("No documents found")

        # Convert the documents to a list
        documents = list(documents)

        results = []

        # Filter out the documents with low similarity
        for document in documents:
            if document["documentId"] != str(document_id):
                continue

            if (
                cosine_similarity(embedding, document["embedding"])
                > self.similarity_threshold
            ):
                results.append(
                    Citation(
                        text=document["text"],
                        page_num=document["pageNum"],
                        document_name=document["documentName"],
                    )
                )

        return results

    def get_page_range(
        self, document_id: uuid.UUID, page_num_start: int, page_num_end: int
    ) -> list[Citation]:
        # Get the curriculum from the database
        cursor = self.collection.find(
            {
                "documentId": str(document_id),
                "pageNum": {"$gte": page_num_start, "$lte": page_num_end},
            }
        )

        if not cursor:
            raise ValueError("No documents found")

        results = []

        for document in cursor:
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
        document_id: uuid.UUID,
    ) -> bool:
        if not curriculum:
            raise ValueError("Curriculum cannot be None")

        if page_num is None:
            raise ValueError("Page number cannot be None")

        if document_name is None:
            raise ValueError("Paragraph number cannot be None")

        if not embedding:
            raise ValueError("Embedding cannot be None")

        if not document_name:
            raise ValueError("Document name cannot be None")

        if not document_id:
            raise ValueError("Document ID cannot be None")

        try:
            # Insert the curriculum into the database with metadata
            self.collection.insert_one(
                {
                    "text": curriculum,
                    "pageNum": page_num,
                    "documentName": document_name,
                    "embedding": embedding,
                    "documentId": str(document_id),
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error posting curriculum: {e}")
            return False


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
                            text=document["text"],
                            page_num=document["pageNum"],
                            document_name=document["documentName"],
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
