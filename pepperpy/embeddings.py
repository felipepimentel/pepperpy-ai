"""Embeddings module for PepperPy.

This module provides the base interfaces and implementations for embeddings providers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Union, cast, runtime_checkable

from pepperpy.core.base import BaseComponent, PepperpyError
from pepperpy.core.config import Config
from pepperpy.plugins.manager import create_provider_instance


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
        embedding: The embedding vector
        usage: Usage information (e.g., tokens used)
        metadata: Additional metadata about the embedding
    """

    embedding: List[float]
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@runtime_checkable
class EmbeddingsProvider(Protocol):
    """Base interface for embeddings providers."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Create an embedding for the given text.

        Args:
            text: Text or list of texts to embed

        Returns:
            List of text embeddings
        """
        raise NotImplementedError

    async def embed_query(self, text: str) -> List[float]:
        """Create an embedding for a single query text.

        Args:
            text: Query text to embed

        Returns:
            Query embedding as a list of floats
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


class EmbeddingComponent(BaseComponent):
    """Embeddings component for text embeddings."""

    def __init__(self, config: Config) -> None:
        """Initialize embeddings component.

        Args:
            config: Configuration instance
        """
        super().__init__()
        self.config = config
        self._provider: Optional[EmbeddingsProvider] = None

    async def _initialize(self) -> None:
        """Initialize the embeddings provider."""
        provider_type = self.config.get("embeddings.provider", "openai")
        provider_config = self.config.get("embeddings.config", {})
        provider = create_provider_instance(
            "embeddings", provider_type, **provider_config
        )
        self._provider = cast(EmbeddingsProvider, provider)
        if self._provider:
            await self._provider.initialize()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._provider:
            await self._provider.cleanup()

    async def embed_single_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text.

        Args:
            text: Text to embed

        Returns:
            Text embeddings as a list of float values
        """
        if not self._provider:
            await self._initialize()

        # Ensure provider is initialized
        assert self._provider is not None

        # Use embed_query which returns List[float] directly
        return await self._provider.embed_query(text)

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for text(s).

        Args:
            text: Text or list of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self._provider:
            await self._initialize()

        # Ensure provider is initialized
        assert self._provider is not None

        # Forward directly to provider's implementation
        return await self._provider.embed_text(text)


def create_provider(
    provider_type: str = "local",
    **config: Any,
) -> EmbeddingsProvider:
    """Create a new embedding provider.

    Args:
        provider_type: Type of provider to create
        **config: Additional configuration options

    Returns:
        A new embedding provider instance

    Raises:
        EmbeddingConfigError: If the provider type is invalid or configuration is invalid
    """
    try:
        # Use enhanced plugin discovery to create provider
        provider = create_provider_instance("embeddings", provider_type, **config)
        if not isinstance(provider, EmbeddingsProvider):
            raise EmbeddingConfigError(
                f"Provider '{provider_type}' does not implement EmbeddingsProvider interface"
            )
        return provider
    except ImportError as e:
        raise EmbeddingConfigError(
            f"Failed to import provider '{provider_type}'. Please install the required dependencies: {e!s}"
        )
    except Exception as e:
        raise EmbeddingConfigError(
            f"Failed to create provider '{provider_type}': {e!s}"
        )


__all__ = [
    "EmbeddingComponent",
    "EmbeddingConfigError",
    "EmbeddingError",
    "EmbeddingOptions",
    "EmbeddingResult",
    "EmbeddingsProvider",
]
