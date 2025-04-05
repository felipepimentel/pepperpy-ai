"""
PepperPy LLM Base Module.

Base interfaces and abstractions for language model functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol, Union

from pepperpy.core.errors import PepperpyError


class LLMError(PepperpyError):
    """Base error for LLM operations."""

    pass


class LLMProviderError(LLMError):
    """Error raised by LLM providers."""

    pass


class LLMConfigError(LLMProviderError):
    """Error related to LLM configuration."""

    pass


class Message:
    """Message for LLM interactions."""

    def __init__(self, role: str, content: str):
        """Initialize a message.

        Args:
            role: Message role (system, user, assistant)
            content: Message content
        """
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary.

        Returns:
            Message as dictionary
        """
        return {"role": self.role, "content": self.content}


class LLMProvider(Protocol):
    """Protocol defining LLM provider interface."""

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Complete a text prompt.

        Args:
            prompt: Text prompt to complete
            **kwargs: Additional provider-specific options

        Returns:
            Completion text
        """
        ...

    async def chat(self, messages: List[Union[Message, Dict[str, str]]], **kwargs: Any) -> str:
        """Generate a chat response.

        Args:
            messages: List of messages
            **kwargs: Additional provider-specific options

        Returns:
            Response text
        """
        ...

    async def stream_chat(self, messages: List[Union[Message, Dict[str, str]]], **kwargs: Any) -> AsyncIterator[str]:
        """Stream a chat response.

        Args:
            messages: List of messages
            **kwargs: Additional provider-specific options

        Returns:
            Async iterator of response chunks
        """
        ...

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed
            **kwargs: Additional provider-specific options

        Returns:
            Embedding vector
        """
        ...


class BaseLLMProvider(ABC):
    """Base implementation for LLM providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize base LLM provider.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the LLM provider.

        Implementations should set self.initialized to True when complete.
        """
        self.initialized = True

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Complete a text prompt.

        Args:
            prompt: Text prompt to complete
            **kwargs: Additional provider-specific options

        Returns:
            Completion text
        """
        if not self.initialized:
            await self.initialize()
        raise LLMProviderError("Text completion not implemented")

    @abstractmethod
    async def chat(self, messages: List[Union[Message, Dict[str, str]]], **kwargs: Any) -> str:
        """Generate a chat response.

        Args:
            messages: List of messages
            **kwargs: Additional provider-specific options

        Returns:
            Response text
        """
        if not self.initialized:
            await self.initialize()
        raise LLMProviderError("Chat not implemented")

    async def stream_chat(self, messages: List[Union[Message, Dict[str, str]]], **kwargs: Any) -> AsyncIterator[str]:
        """Stream a chat response.

        Args:
            messages: List of messages
            **kwargs: Additional provider-specific options

        Returns:
            Async iterator of response chunks
        """
        if not self.initialized:
            await self.initialize()

        # Default implementation just gets the full response and yields it
        response = await self.chat(messages, **kwargs)
        yield response

    @abstractmethod
    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed
            **kwargs: Additional provider-specific options

        Returns:
            Embedding vector
        """
        if not self.initialized:
            await self.initialize()
        raise LLMProviderError("Embedding not implemented") 