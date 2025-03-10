"""Base embedding provider implementation.

This module provides the base class for embedding providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from pepperpy.rag.errors import EmbeddingError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers.

    This class defines the interface that all embedding providers must implement.
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize base embedding provider.

        Args:
            model_name: Optional name of the model to use
        """
        self.model_name = model_name

    @abstractmethod
    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Internal method to embed texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings for each text

        Raises:
            EmbeddingError: If there is an error during embedding
        """
        ...

    async def embed_query(self, query: str) -> List[float]:
        """Embed a query string.

        Args:
            query: The query to embed

        Returns:
            The query embedding

        Raises:
            EmbeddingError: If there is an error during embedding
        """
        try:
            embeddings = await self._embed_texts([query])
            return embeddings[0]
        except Exception as e:
            raise EmbeddingError(f"Error embedding query: {e}")

    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Embed a list of documents.

        Args:
            documents: The documents to embed

        Returns:
            The document embeddings

        Raises:
            EmbeddingError: If there is an error during embedding
        """
        try:
            return await self._embed_texts(documents)
        except Exception as e:
            raise EmbeddingError(f"Error embedding documents: {e}")

    def __repr__(self) -> str:
        """Get string representation of provider.

        Returns:
            String representation
        """
        return f"{self.__class__.__name__}(model_name={self.model_name})"
