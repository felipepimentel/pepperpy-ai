"""OpenAI embedding provider implementation."""

from typing import List, Union

import numpy as np

from pepperpy.embedding.base import EmbeddingError
from pepperpy.embedding.providers.base.base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Provider implementation for OpenAI embeddings."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        **kwargs,
    ):
        """Initialize OpenAI embedding provider.

        Args:
            api_key: OpenAI API key
            model: Model to use for embeddings
            **kwargs: Additional parameters to pass to OpenAI

        Raises:
            ImportError: If openai package is not installed
            EmbeddingError: If initialization fails
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAIEmbeddingProvider. "
                "Install it with: pip install openai"
            )

        self.model = model
        self.kwargs = kwargs

        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize OpenAI client: {e}")

    def embed(
        self,
        text: Union[str, List[str]],
        **kwargs,
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """Generate embeddings for text.

        Args:
            text: Text or list of texts to generate embeddings for
            **kwargs: Additional parameters to pass to OpenAI

        Returns:
            Union[np.ndarray, List[np.ndarray]]: Embedding vector(s)

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            # Handle single text vs list of texts
            texts = [text] if isinstance(text, str) else text

            # Get embeddings from OpenAI
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                **self.kwargs,
                **kwargs,
            )

            # Convert to numpy arrays
            embeddings = [
                np.array(data.embedding, dtype=np.float32) for data in response.data
            ]

            # Return single array for single input, list for multiple inputs
            return embeddings[0] if isinstance(text, str) else embeddings

        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}")

    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            int: Embedding dimension
        """
        # Dimensions for different OpenAI models
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dimensions.get(self.model, 1536)  # Default to 1536 if model unknown

    def get_models(self) -> List[str]:
        """Get list of available embedding models.

        Returns:
            List[str]: List of model names
        """
        return [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002",  # Legacy model
        ]
