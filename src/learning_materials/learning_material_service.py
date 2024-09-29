""" The service module contains the business logic of the application. """

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
    RagAnswer,
)


def process_flashcards(document_name: str, start: int, end: int) -> list[Flashcard]:
    """
    Generate flashcards for a specific page range and file
    """
    print("[INFO] Trying to find relevant document", flush=True)
    pages = get_page_range(document_name, start, end)
    flashcards: list[Flashcard] = []
    print("[INFO] Generating flashcards", flush=True)

    # Use ThreadPoolExecutor to parallelize the API calls
    with ThreadPoolExecutor() as executor:
        # Schedule the execution of each page processing and hold the future objects
        futures = [executor.submit(generate_flashcards, page) for page in pages]

        # As each future completes, gather the results
        for future in as_completed(futures):
            flashcards.extend(future.result())

    return flashcards



def process_answer(
    documents: list[str], user_question: str, chat_history: list[dict[str, str]]
) -> RagAnswer:

    # Get a list of relevant contexts from the database
    curriculum = []
    for document_name in documents:
        curriculum.extend(get_context(document_name, user_question))

    # Use this list to generate a response
    answer_GPT = response_formulation(user_question, curriculum, chat_history)

    answer = RagAnswer(answer_GPT, curriculum)
    return answer

