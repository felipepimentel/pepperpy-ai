"""OpenRouter embeddings provider implementation."""

import os
from typing import Any, List, Optional, Union

import chromadb.utils.embedding_functions

from pepperpy.core.errors import ProviderError
from pepperpy.plugin.plugin import PepperpyPlugin


class OpenRouterEmbeddingProvider(PepperpyPlugin):
    """OpenRouter implementation of embeddings provider."""

    name = "openrouter"
    version = "0.1.0"
    description = "OpenRouter embeddings provider using their API"
    author = "PepperPy Team"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/text-embedding-3-small",
        **kwargs: Any,
    ) -> None:
        """Initialize OpenRouter embeddings provider.

        Args:
            api_key: OpenRouter API key
            model: Model to use for embeddings
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self._api_key = api_key
        self.model = model
        self._embedding_function = None

    @property
    def api_key(self) -> str:
        """Get the API key.

        Returns:
            The API key

        Raises:
            ProviderError: If API key is not found
        """
        key = self._api_key or os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY")
        if not key:
            raise ProviderError(
                "OpenRouter API key not found. Please set PEPPERPY_LLM__OPENROUTER_API_KEY "
                "environment variable or pass api_key parameter."
            )
        return key

    async def initialize(self) -> None:
        """Initialize the provider."""
        self._embedding_function = (
            chromadb.utils.embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.api_key,
                model_name=self.model,
                api_base="https://openrouter.ai/api/v1",
                api_type="openrouter",
            )
        )
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._embedding_function = None
        self.initialized = False

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for the given text.

        Args:
            text: Text or list of texts to embed

        Returns:
            List of embeddings vectors

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self._embedding_function:
            raise ProviderError("Provider not initialized")

        if isinstance(text, str):
            text = [text]
        return self._embedding_function(text)

    async def embed_query(self, text: str) -> List[float]:
        """Generate embeddings for a query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return (await self.embed_text(text))[0]

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """
        return self._embedding_function
