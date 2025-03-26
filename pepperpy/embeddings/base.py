"""Base classes and protocols for embeddings.

This module defines the base interfaces that all embedding providers must implement.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from pepperpy.core.base import PepperpyError


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
        embedding: The generated embedding vector
        usage: Token usage information
        metadata: Additional metadata about the embedding
    """

    embedding: List[float]
    usage: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed.

        Returns:
            Text embeddings.
        """
        ...

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of text embeddings.
        """
        ...

    async def get_dimensions(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            The number of dimensions in the embeddings.

        Raises:
            EmbeddingError: If there is an error getting dimensions.
        """
        raise NotImplementedError("get_dimensions must be implemented by provider")

    name: str

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
