"""Base interfaces and types for LLM capabilities.

This module defines the core interfaces and data types for working with
Language Model providers in PepperPy.

Example:
    >>> from pepperpy.llm import LLMProvider, Message, MessageRole
    >>> provider = LLMProvider.from_config({
    ...     "provider": "openai",
    ...     "model": "gpt-4",
    ...     "api_key": "sk-..."
    ... })
    >>> messages = [
    ...     Message(MessageRole.SYSTEM, "You are helpful."),
    ...     Message(MessageRole.USER, "What's the weather?")
    ... ]
    >>> result = provider.generate(messages)
    >>> print(result.content)
"""

import abc
import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Union, Protocol

from pepperpy.core import PepperpyError
from pepperpy.core.providers import BaseProvider


class LLMError(PepperpyError):
    """Base exception for LLM-related errors."""


class MessageRole(str, enum.Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """A message in a conversation.

    Attributes:
        role: Role of the message sender
        content: Message content
        name: Optional name of the sender
        function_call: Optional function call details
    """

    role: Union[MessageRole, str]
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResult:
    """Result of a text generation request.

    Attributes:
        content: Generated text content
        messages: Full conversation history
        usage: Token usage statistics
        metadata: Additional provider-specific metadata
    """

    content: str
    messages: List[Message]
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GenerationChunk:
    """A chunk of generated text from a streaming response.

    Attributes:
        content: Generated text content
        finish_reason: Reason for finishing (if any)
        metadata: Additional provider-specific metadata
    """

    content: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(Protocol):
    """Interface for LLM providers."""

    @property
    def api_key(self) -> Optional[str]:
        """Get the API key for the provider.
        
        Returns:
            The API key if set, None otherwise.
        """
        ...

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt.
        
        Args:
            prompt: The prompt to generate a response for.
            
        Returns:
            The generated response.
        """
        ...

    async def chat(self, messages: list[Dict[str, Any]]) -> str:
        """Generate a response in a chat context.
        
        Args:
            messages: List of messages in the chat history.
                Each message should have 'role' and 'content' keys.
            
        Returns:
            The generated response.
        """
        ...


class LLMProvider(BaseProvider, abc.ABC):
    """Base class for LLM providers.

    This class defines the interface that all LLM providers must implement.
    It includes methods for text generation, streaming, and embeddings.
    """

    name: str = "base"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize LLM provider.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config=config)
        self.initialized = False
        self.last_used = None

    @abc.abstractmethod
    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text based on input messages.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options

        Returns:
            GenerationResult containing the response

        Raises:
            LLMError: If generation fails
        """

    @abc.abstractmethod
    async def stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text in a streaming fashion.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options

        Returns:
            AsyncIterator yielding GenerationChunk objects

        Raises:
            LLMError: If generation fails
        """

    async def get_embeddings(
        self,
        texts: Union[str, List[str]],
        **kwargs: Any,
    ) -> List[List[float]]:
        """Generate embeddings for input texts.

        Args:
            texts: String or list of strings to embed
            **kwargs: Additional embedding options

        Returns:
            List of embedding vectors

        Raises:
            LLMError: If embedding fails
            NotImplementedError: If provider doesn't support embeddings
        """
        raise NotImplementedError("Embeddings not supported by this provider")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities including:
            - supported_models: List of supported models
            - max_tokens: Maximum tokens per request
            - supports_streaming: Whether streaming is supported
            - supports_embeddings: Whether embeddings are supported
            - additional provider-specific capabilities
        """
        return {
            "embeddings": False,
            "streaming": False,
            "chat_based": True,
            "function_calling": False,
        }

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        It can be used to set up connections, load models, etc.
        """
        await super().initialize()
        self.initialized = True
        self.last_used = datetime.now()

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be called when the provider is no longer needed.
        It can be used to close connections, unload models, etc.
        """
        await super().cleanup()
        self.initialized = False
