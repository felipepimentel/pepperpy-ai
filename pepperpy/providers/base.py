"""Base provider module for Pepperpy.

This module defines the core interfaces and base classes for providers.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, Sequence
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.core.types import Message, Response


class ProviderConfig(BaseModel):
    """Configuration for a provider.

    Attributes
    ----------
        api_key: API key for the provider
        model: Model to use
        temperature: Temperature for sampling
        max_tokens: Maximum tokens to generate
        timeout: Operation timeout in seconds
        max_retries: Maximum number of retries
        base_url: Base URL for API calls
        extra: Extra provider-specific configuration
    """

    api_key: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    timeout: Optional[float] = Field(default=None, gt=0)
    max_retries: Optional[int] = Field(default=None, ge=0)
    base_url: Optional[str] = Field(default=None)
    extra: Optional[Dict[str, Dict[str, Any]]] = Field(default=None)


class BaseProvider(ABC):
    """Base class for providers.

    This class defines the interface that all providers must implement.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider.

        Args:
        ----
            config: Provider configuration
        """
        self.config = config
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        raise NotImplementedError

    @abstractmethod
    async def chat(
        self,
        messages: Sequence[Message],
        **kwargs: Any,
    ) -> Response:
        """Send a chat message.

        Args:
        ----
            messages: Messages to send
            **kwargs: Additional arguments

        Returns:
        -------
            Response from the provider
        """
        raise NotImplementedError

    @abstractmethod
    async def stream_chat(
        self,
        messages: Sequence[Message],
        **kwargs: Any,
    ) -> AsyncGenerator[Response, None]:
        """Stream a chat message.

        Args:
        ----
            messages: Messages to send
            **kwargs: Additional arguments

        Returns:
        -------
            Generator yielding responses
        """
        raise NotImplementedError

    @abstractmethod
    async def clear_history(self) -> None:
        """Clear chat history."""
        raise NotImplementedError

    @property
    def id(self) -> UUID:
        """Get provider ID."""
        return self._id

    @property
    def initialized(self) -> bool:
        """Get initialization status."""
        return self._initialized
