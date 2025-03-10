"""Mock embedding provider implementation.

This module provides a mock embedding provider for testing purposes.
"""

import hashlib
from typing import List, Optional

import numpy as np

from pepperpy.rag.errors import EmbeddingError
from pepperpy.rag.providers.embedding.base import BaseEmbeddingProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Default embedding dimension
DEFAULT_DIM = 384


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Mock embedding provider for testing.

    This provider generates deterministic mock embeddings based on text hashing.
    """

    def __init__(
        self,
        dimension: int = DEFAULT_DIM,
        model_name: Optional[str] = None,
    ):
        """Initialize mock embedding provider.

        Args:
            dimension: Dimension of the embeddings to generate
            model_name: Optional name for the mock model
        """
        super().__init__(model_name=model_name or f"mock-{dimension}d")
        self.dimension = dimension

    def _text_to_seed(self, text: str) -> int:
        """Convert text to a deterministic seed value.

        Args:
            text: Input text

        Returns:
            Seed value for random number generation
        """
        # Get hash of text
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        # Convert first 8 bytes to integer
        return int(text_hash[:16], 16)

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate a deterministic embedding for a text.

        Args:
            text: Input text

        Returns:
            Generated embedding vector
        """
        # Set random seed based on text hash
        seed = self._text_to_seed(text)
        rng = np.random.RandomState(seed)

        # Generate random vector
        vector = rng.normal(size=self.dimension)

        # Normalize to unit length
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of mock embeddings for each text

        Raises:
            EmbeddingError: If there is an error during embedding
        """
        try:
            return [self._generate_embedding(text) for text in texts]
        except Exception as e:
            raise EmbeddingError(f"Error in mock embedding provider: {e}")
