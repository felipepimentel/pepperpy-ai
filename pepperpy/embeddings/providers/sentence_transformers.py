"""Sentence Transformers embeddings provider implementation."""

from typing import TYPE_CHECKING, Any

from ...config.embeddings import EmbeddingsConfig
from ...exceptions import DependencyError
from ..base import BaseEmbeddingsProvider

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
else:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        SentenceTransformer = None


class SentenceTransformersProvider(BaseEmbeddingsProvider):
    """Sentence Transformers embeddings provider.

    This provider uses the sentence-transformers library to generate embeddings.
    """

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration.
        """
        super().__init__(config)
        self._initialized = False
        self._model: Any = None

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized and self._model is not None

    def _ensure_initialized(self) -> None:
        """Ensure provider is initialized.

        Raises:
            RuntimeError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized")

    async def initialize(self) -> None:
        """Initialize provider resources.

        Raises:
            DependencyError: If required packages are not installed.
        """
        if not self.is_initialized:
            if SentenceTransformer is None:
                raise DependencyError(
                    "Required packages not installed. "
                    "Please install extras: pip install pepperpy-ai[embeddings]",
                    package="sentence-transformers",
                )

            try:
                model_name = self.config["model"]
                device = self.config.get("device", "cpu")

                self._model = SentenceTransformer(model_name, device=device)
                self._initialized = True
            except ImportError as e:
                raise DependencyError(
                    "Required packages not installed. "
                    "Please install extras: pip install pepperpy-ai[embeddings]",
                    package="sentence-transformers",
                ) from e

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.is_initialized:
            self._model = None
            self._initialized = False

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            list[float]: Generated embeddings.

        Raises:
            RuntimeError: If provider is not initialized.
        """
        self._ensure_initialized()
        if self._model is None:
            raise RuntimeError("Model not initialized")
        embeddings = self._model.encode([text])
        return [float(x) for x in embeddings[0]]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            list[list[float]]: Generated embeddings for each text.

        Raises:
            RuntimeError: If provider is not initialized.
        """
        self._ensure_initialized()
        if self._model is None:
            raise RuntimeError("Model not initialized")
        embeddings = self._model.encode(texts)
        return [[float(x) for x in embedding] for embedding in embeddings]
