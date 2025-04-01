"""OpenAI embeddings provider for PepperPy.

This module provides embeddings using OpenAI's text embedding models.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from openai import AsyncOpenAI
from pepperpy.embeddings import EmbeddingsProvider
from pepperpy.plugins import ProviderPlugin

T = TypeVar("T", bound="OpenAIEmbeddingsProvider")


class OpenAIEmbeddingsProvider(EmbeddingsProvider, ProviderPlugin):
    """OpenAI embeddings provider for PepperPy."""

    # Instance variables - these come from plugin.yaml
    api_key: str
    model: str
    dimensions: int
    client: Optional[AsyncOpenAI] = None

    def __init__(self, **config: Any) -> None:
        """Initialize the OpenAI embeddings provider.

        Args:
            **config: Configuration options for the provider
        """
        super().__init__(**config)
        self.client = None

    @classmethod
    def from_config(cls: Type[T], **config: Any) -> T:
        """Create provider instance from configuration.

        Args:
            **config: Configuration options for the provider

        Returns:
            Provider instance
        """
        return cast(T, cls(**config))

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not hasattr(self, "api_key") or not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.client = None

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Create embeddings for the given text(s).

        Args:
            text: Text or list of texts to create embeddings for

        Returns:
            List of text embeddings
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                raise RuntimeError("Failed to initialize OpenAI client")

        if isinstance(text, str):
            text = [text]

        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions,
        )

        return [data.embedding for data in response.data]

    async def embed_query(self, text: str) -> List[float]:
        """Create an embedding for a single query text.

        Args:
            text: Text to create embedding for

        Returns:
            Query embedding
        """
        embeddings = await self.embed_text(text)
        return embeddings[0]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts.

        Args:
            texts: List of texts to create embeddings for

        Returns:
            List of text embeddings
        """
        return await self.embed_text(texts)

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings

        Raises:
            NotImplementedError: Synchronous embedding function not supported
        """
        raise NotImplementedError("Synchronous embedding function not supported")

    async def get_dimensions(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            The number of dimensions in the embeddings
        """
        return self.dimensions

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "model": self.model,
            "dimensions": self.dimensions,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "supports_async": True,
            "supports_sync": False,
            "supports_batch": True,
            "max_batch_size": 2048,  # OpenAI's limit
            "max_text_length": 8192,  # OpenAI's limit
            "dimensions": self.dimensions,
            "models": [
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",  # Legacy
            ],
        }
