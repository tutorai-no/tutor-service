
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from flashcards.learning_resources import Flashcard, Page
from config import Config
from dataclasses import dataclass
from typing import Protocol

model = ChatOpenAI(temperature=temperature, api_key=Config().API_KEY)
flashcard_parser = PydanticOutputParser(pydantic_object=Flashcard)

def generate_flashcards(page: Page) -> list[Flashcard]:
    template = _generate_template(page.text)
    prompt = PromptTemplate(
        template="Answer the user query.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": flashcard_parser.get_format_instructions()},
    )

    # Creating the LangChain with prompt, model, and parser
    chain = prompt | model | flashcard_parser

    # Generating the flashcards
    flashcards = chain.invoke({"query": template})

    # Ensuring page_num and pdf_name are set correctly
    for flashcard in flashcards:
        flashcard.page_num = page.page_num
        flashcard.pdf_name = page.pdf_name

    return flashcards

def _generate_template(context: str) -> str:
    """
    Returns a template with the correct flashcard and prompt format which can be used to generate flashcards using the context

    Args:
        context (str): The sample text to be used

    Returns:
        str: The template with the correct flashcard and prompt format which can be used to generate flashcards using the context
    """

    example = f"Front: Which year was the person born? - Back: 1999 | Front: At what temperature does water boil? - Back: 100 degrees celsius | Front: MAC - Back: Message Authentication Code"
    template = f"Create a set of flashcards using the following format: {example} from the following text: {context}. Use only information from the text to generate the flashcards. Use only the given format. Do not use line breaks. Do not use any other format"

    return template


def parse_for_anki(flashcards: list[Flashcard]) -> str:
    """
    Returns a string with the flashcards in the correct format for Anki

    Correct format: front:back
    Example: "apple:banana"

    Args:
        flashcards (list[Flashcard]): The flashcards to be parsed

    Returns:
        str: A string with the flashcards in the correct format for Anki
    """
    num_elements = len(flashcards)
    text = ""
    separator = "\n"

    for i in range(num_elements):
        front = flashcards[i].front
        back = flashcards[i].back

        text += front + ":" + back + separator

    return text
