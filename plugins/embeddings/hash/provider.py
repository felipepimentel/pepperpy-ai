"""Hash-based embedding provider for testing.

This module provides a simple hash-based embedding provider that converts text into vectors
using hash values. It's useful for testing and development, but should not be used in
production as it doesn't capture semantic meaning.
"""

import hashlib
from typing import Any, Dict, List, Optional, Union

from pepperpy.embeddings import (
    EmbeddingError,
    EmbeddingOptions,
    EmbeddingResult,
    EmbeddingsProvider,
)


class HashEmbeddingProvider(EmbeddingsProvider):
    """Simple embedding provider that uses hash values.

    This is a lightweight embedding provider that converts text into vectors
    using hash values. It's useful for testing and development, but should
    not be used in production as it doesn't capture semantic meaning.
    """

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str

    def __init__(
        self,
        embedding_dim: int = 1536,
        provider_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the hash embedding provider.

        Args:
            embedding_dim: Dimension of the embeddings (default: 1536)
            provider_name: Optional specific name for this provider
            **kwargs: Additional provider configuration
        """
        self.name = provider_name or "hash"
        self.embedding_dim = embedding_dim
        self._config = {
            "embedding_dim": embedding_dim,
            **kwargs,
        }

    async def initialize(self) -> None:
        """Initialize the provider.

        This provider doesn't require initialization.
        """
        pass

    async def cleanup(self) -> None:
        """Clean up resources.

        This provider doesn't require cleanup.
        """
        pass

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Create embeddings for the given text.

        Args:
            text: Text or list of texts to embed

        Returns:
            List of text embeddings
        """
        if isinstance(text, str):
            result = await self.embed(text)
            return [result.embedding]
        else:
            results = await self.embed_batch(text)
            return [r.embedding for r in results]

    async def embed_query(self, text: str) -> List[float]:
        """Create an embedding for a single query text.

        Args:
            text: Query text to embed

        Returns:
            Query embedding as a list of floats
        """
        result = await self.embed(text)
        return result.embedding

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of text embeddings
        """
        results = await self.embed_batch(texts)
        return [r.embedding for r in results]

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """

        async def embed_fn(text: str) -> List[float]:
            return await self.embed_query(text)

        return embed_fn

    async def embed(
        self, text: str, options: Optional[EmbeddingOptions] = None
    ) -> EmbeddingResult:
        """Convert text into a vector embedding.

        Args:
            text: Text to convert
            options: Optional embedding options

        Returns:
            EmbeddingResult with the generated embedding

        Raises:
            EmbeddingError: If embedding fails
        """
        try:
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

            return EmbeddingResult(
                embedding=embedding,
                usage={"total_tokens": len(text.split())},
                metadata={"model": "hash", "dimensions": self.embedding_dim},
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to generate hash embedding: {e}") from e

    async def embed_batch(
        self, texts: List[str], options: Optional[EmbeddingOptions] = None
    ) -> List[EmbeddingResult]:
        """Convert multiple texts into vector embeddings.

        Args:
            texts: List of texts to convert
            options: Optional embedding options

        Returns:
            List of EmbeddingResult objects

        Raises:
            EmbeddingError: If embedding fails
        """
        results = []
        for text in texts:
            result = await self.embed(text, options)
            results.append(result)
        return results

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return self._config.copy()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "capabilities": ["text_embedding"],
            "dimensions": self.embedding_dim,
        }
