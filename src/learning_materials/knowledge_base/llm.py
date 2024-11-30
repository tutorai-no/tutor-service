from langchain_core.language_models.llms import LLM

from langchain_openai import ChatOpenAI

from config import Config


def create_llm_model() -> ChatOpenAI:

    llm = ChatOpenAI(api_key=Config().API_KEY, temperature=0.0)
    return llm
