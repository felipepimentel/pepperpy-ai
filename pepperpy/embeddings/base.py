"""Base classes and protocols for embeddings.

This module defines the base interfaces that all embedding providers must implement.
"""

from typing import Any, Dict, List, Optional, Protocol, Union
from abc import ABC, abstractmethod

from .models import EmbeddingOptions, EmbeddingResult
from pepperpy.core import PepperpyError


class EmbeddingError(PepperpyError):
    """Base class for embedding errors."""

    pass


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider.

        Args:
            **kwargs: Provider-specific arguments.
        """
        self.config = kwargs

    @abstractmethod
    async def embed_text(
        self,
        text: Union[str, List[str]],
        **kwargs: Any,
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text.

        Args:
            text: Text or list of texts to embed.
            **kwargs: Additional provider-specific arguments.

        Returns:
            A list of embeddings (one per text).

        Raises:
            EmbeddingError: If there is an error generating embeddings.
        """
        pass

    @abstractmethod
    async def get_dimensions(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            The number of dimensions in the embeddings.

        Raises:
            EmbeddingError: If there is an error getting dimensions.
        """
        pass

    name: str

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider to set up any
        necessary resources or connections.
        """
        ...

    async def embed(
        self, text: str, options: Optional[EmbeddingOptions] = None
    ) -> EmbeddingResult:
        """Generate embeddings for the given text.

        Args:
            text: The text to generate embeddings for
            options: Optional embedding options

        Returns:
            The generated embeddings

        Raises:
            EmbeddingError: If there is an error generating the embeddings
        """
        ...

    async def embed_batch(
        self, texts: List[str], options: Optional[EmbeddingOptions] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        Args:
            texts: The texts to generate embeddings for
            options: Optional embedding options

        Returns:
            The generated embeddings for each text

        Raises:
            EmbeddingError: If there is an error generating the embeddings
        """
        ...

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        ...

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        ... 