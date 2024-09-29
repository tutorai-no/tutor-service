from learning_materials.knowledge_base.db_interface import Database, MockDatabase, MongoDB
from learning_materials.knowledge_base.embeddings import EmbeddingsModel, OpenAIEmbedding


def create_database(database_system: str = "mongodb") -> Database:
    match database_system.lower():
        case "mongodb":
            return MongoDB()
        case "mock":
            return MockDatabase()
        case _:
            raise ValueError(f"Database system {database_system} not supported")


def create_embeddings_model(embeddings_model: str = "openai") -> EmbeddingsModel:
    match embeddings_model.lower():
        case "openai":
            return OpenAIEmbedding()
        case _:
            raise ValueError(f"Embeddings model {embeddings_model} not supported")
