from langchain_openai import ChatOpenAI

from config import Config


def create_llm_model() -> ChatOpenAI:

    llm = ChatOpenAI(api_key=Config().API_KEY, model=Config().GPT_MODEL, temperature=0.0)
    return llm
