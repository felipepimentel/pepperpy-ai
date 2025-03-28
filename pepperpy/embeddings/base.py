"""Base module for embeddings functionality.

This module defines the base interfaces and types for embedding providers.
"""

import importlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Union

from pepperpy.core.base import BaseComponent, BaseProvider, PepperpyError
from pepperpy.core.config import Config


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
        self._provider = create_provider(provider_type, **provider_config)
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

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        This is an alias for embed_text with a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of text embeddings
        """
        return await self.embed_text(texts)


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
    from pepperpy.embeddings.providers import PROVIDER_MODULES

    if provider_type not in PROVIDER_MODULES:
        raise EmbeddingConfigError(
            f"Invalid provider type '{provider_type}'. Available providers: {list(PROVIDER_MODULES.keys())}"
        )

    try:
        module = importlib.import_module(
            PROVIDER_MODULES[provider_type], package="pepperpy.embeddings.providers"
        )
        provider_class = getattr(module, provider_type)
        return provider_class(**config)
    except ImportError as e:
        raise EmbeddingConfigError(
            f"Failed to import provider '{provider_type}'. Please install the required dependencies: {str(e)}"
        )
    except AttributeError:
        raise EmbeddingConfigError(
            f"Provider class '{provider_type}' not found in module '{PROVIDER_MODULES[provider_type]}'"
        )
    except Exception as e:
        raise EmbeddingConfigError(
            f"Failed to create provider '{provider_type}': {str(e)}"
        )
