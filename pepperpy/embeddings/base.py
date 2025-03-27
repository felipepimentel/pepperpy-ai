"""Base module for embeddings functionality.

This module defines the base interfaces and types for embedding providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Union

from pepperpy.core.base import BaseProvider, PepperpyError


class EmbeddingError(PepperpyError):
    """Base error for the embeddings module."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize a new embeddings error.

        Args:
            message: Error message.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(message, *args, **kwargs)


class EmbeddingConfigError(EmbeddingError):
    """Error related to configuration of embedding providers."""

    def __init__(
        self, message: str, provider: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a new embedding configuration error.

        Args:
            message: Error message.
            provider: The embedding provider name.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.provider = provider
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        """Return the string representation of the error."""
        if self.provider:
            return f"Configuration error for provider '{self.provider}': {self.message}"
        return f"Configuration error: {self.message}"


class EmbeddingProcessError(EmbeddingError):
    """Error related to the embedding process."""

    def __init__(
        self, message: str, text: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a new embedding process error.

        Args:
            message: Error message.
            text: The text that failed to be embedded.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.text = text
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        """Return the string representation of the error."""
        if self.text:
            # Truncate text if too long
            text = self.text[:50] + "..." if len(self.text) > 50 else self.text
            return f"Embedding process error for text '{text}': {self.message}"
        return f"Embedding process error: {self.message}"


@dataclass
class EmbeddingOptions:
    """Options for embedding generation.

    Attributes:
        model: Model to use for embedding generation
        dimensions: Number of dimensions for the embeddings
        normalize: Whether to normalize the embeddings
        additional_options: Additional provider-specific options
    """

    model: str = "default"
    dimensions: Optional[int] = None
    normalize: bool = False
    additional_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResult:
    """Result of an embedding operation.

    Attributes:
        vector: The embedding vector
        metadata: Additional metadata about the embedding
    """

    vector: List[float]
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingProvider(BaseProvider, ABC):
    """Base class for embedding providers."""

    name: str = "base"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider.

        Args:
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self._model = None
        self._embedding_function = None

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    @abstractmethod
    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for the given text.

        Args:
            text: Text or list of texts to embed

        Returns:
            List of embeddings vectors
        """
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate embeddings for a query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """
        pass

    @abstractmethod
    async def get_dimensions(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            The number of dimensions in the embeddings
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
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


class EmbeddingsProvider(Protocol):
    """Base interface for embeddings providers."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def embed_text(
        self, text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        """Create an embedding for the given text.

        Args:
            text: Text or list of texts to embed

        Returns:
            Text embedding as a list of floats or list of embeddings
        """
        raise NotImplementedError

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of text embeddings
        """
        raise NotImplementedError

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """
        raise NotImplementedError


def create_provider(provider_type: str, **config: Any) -> EmbeddingsProvider:
    """Create an embeddings provider instance.

    Args:
        provider_type: Provider type to create
        **config: Provider configuration

    Returns:
        Instantiated provider
    """
    if provider_type == "local":
        from .providers import LocalProvider

        return LocalProvider(
            model=config.get("model", "default"), device=config.get("device", "cpu")
        )
    elif provider_type == "numpy":
        from .providers import NumpyProvider

        return NumpyProvider(embedding_dim=config.get("embedding_dim", 64))
    elif provider_type == "openai":
        from .providers import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(
            api_key=config.get("api_key"),
            model=config.get("model", "text-embedding-ada-002"),
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
