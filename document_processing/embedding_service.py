"""
Embedding generation service for document processing.
"""

import logging
from typing import Any

from django.conf import settings

import numpy as np

logger = logging.getLogger(__name__)

# Optional imports
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not available")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("openai not available")
    openai = None
    OPENAI_AVAILABLE = False


class EmbeddingService:
    """
    Service for generating text embeddings using various models.
    """

    def __init__(self):
        """Initialize embedding service with configured model."""
        self.model_type = getattr(
            settings, "EMBEDDING_MODEL_TYPE", "sentence_transformers"
        )
        self.model_name = getattr(settings, "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the embedding model."""
        try:
            if self.model_type == "sentence_transformers":
                if not SENTENCE_TRANSFORMERS_AVAILABLE:
                    raise ImportError("sentence-transformers not available")
                logger.info(f"Loading SentenceTransformer model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("SentenceTransformer model loaded successfully")

            elif self.model_type == "openai":
                if not OPENAI_AVAILABLE:
                    raise ImportError("openai not available")
                # OpenAI embeddings via API
                openai_key = getattr(settings, "OPENAI_API_KEY", None)
                if not openai_key:
                    raise ValueError("OPENAI_API_KEY required for OpenAI embeddings")
                openai.api_key = openai_key
                self.model = "openai"  # Use string identifier
                logger.info("OpenAI embeddings configured")

            else:
                raise ValueError(f"Unsupported embedding model type: {self.model_type}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            self.model = None

    def generate_embedding(self, text: str) -> list[float] | None:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of embedding values or None if failed
        """
        if not self.model:
            logger.error("No embedding model available")
            return None

        try:
            if self.model_type == "sentence_transformers":
                embedding = self.model.encode(text, convert_to_tensor=False)
                return embedding.tolist()

            elif self.model_type == "openai":
                response = openai.Embedding.create(model=self.model_name, input=text)
                return response["data"][0]["embedding"]

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float] | None]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embeddings (or None for failed ones)
        """
        if not self.model:
            logger.error("No embedding model available")
            return [None] * len(texts)

        try:
            if self.model_type == "sentence_transformers":
                embeddings = self.model.encode(texts, convert_to_tensor=False)
                return [embedding.tolist() for embedding in embeddings]

            elif self.model_type == "openai":
                # Process in batches for OpenAI API
                batch_size = 100  # OpenAI limit
                all_embeddings = []

                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    response = openai.Embedding.create(
                        model=self.model_name, input=batch
                    )
                    batch_embeddings = [item["embedding"] for item in response["data"]]
                    all_embeddings.extend(batch_embeddings)

                return all_embeddings

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return [None] * len(texts)

    def calculate_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between 0 and 1
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Cosine similarity
            similarity = np.dot(vec1, vec2) / (
                np.linalg.norm(vec1) * np.linalg.norm(vec2)
            )

            # Convert to 0-1 range
            return (similarity + 1) / 2

        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0

    def find_similar_chunks(
        self,
        query_embedding: list[float],
        chunk_embeddings: list[dict[str, Any]],
        threshold: float = 0.7,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find chunks similar to a query embedding.

        Args:
            query_embedding: Query embedding vector
            chunk_embeddings: List of dicts with 'embedding' and metadata
            threshold: Minimum similarity threshold
            top_k: Maximum number of results

        Returns:
            List of similar chunks with similarity scores
        """
        try:
            similarities = []

            for chunk in chunk_embeddings:
                if "embedding" not in chunk or not chunk["embedding"]:
                    continue

                similarity = self.calculate_similarity(
                    query_embedding, chunk["embedding"]
                )

                if similarity >= threshold:
                    chunk_with_score = chunk.copy()
                    chunk_with_score["similarity"] = similarity
                    similarities.append(chunk_with_score)

            # Sort by similarity (descending) and return top k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Error finding similar chunks: {str(e)}")
            return []

    def get_model_info(self) -> dict[str, Any]:
        """
        Get information about the current embedding model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "is_loaded": self.model is not None,
            "embedding_dimension": self._get_embedding_dimension(),
        }

    def _get_embedding_dimension(self) -> int | None:
        """Get the dimension of embeddings produced by the model."""
        if not self.model:
            return None

        try:
            # Test with a simple text
            test_embedding = self.generate_embedding("test")
            return len(test_embedding) if test_embedding else None
        except Exception:
            return None


# Global service instance
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    return embedding_service
