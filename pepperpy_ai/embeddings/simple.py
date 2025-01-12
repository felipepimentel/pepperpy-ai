"""Simple embeddings implementation."""

from typing import List

import numpy as np

from .base import EmbeddingsConfig
from .client import EmbeddingsClient
from .types import EmbeddingVector


class SimpleEmbeddings(EmbeddingsClient):
    """A simple embeddings implementation for testing and demonstration purposes."""

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize the simple embeddings client.

        Args:
            config: The embeddings configuration.
        """
        super().__init__(config)
        self._dimension = config.dimension or 384  # Default dimension

    async def embed_text(self, text: str) -> EmbeddingVector:
        """Generate a simple embedding for a text string.

        This is a mock implementation that generates random vectors.
        It should only be used for testing and demonstration purposes.

        Args:
            text: The text to embed.

        Returns:
            A numpy array representing the embedding vector.
        """
        # Generate a deterministic random vector based on the text hash
        text_hash = hash(text)
        rng = np.random.RandomState(text_hash)
        vector = rng.randn(self._dimension)
        # Normalize the vector
        return vector / np.linalg.norm(vector)

    async def embed_texts(self, texts: List[str]) -> List[EmbeddingVector]:
        """Generate simple embeddings for a list of texts.

        Args:
            texts: The list of texts to embed.

        Returns:
            A list of numpy arrays representing the embedding vectors.
        """
        return [await self.embed_text(text) for text in texts] 