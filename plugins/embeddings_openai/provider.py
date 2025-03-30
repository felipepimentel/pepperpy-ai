"""OpenAI embedding provider implementation.

This module provides an OpenAI implementation of the embedding provider interface,
using OpenAI's text embedding models.
"""

from typing import Any, Dict, List, Optional, Union

from openai import OpenAI

from ..base import EmbeddingError, EmbeddingProvider


class OpenAIEmbeddingFunction:
    """Embedding function that follows Chroma's interface."""

    def __init__(self, provider: "OpenAIEmbeddingProvider"):
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

        # Get embeddings from OpenAI
        response = self._provider.client.embeddings.create(
            input=input,
            model=self._provider.model,
        )

        # Extract embeddings
        return [data.embedding for data in response.data]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI implementation of the embedding provider interface."""

    

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    model: str = "default-model"
    base_url: str
    temperature: float = 0.7
    max_tokens: int = 1024
    user_id: str
    client: Optional[Any]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        **kwargs: Any,
    ) -> None:
        """Initialize the OpenAI embedding provider.

        Args:
            api_key: OpenAI API key (default: None, uses env var)
            model: OpenAI embedding model (default: text-embedding-3-small)
            **kwargs: Additional configuration options

        Raises:
            EmbeddingError: If required dependencies are not installed
        """
        super().__init__(name=self.name, **kwargs)
        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize OpenAI client: {e}")

        self.model = model
        self.dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        self._embedding_function = None

    async def initialize(self) -> None:
        """Initialize the provider."""
        self._embedding_function = OpenAIEmbeddingFunction(self)

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def embed_text(
        self,
        text: Union[str, List[str]],
        **kwargs: Any,
    ) -> List[List[float]]:
        """Convert text to vector embeddings."""
        # Convert single text to list
        texts = [text] if isinstance(text, str) else text

        # Get embeddings from OpenAI
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model,
            **kwargs,
        )

        # Extract embeddings
        return [data.embedding for data in response.data]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of text embeddings
        """
        return await self.embed_text(texts)

    async def embed_query(self, text: str) -> List[float]:
        """Generate embeddings for a query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        result = await self.embed_text(text)
        return result[0]

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """
        if not self._embedding_function:
            self._embedding_function = OpenAIEmbeddingFunction(self)
        return self._embedding_function

    async def get_dimensions(self) -> int:
        """Get embedding dimensions.

        Returns:
            The number of dimensions in the embeddings
        """
        return self.dimensions.get(self.model, 1536)

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "model": self.model,
            "dimensions": self.dimensions.get(self.model),
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI embedding provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "supported_models": list(self.dimensions.keys()),
            "max_tokens": 8191,  # OpenAI token limit
            "supports_batch": True,
            "dimensions": self.dimensions,
        }
