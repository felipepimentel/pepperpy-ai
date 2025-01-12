"""Simple embeddings provider implementation."""

from ...config.embeddings import EmbeddingsConfig
from ..base import BaseEmbeddingsProvider, EmbeddingResult


class SimpleEmbeddingsProvider(BaseEmbeddingsProvider):
    """Simple embeddings provider for testing and demonstration.

    A basic implementation that provides embedding functionality for testing
    and demonstration purposes.
    """

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration.
        """
        super().__init__(config)
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

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
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.is_initialized:
            self._initialized = False

    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            EmbeddingResult: Generated embeddings.
        """
        self._ensure_initialized()
        return EmbeddingResult(
            embeddings=[0.0] * 10,
            metadata={"model": "simple", "dimensions": 10},
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            list[EmbeddingResult]: Generated embeddings for each text.
        """
        self._ensure_initialized()
        return [
            EmbeddingResult(
                embeddings=[0.0] * 10,
                metadata={"model": "simple", "dimensions": 10},
            )
            for _ in texts
        ]
