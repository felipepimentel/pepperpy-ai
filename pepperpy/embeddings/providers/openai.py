"""OpenAI embedding provider implementation.

This module provides an OpenAI implementation of the embedding provider interface,
using OpenAI's text embedding models.
"""

from typing import Any, Dict, List, Optional, Sequence, Union, cast

from openai import OpenAI

from ..base import EmbeddingError, EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI implementation of the embedding provider interface."""

    name = "openai"

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

    async def embed_text(
        self,
        text: Union[str, List[str]],
        **kwargs: Any,
    ) -> Union[List[float], List[List[float]]]:
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
        embeddings = [data.embedding for data in response.data]

        # Return single vector for single text
        return embeddings[0] if isinstance(text, str) else embeddings

    async def embed_documents(
        self,
        documents: Sequence[Dict[str, Any]],
        text_field: str = "content",
        **kwargs: Any,
    ) -> List[List[float]]:
        """Convert documents to vector embeddings."""
        # Extract text from documents
        texts = []
        for doc in documents:
            if text_field not in doc:
                raise EmbeddingError(f"Document missing {text_field} field")
            texts.append(doc[text_field])

        # Get embeddings and ensure we always return List[List[float]]
        result = await self.embed_text(texts, **kwargs)
        if isinstance(result, list):
            if not result:
                return []
            if isinstance(result[0], float):
                return [cast(List[float], result)]
            return cast(List[List[float]], result)
        return [result]

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.dimensions.get(self.model, 1536)

    def get_model_name(self) -> str:
        """Get embedding model name."""
        return self.model

    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI embedding provider capabilities."""
        return {
            "supported_models": list(self.dimensions.keys()),
            "max_tokens": 8191,  # OpenAI token limit
            "supports_batch": True,
            "dimensions": self.dimensions,
        }
