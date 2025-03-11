"""Base classes for LLM providers in PepperPy.

This module provides the base classes for LLM providers in PepperPy.
It defines the interface that all LLM providers must implement.
"""

import abc
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.core.base_provider import BaseProvider
from pepperpy.errors.core import PepperPyError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class LLMError(PepperPyError):
    """Error raised by LLM providers."""

    pass


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


class LLMProvider(BaseProvider, abc.ABC):
    """Base class for LLM providers.

    All LLM providers must implement this interface to ensure consistent behavior
    across different implementations.
    """

    def __init__(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the LLM provider.

        Args:
            provider_name: Optional specific name for this provider
            model_name: Name of the LLM model
            **kwargs: Provider-specific configuration
        """
        super().__init__(
            provider_type="llm",
            provider_name=provider_name,
            model_name=model_name,
            **kwargs,
        )
        # Add LLM-specific capabilities
        self.add_capability("text_generation")

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
    async def tokenize(self, text: str) -> List[str]:
        """Tokenize the given text.

        Args:
            text: The text to tokenize

        Returns:
            The tokenized text

        Raises:
            LLMError: If there is an error tokenizing the text
        """
        pass

    @abc.abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens

        Raises:
            LLMError: If there is an error counting tokens
        """
        pass

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return self.config.copy()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {"capabilities": list(self._capabilities)}


# Register provider type with global registry
from pepperpy.core.base_provider import provider_registry

provider_registry.register("llm", LLMProvider)
