"""Embedding management utilities."""

import numpy as np
from pydantic import BaseModel

from pepperpy.llms.base_llm import BaseLLM


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""

    model_name: str
    batch_size: int = 32
    cache_embeddings: bool = True
    normalize: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0


class EmbeddingManager:
    """Manages embedding generation and caching.

    This class handles:
    - Batched embedding generation
    - Caching of embeddings
    - Normalization and preprocessing
    - Error handling and retries
    """

    def __init__(self, llm: BaseLLM, config: EmbeddingConfig) -> None:
        """Initialize the embedding manager.

        Args:
            llm: Language model for generating embeddings
            config: Configuration for embedding generation
        """
        self.llm = llm
        self.config = config
        self._cache: dict[str, list[float]] = {}

    async def get_embeddings(
        self, texts: str | list[str], use_cache: bool = True
    ) -> list[float] | list[list[float]]:
        """Get embeddings for text(s).

        Args:
            texts: Text or list of texts to embed
            use_cache: Whether to use cached embeddings

        Returns:
            Embeddings for the input texts

        Raises:
            Exception: If embedding generation fails
        """
        # Convert single text to list
        single_input = isinstance(texts, str)
        texts_list = (
            [texts] if single_input else [str(t) for t in texts]
        )  # Ensure all texts are strings

        # Get embeddings (from cache or generate)
        embeddings: list[list[float]] = []
        texts_to_embed: list[str] = []
        indices_to_embed: list[int] = []

        for i, text_str in enumerate(texts_list):
            if use_cache and self.config.cache_embeddings:
                cached = self._cache.get(str(text_str))  # Ensure key is str
                if cached is not None:
                    embeddings.append(cached)
                    continue

            texts_to_embed.append(str(text_str))  # Ensure text is str
            indices_to_embed.append(i)

        # Generate missing embeddings
        if texts_to_embed:
            new_embeddings = await self._generate_embeddings(texts_to_embed)

            # Update cache and insert at correct positions
            for idx, embedding in zip(indices_to_embed, new_embeddings, strict=False):
                if self.config.cache_embeddings:
                    self._cache[str(texts_list[idx])] = embedding  # Ensure key is str
                embeddings.insert(idx, embedding)

        return embeddings[0] if single_input else embeddings

    async def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings in batches.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings

        Raises:
            Exception: If embedding generation fails
        """
        embeddings: list[list[float]] = []

        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]

            # Generate with retries
            for attempt in range(self.config.max_retries):
                try:
                    batch_embeddings = await self.llm.embed(batch)
                    if not isinstance(batch_embeddings, list):
                        raise ValueError("Expected list of embeddings")
                    if not all(
                        isinstance(emb, list) and all(isinstance(x, float) for x in emb)
                        for emb in batch_embeddings
                    ):
                        raise ValueError("Invalid embedding format")
                    embeddings.extend(batch_embeddings)
                    break
                except Exception as e:
                    if attempt == self.config.max_retries - 1:
                        raise Exception(f"Embedding generation failed: {e!s}") from e
                    await self._wait_before_retry(attempt)

        # Normalize if configured
        if self.config.normalize:
            normalized = self._normalize_embeddings(embeddings)
            if not isinstance(normalized, list):
                raise ValueError("Normalization failed")
            return normalized

        return embeddings

    async def _wait_before_retry(self, attempt: int) -> None:
        """Wait before retrying a failed request.

        Args:
            attempt: The current attempt number (0-based)
        """
        import asyncio

        await asyncio.sleep(self.config.retry_delay * (2**attempt))

    def _normalize_embeddings(self, embeddings: list[list[float]]) -> list[list[float]]:
        """Normalize embedding vectors.

        Args:
            embeddings: List of embeddings to normalize

        Returns:
            Normalized embeddings
        """
        import numpy as np

        # Convert to numpy for efficient computation
        vectors = np.array(embeddings)

        # Compute norms
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)

        # Normalize and handle zero vectors
        normalized = np.divide(vectors, norms, where=norms != 0)

        # Convert back to list and ensure correct type
        result = normalized.tolist()
        if not isinstance(result, list) or not all(
            isinstance(x, list) and all(isinstance(y, float) for y in x) for x in result
        ):
            raise ValueError("Normalization failed to produce valid embeddings")
        return result

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    async def cleanup(self) -> None:
        """Clean up resources used by the embedding manager.

        This includes:
        - Clearing the embedding cache
        - Cleaning up LLM resources
        """
        self.clear_cache()
        await self.llm.cleanup()

    def normalize_embeddings(self, embeddings: list[list[float]]) -> list[list[float]]:
        """Normalize embeddings to unit length."""
        normalized = np.array(embeddings)
        normalized = normalized / np.linalg.norm(normalized, axis=1)[:, np.newaxis]
        result = normalized.tolist()
        assert isinstance(result, list) and all(
            isinstance(x, list) and all(isinstance(y, float) for y in x) for x in result
        ), "Invalid embedding format"
        return result
