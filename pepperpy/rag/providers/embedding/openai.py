"""OpenAI embedding provider implementation.

This module provides embedding functionality using OpenAI's models.
"""

import asyncio
from typing import List, Optional

from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pepperpy.rag.errors import EmbeddingError
from pepperpy.rag.providers.embedding.base import BaseEmbeddingProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Default model for embeddings
DEFAULT_MODEL = "text-embedding-3-small"

# Maximum batch size for embedding requests
MAX_BATCH_SIZE = 100

# Retry configuration
MAX_RETRIES = 3
MIN_WAIT = 1
MAX_WAIT = 10


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider.

    This provider uses OpenAI's models to generate embeddings.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        batch_size: int = MAX_BATCH_SIZE,
    ):
        """Initialize OpenAI embedding provider.

        Args:
            api_key: OpenAI API key (if None, uses environment variable)
            model_name: Name of the model to use
            batch_size: Maximum number of texts to embed in one request
        """
        super().__init__(model_name=model_name)
        self.client = AsyncOpenAI(api_key=api_key)
        self.batch_size = min(batch_size, MAX_BATCH_SIZE)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=MIN_WAIT, max=MAX_WAIT),
        reraise=True,
    )
    async def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings

        Raises:
            EmbeddingError: If there is an error getting embeddings
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=texts,
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            raise EmbeddingError(f"Error getting embeddings from OpenAI: {e}")

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using OpenAI's models.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings for each text

        Raises:
            EmbeddingError: If there is an error during embedding
        """
        try:
            # Split texts into batches
            batches = [
                texts[i : i + self.batch_size]
                for i in range(0, len(texts), self.batch_size)
            ]

            # Get embeddings for each batch
            tasks = [self._get_embeddings_batch(batch) for batch in batches]
            results = await asyncio.gather(*tasks)

            # Combine results
            embeddings = []
            for batch_embeddings in results:
                embeddings.extend(batch_embeddings)

            return embeddings

        except Exception as e:
            raise EmbeddingError(f"Error in OpenAI embedding provider: {e}")
