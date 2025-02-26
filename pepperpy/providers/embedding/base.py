"""Base interfaces and exceptions for embedding providers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Union

import numpy as np


class EmbeddingError(Exception):
    """Base exception for embedding errors."""

    pass


class EmbeddingProvider(ABC):
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
            **kwargs: Additional provider-specific parameters

        Returns:
            Union[np.ndarray, List[np.ndarray]]: Embedding vector(s)

        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            int: Embedding dimension
        """
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available embedding models.

        Returns:
            List[str]: List of model names
        """
        pass

    def batch_embed(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> List[np.ndarray]:
        """Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to generate embeddings for
            batch_size: Optional batch size (provider-specific default if None)
            **kwargs: Additional provider-specific parameters

        Returns:
            List[np.ndarray]: List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not batch_size:
            return self.embed(texts, **kwargs)

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = self.embed(batch, **kwargs)
            if isinstance(batch_embeddings, np.ndarray):
                embeddings.append(batch_embeddings)
            else:
                embeddings.extend(batch_embeddings)
        return embeddings
