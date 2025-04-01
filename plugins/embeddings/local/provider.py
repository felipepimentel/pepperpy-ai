"""Local embeddings provider implementation using sentence-transformers."""

import logging
from typing import Any, Dict, List, Optional

from pepperpy.core.errors import EmbeddingError
from pepperpy.plugins.plugin import PepperpyPlugin

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class LocalProvider(PepperpyPlugin):
    """Local implementation of embeddings provider using sentence-transformers.

    This provider runs completely offline without requiring any API keys.
    It uses the sentence-transformers library which provides high quality
    multilingual embeddings.
    """

    name = "local"
    version = "0.1.0"
    description = "Local embeddings provider using sentence-transformers"
    author = "PepperPy Team"

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        **kwargs: Any,
    ) -> None:
        """Initialize the provider.

        Args:
            model_name: Name of the sentence-transformer model to use
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.model_name = model_name
        self._model: Optional[Any] = None

    def _ensure_initialized(self) -> None:
        """Ensure the model is initialized.

        Raises:
            EmbeddingError: If initialization fails
        """
        if not self._model:
            try:
                if SentenceTransformer is None:
                    raise ImportError("sentence-transformers is not installed")
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                raise EmbeddingError(f"Failed to initialize model: {e}")

    async def initialize(self) -> None:
        """Initialize the provider."""
        self._ensure_initialized()
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._model = None
        self.initialized = False

    def _get_embedding_function(self) -> Any:
        """Get the embedding function.

        Returns:
            The embedding function

        Raises:
            EmbeddingError: If model is not initialized
        """
        self._ensure_initialized()
        if not self._model:
            raise EmbeddingError("Model not initialized")
        return self._model

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text.

        Args:
            text: Text to embed

        Returns:
            List of embedding values

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            model = self._get_embedding_function()
            embeddings = model.encode(text)
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            model = self._get_embedding_function()
            embeddings = model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}")

    async def embed_query(self, query: str) -> List[float]:
        """Generate embeddings for a query.

        Args:
            query: Query text to embed

        Returns:
            List of embedding values

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            model = self._get_embedding_function()
            embeddings = model.encode(query)
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}")

    def get_dimensions(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            Number of dimensions

        Raises:
            EmbeddingError: If model is not initialized
        """
        try:
            model = self._get_embedding_function()
            return model.get_sentence_embedding_dimension()
        except Exception as e:
            raise EmbeddingError(f"Failed to get dimensions: {e}")

    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration.

        Returns:
            Provider configuration
        """
        return {
            "model_name": self.model_name,
            "is_initialized": self._model is not None,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "supports_batching": True,
            "supports_multilingual": True,
            "requires_gpu": False,
            "is_local": True,
            "max_sequence_length": 512,
        }

    def get_embedding_function(self) -> Any:
        """Get the embedding function.

        Returns:
            The embedding function

        Raises:
            EmbeddingError: If model is not initialized
        """
        return self._get_embedding_function()
