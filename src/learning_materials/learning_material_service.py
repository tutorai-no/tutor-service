""" The service module contains the business logic of the application. """

import logging

from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

from learning_materials.knowledge_base.response_formulation import (
    response_formulation,
)
from learning_materials.knowledge_base.rag_service import (
    get_context,
    get_page_range,
)
from learning_materials.flashcards.flashcards_service import generate_flashcards
from learning_materials.learning_resources import (
    Flashcard,
    Citation,
    RagAnswer,
)

logger = logging.getLogger(__name__)


def process_flashcards(document_id: uuid.UUID, start: int, end: int) -> list[Flashcard]:
    """
    Generate flashcards for a specific page range and file
    """
    logger.info("Trying to find relevant document")
    pages = get_page_range(document_id, start, end)
    logger.info(f"Found {len(pages)} pages in the document")
    flashcards: list[Flashcard] = []
    logger.info(f"Generating flashcards for {document_id} from page {start} to {end}")

    # Use ThreadPoolExecutor to parallelize the API calls
    with ThreadPoolExecutor() as executor:
        # Schedule the execution of each page processing and hold the future objects
        futures = [executor.submit(generate_flashcards, page) for page in pages]

        # As each future completes, gather the results
        for future in as_completed(futures):
            flashcards.extend(future.result())

    return flashcards


def process_answer(
    document_ids: list[uuid.UUID],
    user_question: str,
    chat_history: list[dict[str, str]],
) -> RagAnswer:
    """
    Process the user's question and return a response based on the context of the documents and chat history.
    """
    # Retrieve relevant contexts for the provided documents
    curriculum: list[Citation] = []
    for document_id in document_ids:
        curriculum.extend(get_context(document_id, user_question))

    # Handle case when no context is available
    if len(curriculum) == 0:
        answer_content = (
            "I'm sorry, but I don't have enough information to answer your question."
        )
    else:
        answer_content = response_formulation(user_question, curriculum, chat_history)

    # Create a response object
    answer = RagAnswer(content=answer_content, citations=curriculum)

    # Add the assistant's response to the chat history
    chat_history.append({
        "role": "assistant",
        "content": answer.content,
        "citations": [citation.model_dump() for citation in answer.citations],
    })

    return answer