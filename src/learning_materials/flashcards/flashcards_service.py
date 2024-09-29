from pydantic import BaseModel

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from learning_materials.learning_resources import Flashcard, Page
from config import Config


class FlashcardWrapper(BaseModel):
    flashcards: list[Flashcard]


model = ChatOpenAI(temperature=0, api_key=Config().API_KEY)
flashcard_parser = PydanticOutputParser(pydantic_object=FlashcardWrapper)

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
    wrapper = chain.invoke({"query": template})
    flashcards = wrapper.flashcards

    # Ensuring page_num and pdf_name are set correctly
    for flashcard in flashcards:
        flashcard.page_num = page.page_num
        flashcard.pdf_name = page.pdf_name

    return flashcards

def _generate_template(context: str) -> str:
    """
    Returns a template with the correct flashcard and prompt format which can be used to generate flashcards using the context.
    
    Args:
        context (str): The sample text to be used

    Returns:
        str: The template with the correct flashcard and prompt format which can be used to generate flashcards using the context
    """

    template = (
        f"""Create flashcards from the provided text using any of the following formats: Standard Q&A, Vocabulary, Fill-in-the-Blank, Multiple Choice, and True/False. Choose the best format(s) based on the content of the text. Follow these examples:
        1. Q&A:
        * Front: "What is the capital of France?"
        * Back: "Paris"

        2. Vocabulary:
        * Front: "Photosynthesis"
        * Back: "The process by which plants use sunlight to make food."

        3. Fill-in-the-Blank:
        * Front: "The largest ocean is ____."
        * Back: "Pacific Ocean"

        4. Multiple Choice:
        * Front: "Which planet is the Red Planet? (a) Venus (b) Mars (c) Jupiter"
        * Back: "(b) Mars"

        5. True/False:
        * Front: "The Eiffel Tower is in Paris. True or False?"
        * Back: "True"

        Generate flashcards that best represent the content of the text. 
        Use only the formats listed above, and ensure each flashcard is clear, relevant, and directly derived from the text."
        """
        f"\n\nText:\n{context}"
    )
    
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
