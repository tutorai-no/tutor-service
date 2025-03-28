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
    def __init__(self, path=".env", gpt_model="gpt-4o-mini"):
        self.path = path
        self.GPT_MODEL = os.getenv(key="GPT_MODEL", default=gpt_model)
        self.API_KEY = os.getenv("OPENAI_API_KEY")
        self.MONGODB_URI = os.getenv("MONGODB_URI")
        self.MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")
        self.MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
        self.RAG_DATABASE_SYSTEM = os.getenv("RAG_DATABASE_SYSTEM", "mongodb")
        self.AZURE_STORAGE_CONNECTION_STRING = os.getenv(
            "AZURE_STORAGE_CONNECTION_STRING"
        )
        self.AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
        self.BASE_URL_SCRAPER = os.getenv("BASE_URL_SCRAPER")
        self.BASE_URL_FRONTEND = os.getenv("BASE_URL_FRONTEND", "http://localhost:8080")
