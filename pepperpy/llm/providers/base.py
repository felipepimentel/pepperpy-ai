"""Base interfaces and types for LLM providers.

This module defines the base interfaces and types that all LLM providers must implement.
It ensures consistent behavior across different LLM implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.interfaces import Provider


@dataclass
class Message:
    """A message in a conversation with an LLM.

    Attributes:
        role: The role of the message sender (e.g., "system", "user", "assistant")
        content: The content of the message
        name: Optional name of the sender
        metadata: Additional metadata about the message
    """

    role: str
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Prompt:
    """A prompt to be sent to an LLM.

    Attributes:
        messages: The messages in the conversation
        temperature: Controls randomness in the response (0.0 to 2.0)
        max_tokens: Maximum number of tokens to generate
        stop: Optional list of strings that will stop generation
        metadata: Additional metadata about the prompt
    """

    messages: List[Message]
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """A response from an LLM.

    Attributes:
        text: The generated text
        usage: Token usage information
        metadata: Additional metadata about the response
    """

    text: str
    usage: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamingResponse:
    """A streaming response chunk from an LLM.

    Attributes:
        text: The generated text chunk
        is_finished: Whether this is the last chunk
        metadata: Additional metadata about the chunk
    """

    text: str
    is_finished: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(Provider, ABC):
    """Base class for LLM providers.

    All LLM providers must implement this interface to ensure consistent behavior
    across different implementations.
    """

    @abstractmethod
    async def complete(self, prompt: Union[str, Prompt]) -> Response:
        """Generate a completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for

        Returns:
            The generated completion

        Raises:
            LLMError: If there is an error generating the completion
        """
        pass

    @abstractmethod
    async def stream_complete(
        self, prompt: Union[str, Prompt]
    ) -> AsyncIterator[StreamingResponse]:
        """Generate a streaming completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for

        Returns:
            An async iterator of response chunks

        Raises:
            LLMError: If there is an error generating the completion
        """
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for the given text.

        Args:
            text: The text to generate embeddings for

        Returns:
            The generated embeddings

        Raises:
            LLMError: If there is an error generating the embeddings
        """
        pass

    @abstractmethod
    async def tokenize(self, text: str) -> List[str]:
        """Tokenize the given text.

        Args:
            text: The text to tokenize

        Returns:
            The list of tokens

        Raises:
            LLMError: If there is an error tokenizing the text
        """
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Args:
            text: The text to count tokens in

        Returns:
            The number of tokens

        Raises:
            LLMError: If there is an error counting tokens
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
            The provider capabilities
        """
        pass
