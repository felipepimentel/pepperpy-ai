"""Numpy-based embeddings provider for basic text embeddings."""

import hashlib
from typing import Any, List, Union

import numpy as np

from pepperpy.embeddings.base import EmbeddingsProvider


class NumpyEmbeddingFunction:
    """Embedding function that follows Chroma's interface."""

    def __init__(self, provider: "NumpyProvider"):
        """Initialize with a provider instance."""
        self._provider = provider

    def __call__(self, input: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for input text(s).

        Args:
            input: Text or list of texts to embed

        Returns:
            List of embeddings
        """
        if isinstance(input, str):
            input = [input]

        embeddings = []
        for text in input:
            # Get character frequencies
            freq_vec = self._provider._get_char_frequencies(text)

            # Add some random noise for variety
            noise = self._provider._rng.normal(0, 0.1, self._provider.embedding_dim)
            embedding = freq_vec + noise

            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            embeddings.append(embedding.tolist())

        return embeddings


class NumpyProvider(EmbeddingsProvider):
    """A lightweight embeddings provider that uses numpy for basic text embeddings.

    This provider is meant for testing and development purposes only.
    It creates simple embeddings based on character frequencies.
    """

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(self, embedding_dim: int = 64):
        """Initialize the numpy embeddings provider.

        Args:
            embedding_dim: Dimension of the embeddings to generate
        """
        self.embedding_dim = embedding_dim
        self._rng = np.random.RandomState(42)  # Fixed seed for reproducibility

    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    def _get_char_frequencies(self, text: str) -> np.ndarray:
        """Get character frequency vector for a text.

        Args:
            text: Input text

        Returns:
            Character frequency vector
        """
        # Get unique characters and their counts
        chars, counts = np.unique(list(text.lower()), return_counts=True)

        # Create a frequency vector
        freq_vec = np.zeros(self.embedding_dim)
        for char, count in zip(chars, counts):
            # Use character's hash as index
            idx = int(hashlib.md5(char.encode()).hexdigest(), 16) % self.embedding_dim
            freq_vec[idx] = count / len(text)

        return freq_vec

    async def embed_text(self, text: str) -> List[float]:
        """Create an embedding for the given text.

        Args:
            text: Text to embed

        Returns:
            Text embedding as a list of floats
        """
        return NumpyEmbeddingFunction(self)([text])[0]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of text embeddings
        """
        return NumpyEmbeddingFunction(self)(texts)

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """
        return NumpyEmbeddingFunction(self)
