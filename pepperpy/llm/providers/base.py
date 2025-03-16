"""Base classes for LLM providers in PepperPy.

This module provides the base classes for LLM providers in PepperPy.
It defines the interface that all LLM providers must implement.
"""

import abc
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.core.base import BaseProvider
from pepperpy.core.errors import PepperPyError
from pepperpy.core.registry import Registry
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Create a registry for LLM providers
provider_registry = Registry[Any]("llm_provider_registry", "llm_provider")


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


@dataclass
class LLMResult:
    """Result of a language model generation.

    Attributes:
        text: The generated text
        model_name: The name of the model used
        usage: Token usage information
        metadata: Additional metadata about the generation
    """

    text: str
    model_name: str
    usage: Dict[str, int]
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
        name = provider_name or f"{self.__class__.__name__}_{id(self)}"
        super().__init__(name=name, **kwargs)
        self.provider_type = "llm"
        self.model_name = model_name

        # Initialize capabilities
        self._capabilities = set()

        # Add default capabilities
        self.add_capability("text_generation")

    def add_capability(self, capability: str) -> None:
        """Add a capability to this provider.

        Args:
            capability: The capability to add
        """
        self._capabilities.add(capability)

    def has_capability(self, capability: str) -> bool:
        """Check if this provider has a specific capability.

        Args:
            capability: The capability to check for

        Returns:
            Whether the provider has this capability
        """
        return capability in self._capabilities

    @abc.abstractmethod
    async def generate(self, prompt: Union[str, List[Message]], **options) -> LLMResult:
        """Generate text using the provider's API.

        Args:
            prompt: The prompt to generate text from (string or list of messages)
            **options: Additional options for generation

        Returns:
            The generated text result

        Raises:
            LLMError: If generation fails
        """
        pass

    @abc.abstractmethod
    async def generate_stream(
        self, prompt: Union[str, List[Message]], **options
    ) -> AsyncIterator[LLMResult]:
        """Generate text in a streaming fashion.

        Args:
            prompt: The prompt to generate text from (string or list of messages)
            **options: Additional options for generation

        Yields:
            The generated text chunks

        Raises:
            LLMError: If generation fails
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
provider_registry.register("llm", LLMProvider)
