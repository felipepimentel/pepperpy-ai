"""Base class for embedding providers.

This module defines the base class for embedding providers.
"""

from abc import ABC, abstractmethod
from typing import List, Union

import numpy as np


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def embed(
        self,
        text: Union[str, List[str]],
        **kwargs,
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """Generate embeddings for text.

        Args:
            text: Text or list of texts to generate embeddings for
            **kwargs: Additional parameters to pass to the provider

        Returns:
            Union[np.ndarray, List[np.ndarray]]: Embedding vector(s)

        Raises:
            EmbeddingError: If embedding generation fails

        """

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            int: Embedding dimension

        """

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available embedding models.

        Returns:
            List[str]: List of model names

        """
