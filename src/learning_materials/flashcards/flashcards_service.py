from pydantic import BaseModel

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from learning_materials.learning_resources import Flashcard, Citation
from config import Config


class FlashcardWrapper(BaseModel):
    flashcards: list[Flashcard]


model = ChatOpenAI(temperature=0, api_key=Config().API_KEY)
flashcard_parser = PydanticOutputParser(pydantic_object=FlashcardWrapper)


def generate_flashcards(page: Citation, language: str = "en") -> list[Flashcard]:
    template = _generate_template(page.text, language)
    prompt = PromptTemplate(
        template="Answer the user query.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={
            "format_instructions": flashcard_parser.get_format_instructions()
        },
    )

    # Creating the LangChain with prompt, model, and parser
    chain = prompt | model | flashcard_parser

    # Generating the flashcards
    wrapper = chain.invoke({"query": template})
    flashcards = wrapper.flashcards

    # Ensuring page_num and document_name are set correctly
    for flashcard in flashcards:
        flashcard.page_num = page.page_num
        flashcard.document_name = page.document_name

    return flashcards


def _generate_template(context: str, language: str = "en") -> str:
    """
    Returns a template with the correct flashcard and prompt format which can be used to generate flashcards using the context.

    Args:
        context (str): The sample text to be used

    Returns:
        str: The template with the correct flashcard and prompt format which can be used to generate flashcards using the context
    """

    template = (
        f"""Create flashcards from the provided text using any of the following formats: Standard Q&A, Vocabulary, Fill-in-the-Blank, Multiple Choice, and True/False. Choose the best format(s) based on the content of the text.  
        
        The following examples are provided in English solely for guidance on the desired format. Do not include these examples in your final output:
        
        1. Q&A:
        * Front: "What is a question?"
        * Back: "This is an answer."
        
        2. Vocabulary:
        * Front: "Word"
        * Back: "This is the definition."
        
        3. Fill-in-the-Blank:
        * Front: "The ... is ____."
        * Back: "The ... is <answer>."
        
        4. Multiple Choice:
        * Front: "<question> (a) <option1> (b) <option2> (c) <option3>"
        * Back: "(x) <correct answer>"
        
        5. True/False:
        * Front: "This is a statement."
        * Back: "True/False"
        
        Generate all flashcards in the language corresponding to the language code "{language}". If this code represents a language other than English, ensure that every flashcard (both front and back) is entirely in that language.

        The same information shall not be repeated in multiple flashcards. Each flashcard should focus on a unique piece of information or concept. Avoid generating flashcards that are too similar to each other.
        
        Generate flashcards that best represent the content of the text. Do NOT ask questions about meta data from the text, like author or publisher. Each flashcard should be clear, directly derived from the text, and formatted using only the styles listed above.
        """
        f"\n\nText:\n{context}"
    )
    print("TEMPLATEABC", template)
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
