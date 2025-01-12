"""Simple embeddings provider implementation."""

from typing import List

import numpy as np

from ..base import EmbeddingsConfig
from .base import BaseEmbeddingsProvider


class SimpleEmbeddingsProvider(BaseEmbeddingsProvider):
    """A simple embeddings provider implementation for testing and demonstration purposes."""

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize the simple embeddings provider.

        Args:
            config: The embeddings configuration.
        """
        super().__init__(config)
        self._dimension = config.dimension or 384  # Default dimension

    async def initialize(self) -> None:
        """Initialize the provider. No-op for this simple implementation."""
        pass

    async def cleanup(self) -> None:
        """Cleanup provider resources. No-op for this simple implementation."""
        pass

    async def embed(self, text: str) -> List[float]:
        """Generate a simple embedding for a text string.

        This is a mock implementation that generates random vectors.
        It should only be used for testing and demonstration purposes.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        # Generate a deterministic random vector based on the text hash
        text_hash = hash(text)
        rng = np.random.RandomState(text_hash)
        vector = rng.randn(self._dimension)
        # Normalize the vector
        normalized = vector / np.linalg.norm(vector)
        return normalized.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate simple embeddings for a list of texts.

        Args:
            texts: The list of texts to embed.

        Returns:
            A list of float lists representing the embedding vectors.
        """
        return [await self.embed(text) for text in texts] 