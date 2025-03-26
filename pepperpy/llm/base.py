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
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.core.base import PepperpyError
from pepperpy.providers import BaseProvider


class LLMError(PepperpyError):
    """Base error for the LLM module."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize a new LLM error.

        Args:
            message: Error message.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(message, *args, **kwargs)


class LLMConfigError(LLMError):
    """Error related to configuration of LLM providers."""

    def __init__(
        self, message: str, provider: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a new LLM configuration error.

        Args:
            message: Error message.
            provider: The LLM provider name.
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


class LLMProcessError(LLMError):
    """Error related to the LLM process."""

    def __init__(
        self, message: str, prompt: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a new LLM process error.

        Args:
            message: Error message.
            prompt: The prompt that failed to be processed.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.prompt = prompt
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        """Return the string representation of the error."""
        if self.prompt:
            # Truncate prompt if too long
            prompt = self.prompt[:50] + "..." if len(self.prompt) > 50 else self.prompt
            return f"LLM process error for prompt '{prompt}': {self.message}"
        return f"LLM process error: {self.message}"


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


class LLMProvider(BaseProvider, abc.ABC):
    """Base class for LLM providers.

    This class defines the interface that all LLM providers must implement.
    It includes methods for text generation, streaming, and embeddings.
    """

    name: str = "base"

    def __init__(
        self,
        name: str = "base",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LLM provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        self.name = name
        self._config = config or {}
        self._config.update(kwargs)
        self.initialized = False
        self.last_used = None

    @property
    def api_key(self) -> Optional[str]:
        """Get the API key for the provider.

        Returns:
            The API key if set, None otherwise.
        """
        return self._config.get("api_key")

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
        raise NotImplementedError("generate must be implemented by provider")

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
        raise NotImplementedError("stream must be implemented by provider")

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
            LLMError: If embedding generation fails
        """
        raise NotImplementedError("get_embeddings must be implemented by provider")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            "streaming": True,
            "embeddings": True,
            "function_calling": True,
            "max_tokens": 4096,
            "max_messages": 100,
        }

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        It can be used to set up any necessary resources or connections.
        """
        if not self.initialized:
            self.initialized = True
            self.last_used = datetime.now()

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be called when the provider is no longer needed.
        It can be used to clean up any resources or connections.
        """
        self.initialized = False
        self.last_used = None

    # Utility methods for common operations

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Chat with the model.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional provider options

        Returns:
            Model response

        Raises:
            LLMError: If chat fails
        """
        # Convert dict messages to Message objects
        formatted_messages = [
            Message(
                role=msg.get("role", MessageRole.USER),
                content=msg["content"],
                name=msg.get("name"),
            )
            for msg in messages
        ]

        result = await self.generate(formatted_messages, **kwargs)
        return result.content

    async def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Summarize text.

        Args:
            text: Text to summarize
            max_length: Optional maximum length in words
            **kwargs: Additional provider options

        Returns:
            Generated summary

        Raises:
            LLMError: If summarization fails
        """
        prompt = "Summarize the following text"
        if max_length:
            prompt += f" in {max_length} words or less"
        prompt += f":\n\n{text}"

        result = await self.generate(prompt, **kwargs)
        return result.content

    async def classify(
        self,
        text: str,
        categories: List[str],
        **kwargs: Any,
    ) -> str:
        """Classify text into predefined categories.

        Args:
            text: Text to classify
            categories: List of possible categories
            **kwargs: Additional provider options

        Returns:
            Selected category

        Raises:
            LLMError: If classification fails
        """
        categories_str = ", ".join(categories)
        prompt = f"Classify the following text into one of these categories: {categories_str}\n\nText: {text}\n\nCategory:"

        result = await self.generate(prompt, **kwargs)
        return result.content
