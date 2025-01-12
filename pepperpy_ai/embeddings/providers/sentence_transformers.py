"""Sentence Transformers embeddings provider implementation."""

from typing import Any

from ...config.embeddings import EmbeddingsConfig
from ..base import BaseEmbeddingsProvider, EmbeddingResult


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
        """Initialize provider resources."""
        if not self.is_initialized:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers package is required for this provider"
                ) from e

            self._model = SentenceTransformer(self.config.model)
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.is_initialized:
            self._model = None
            self._initialized = False

    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            EmbeddingResult: Generated embeddings.
        """
        self._ensure_initialized()
        embeddings = self._model.encode(text)
        return EmbeddingResult(
            embeddings=embeddings.tolist(),
            metadata={"model": self.config.model},
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            list[EmbeddingResult]: Generated embeddings for each text.
        """
        self._ensure_initialized()
        embeddings = self._model.encode(texts)
        return [
            EmbeddingResult(
                embeddings=embedding.tolist(),
                metadata={"model": self.config.model},
            )
            for embedding in embeddings
        ]
