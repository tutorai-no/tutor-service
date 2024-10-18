import os
from dotenv import load_dotenv

"""
This module provides the Config class to manage configuration variables
from environment files. It also supports fetching test cases 
ifthe configuration is loaded from a test environment file.
"""

# a class for defining the config variables
load_dotenv("../.env")


class Config:
    def __init__(self, path=".env", gpt_model="gpt-3.5-turbo"):
        self.path = path
        self.GPT_MODEL = os.getenv(key="GPT_MODEL", default=gpt_model)
        self.API_KEY = os.getenv("OPENAI_API_KEY")
        self.MONGODB_URI = os.getenv("MONGODB_URI")
        self.RAG_DATABASE_SYSTEM = os.getenv("RAG_DATABASE_SYSTEM", "mongodb")
