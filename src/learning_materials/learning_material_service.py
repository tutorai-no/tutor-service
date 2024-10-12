""" The service module contains the business logic of the application. """

import logging

from concurrent.futures import ThreadPoolExecutor, as_completed

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

def process_flashcards(document_name: str, start: int, end: int) -> list[Flashcard]:
    """
    Generate flashcards for a specific page range and file
    """
    logger.info("Trying to find relevant document")
    pages = get_page_range(document_name, start, end)
    logger.info(f"Found {len(pages)} pages in the document")
    flashcards: list[Flashcard] = []
    logger.info(f"Generating flashcards for {document_name} from page {start} to {end}")

    # Use ThreadPoolExecutor to parallelize the API calls
    with ThreadPoolExecutor() as executor:
        # Schedule the execution of each page processing and hold the future objects
        futures = [executor.submit(generate_flashcards, page) for page in pages]

        # As each future completes, gather the results
        for future in as_completed(futures):
            flashcards.extend(future.result())

    return flashcards




def process_answer(
    documents: list[str],
    user_question: str,
    chat_history: list[dict[str, str]]
) -> RagAnswer:

    # Get a list of relevant contexts from the database
    curriculum: list[Citation] = []
    for document_name in documents:
        curriculum.extend(get_context(document_name, user_question))

    # Handle case when no context is available
    if len(curriculum) == 0:
        answer_content = "I'm sorry, but I don't have enough information to answer your question."
    else:
        answer_content = response_formulation(user_question, curriculum, chat_history)
        

    answer = RagAnswer(content=answer_content, citations=curriculum)
    return answer
