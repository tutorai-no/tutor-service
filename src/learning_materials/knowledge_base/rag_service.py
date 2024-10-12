""" Retrieval Augmented Generation Service """

from learning_materials.learning_resources import Citation
from learning_materials.knowledge_base.db_interface import Database
from learning_materials.knowledge_base.embeddings import EmbeddingsModel
from learning_materials.knowledge_base.factory import create_database
from learning_materials.knowledge_base.factory import create_embeddings_model
from config import Config

db_system = Config().RAG_DATABASE_SYSTEM
db: Database = create_database(db_system)
embeddings: EmbeddingsModel = create_embeddings_model()


def get_context(document_name: str, query: str) -> list[Citation]:
    """
    Get the context of the query

    Args:
        query (str): The query to get the context of

    Returns:
        list[str]: The context of the query
    """
    embedding = embeddings.get_embedding(query)
    context = db.get_curriculum(document_name, embedding)
    return context


def get_page_range(
    document_name: str,
    page_num_start: int,
    page_num_end: int,
) -> list[Citation]:
    """
    Get the context of the query

    Args:
        document_name (str): The name of the pdf
        page_num_start (int): The start page number
        page_num_end (int): The end page number
    Returns:
        list[str]: The context of the query
    """
    return db.get_page_range(document_name, page_num_start, page_num_end)


def post_context(
    context: str,
    page_num: int,
    document_name: str,
) -> bool:
    """
    Post the context to the database

    Args:
        context (str): The context to be posted
        page_num (int): The page number of the context
        paragraph_num (int): The paragraph number of the context

    Returns:
        bool: True if the context was posted, False otherwise
    """

    embedding = embeddings.get_embedding(context)
    return db.post_curriculum(context, page_num, document_name, embedding)
