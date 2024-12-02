import logging
import uuid

from learning_materials.knowledge_base.response_formulation import create_llm_model
from learning_materials.knowledge_base.rag_service import get_page_range
from learning_materials.learning_resources import Compendium, Citation


logger = logging.getLogger(__name__)


def generate_compendium(document_id: uuid.UUID, start: int, end: int) -> Compendium:
    """
    Generates a compendium for the document
    """

    # Retrieve the pages from the database
    context_pages: list[Citation] = get_page_range(document_id, start, end)
    logger.info(f"Generating compendium for document {document_id}")
    # Generate the compendium
    summaries = ""
    key_concepts = []

    llm = create_llm_model()
    document_name = ""
    for page in context_pages:
        document_name = page.document_name
        # Extract the key concepts and summaries from the page
        # Append the key concepts and summaries to the lists

        concept_template, summary_template = _generate_compendium_template(page.text)
        concept = llm.invoke([{"role": "system", "content": concept_template}])
        summary = llm.invoke([{"role": "system", "content": summary_template}])
        key_concepts.extend(concept.content.split("|"))
        summaries += summary.content

    compendium = Compendium(
        document_name=document_name,
        start_page=start,
        end_page=end,
        key_concepts=key_concepts,
        summary=summaries,
    )
    return compendium


def _generate_compendium_template(text: str) -> tuple[str, str]:
    """
    Generate a compendium template for the text
    """

    key_concepts_format = "France: A large country in westeren Europe | Java Virtual Machine: A microarchitecture that the Java programming language uses | Deforestation: The process in which a forest is destroyed by humans"
    key_concepts_template = f"Generate a list of key concepts from the given text: '''{text}'''. Use only the most important concepts. Do not include any unnecessary information. Use only the information that is in the text. Use the following format: {key_concepts_format}"

    summary_template = f"Generate a summary of the given text: '''{text}'''. Use only the most important information. Do not include any unnecessary information. Use only the information that is in the text."

    return key_concepts_template, summary_template
