"""Azure AI Embeddings Provider.

This module provides an embeddings provider that uses Azure OpenAI services.
"""

from collections.abc import Sequence
from typing import Any, List, Optional

from openai import AsyncAzureOpenAI

from pepperpy.core import ConfigError, ProviderError
from pepperpy.embeddings.base import EmbeddingsProvider
from pepperpy.plugins import ProviderPlugin


class AzureEmbeddingsProvider(EmbeddingsProvider, ProviderPlugin):
    """Azure AI Embeddings Provider."""

    

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    client: Optional[Any]
    model: str = "embedding-model"
    dimensions: int = 1536

    def __init__(self, **config: Any) -> None:
        """Initialize the provider.

        Args:
            **config: Configuration options
              - api_key: Azure API key
              - api_endpoint: Azure API endpoint
              - model: Model name (default: text-embedding-ada-002)
              - dimensions: Output dimensions (default: 1536)
              - batch_size: Maximum batch size for embeddings (default: 16)
        """
        super().__init__(**config)
        self._client: Optional[AsyncAzureOpenAI] = None

    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            ConfigError: If required configuration is missing
            ProviderError: If initialization fails
        """
        if self.initialized:
            return

        # Check for required configuration
        if not self.api_key:
            raise ConfigError("Azure API key is required")
        if not self.api_endpoint:
            raise ConfigError("Azure API endpoint is required")

        try:
            # Create client
            self._client = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version="2023-05-15",
                azure_endpoint=self.api_endpoint,
            )

            # Set default dimensions
            if not hasattr(self, "dimensions"):
                # Default to 1536 for text-embedding-ada-002
                self.dimensions = 1536

            self.logger.info(
                "Azure Embeddings Provider initialized (model: %s, dimensions: %s)",
                self.model,
                self.dimensions,
            )
        except Exception as e:
            raise ProviderError(
                f"Failed to initialize Azure Embeddings Provider: {e}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._client = None

    async def embed_texts(
        self, texts: Sequence[str], **kwargs: Any
    ) -> List[List[float]]:
        """Generate embeddings for the provided texts.

        Args:
            texts: Texts to embed
            **kwargs: Additional options
              - model: Model name to use
              - batch_size: Maximum batch size for embeddings

        Returns:
            List of embeddings, one per input text

        Raises:
            ProviderError: If embedding generation fails
        """
        if not texts:
            return []

        if not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Get options from kwargs or config
            model = kwargs.get("model", self.model)
            batch_size = kwargs.get("batch_size", getattr(self, "batch_size", 16))

            # Process in batches
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = list(
                    texts[i : i + batch_size]
                )  # Convert to list for OpenAI API
                response = await self._client.embeddings.create(
                    model=model,
                    input=batch,
                )
                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)

            return all_embeddings

        except Exception as e:
            raise ProviderError(f"Failed to generate embeddings: {e}") from e

    async def embed_query(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for a query.

        Args:
            text: Query text to embed
            **kwargs: Additional options passed to embed_texts

        Returns:
            Embedding for the query

        Raises:
            ProviderError: If embedding generation fails
        """
        embeddings = await self.embed_texts([text], **kwargs)
        return embeddings[0]

    def get_dimensions(self) -> int:
        """Get the dimensions of the embeddings.

        Returns:
            Dimensionality of the embeddings
        """
        return self.dimensions
