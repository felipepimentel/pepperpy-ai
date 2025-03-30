"""OpenAI embeddings provider plugin."""

from typing import Any, Dict, List, Optional, Union, cast

from openai import AsyncClient

from pepperpy.core import ConfigError, ProviderError
from pepperpy.embeddings import EmbeddingProvider
from pepperpy.plugin import ProviderPlugin


class OpenAIProvider(EmbeddingProvider, ProviderPlugin):
    """OpenAI embeddings provider."""

    # Auto-bound attributes from plugin.yaml
    api_key: str
    model: str
    dimensions: Optional[int]
    organization: Optional[str]
    client: Optional[AsyncClient]

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if self.initialized:
            return

        # Check for required configurations (auto-bound from yaml)
        if not self.api_key:
            raise ConfigError("OpenAI API key is required")

        try:
            self.client = AsyncClient(
                api_key=self.api_key,
                organization=self.organization,
            )
        except Exception as e:
            raise ProviderError(f"Failed to initialize OpenAI client: {e}") from e

        self.initialized = True

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for the given text.

        Args:
            text: Text or list of texts to embed

        Returns:
            List of embeddings vectors
        """
        if not self.initialized:
            await self.initialize()

        if isinstance(text, str):
            text = [text]

        # At this point self.client is guaranteed to be initialized
        client = cast(AsyncClient, self.client)

        # Only pass dimensions if explicitly set
        kwargs: Dict[str, Any] = {"model": self.model, "input": text}
        if self.dimensions is not None:
            kwargs["dimensions"] = self.dimensions

        try:
            response = await client.embeddings.create(**kwargs)
        except Exception as e:
            raise ProviderError(f"Failed to generate embeddings: {e}") from e

        return [data.embedding for data in response.data]

    async def embed_query(self, text: str) -> List[float]:
        """Generate embeddings for a query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        embeddings = await self.embed_text(text)
        return embeddings[0]

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """

        async def embedding_function(texts: List[str]) -> List[List[float]]:
            return await self.embed_text(texts)

        return embedding_function

    async def get_dimensions(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            The number of dimensions in the embeddings
        """
        if self.dimensions:
            return self.dimensions

        # Default dimensions based on model
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return model_dimensions.get(self.model, 1536)

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "model": self.model,
            "dimensions": self.dimensions,
            "organization": self.organization,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "models": [
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ],
            "max_tokens": 8191,
            "supports_batch": True,
            "supports_async": True,
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.close()
            self.client = None
