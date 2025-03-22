"""Embedding functions for RAG providers.

This module provides various embedding functions that can be used with RAG providers
to convert text into vector embeddings.
"""

import hashlib
from typing import List


class HashEmbeddingFunction:
    """Simple embedding function that uses hash values.

    This is a lightweight embedding function that converts text into vectors
    using hash values. It's useful for testing and development, but should
    not be used in production as it doesn't capture semantic meaning.

    Args:
        embedding_dim: Dimension of the embeddings (default: 1536)
    """

    def __init__(self, embedding_dim: int = 1536) -> None:
        self.embedding_dim = embedding_dim

    async def embed_text(self, text: str) -> List[float]:
        """Convert text into a vector embedding.

        Args:
            text: Text to convert

        Returns:
            Vector embedding as a list of floats
        """
        # Hash the text
        hash_value = hashlib.sha256(text.encode()).hexdigest()

        # Convert hash to list of floats
        embedding = []
        for i in range(0, min(len(hash_value), self.embedding_dim), 2):
            # Convert each pair of hex digits to a float between 0 and 1
            value = int(hash_value[i : i + 2], 16) / 255.0
            embedding.append(value)

        # Pad with zeros if needed
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)

        return embedding

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts into vector embeddings.

        Args:
            texts: List of texts to convert

        Returns:
            List of vector embeddings
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings
