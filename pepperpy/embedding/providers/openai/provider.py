"""OpenAI embedding provider implementation."""

from typing import Any, Dict, List, Optional, Union

from pepperpy.embedding.providers.base import BaseEmbeddingProvider, EmbeddingResponse


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Provider implementation for OpenAI embeddings."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-ada-002",
        **kwargs: Any,
    ):
        """Initialize OpenAI embedding provider.

        Args:
            api_key: OpenAI API key (uses env var if None)
            model: Embedding model name
            **kwargs: Additional provider options
        """
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def client(self):
        """Get or create OpenAI client.

        Returns:
            OpenAI client
        """
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI package is required to use OpenAIEmbeddingProvider. "
                    "Install it with `pip install openai`."
                )
        return self._client

    def embed(self, texts: Union[str, List[str]]) -> EmbeddingResponse:
        """Generate embeddings for text.

        Args:
            texts: Text or list of texts to embed

        Returns:
            Embedding response with vectors

        Raises:
            ValueError: If embedding generation fails
        """
        if isinstance(texts, str):
            texts = [texts]

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
            
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=self.model,
                provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            )
        except Exception as e:
            raise ValueError(f"Failed to generate embeddings: {e}")

    def get_dimensions(self) -> int:
        """Get dimensions for the embedding model.

        Returns:
            Number of dimensions

        Raises:
            ValueError: If dimensions cannot be determined
        """
        # Common OpenAI model dimensions
        dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
        
        if self.model in dimensions:
            return dimensions[self.model]
        
        # If model not in known dimensions, try to get dimensions from a sample embedding
        try:
            response = self.embed("Sample text")
            if response.embeddings and len(response.embeddings) > 0:
                return len(response.embeddings[0])
        except Exception:
            pass
            
        raise ValueError(f"Could not determine dimensions for model {self.model}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model.

        Returns:
            Dictionary with model information
        """
        return {
            "name": self.model,
            "provider": "openai",
            "dimensions": self.get_dimensions(),
        }
