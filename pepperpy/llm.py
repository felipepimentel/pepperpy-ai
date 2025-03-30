"""LLM interfaces and types.

This module defines the core interfaces and data types for working with
Language Model providers in PepperPy.
"""

import abc
import enum
import functools
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from pepperpy.core import BaseProvider, ConfigError, ProviderError
from pepperpy.core.logging import get_logger
from pepperpy.plugin_manager import plugin_manager

# Module-level logger
logger = get_logger(__name__)

T = TypeVar("T")


class MessageRole(str, enum.Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """A message in a conversation."""

    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResult:
    """Result of a text generation request."""

    content: str
    messages: List[Message]
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GenerationChunk:
    """A chunk of generated text from a streaming response."""

    content: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMError(ProviderError):
    """Base error for the LLM module."""

    pass


def _handle_provider_method(method_name: str) -> Callable:
    """Decorator to handle provider method lifecycle and errors.

    This decorator manages initialization, logging, and error handling for provider methods.

    Args:
        method_name: Name of the method for logging purposes

    Returns:
        Decorated method
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self: "LLMProvider", *args: Any, **kwargs: Any) -> T:
            try:
                # Handle cleanup method specially
                if method_name == "cleanup":
                    # Run the cleanup method
                    result = await func(self, *args, **kwargs)
                    # Framework manages initialization state
                    self._set_initialized_state(False)
                    logger.debug(
                        f"{self.__class__.__name__} marked as uninitialized after cleanup"
                    )
                    return result

                # Auto-validation of configuration
                if not self.initialized:
                    # Auto-initialize if not already initialized
                    logger.debug(
                        f"Auto-initializing provider {self.__class__.__name__} before {method_name}"
                    )
                    await self.initialize()
                    # Framework manages initialization state
                    self._set_initialized_state(True)
                    logger.debug(f"{self.__class__.__name__} marked as initialized")

                # Run the actual method
                result = await func(self, *args, **kwargs)
                return result

            except ConfigError as e:
                # Log configuration errors
                logger.error(
                    f"{self.__class__.__name__} {method_name} failed with configuration error: {e}"
                )
                raise

            except Exception as e:
                # Log operational errors
                logger.error(f"{self.__class__.__name__} {method_name} failed: {e}")
                # Convert to ProviderError with original context
                if not isinstance(e, ProviderError):
                    raise ProviderError(f"{method_name} failed: {e}") from e
                raise

        return wrapper

    return decorator


class LLMProvider(BaseProvider):
    """Base class for LLM providers."""

    name: str = "base"

    # Common auto-bound attributes used by LLM providers
    temperature: float
    max_tokens: int
    model: str
    api_key: str

    @abc.abstractmethod
    @_handle_provider_method("generate")
    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text based on input messages.

        Args:
            messages: Input messages or a single string message
            **kwargs: Additional generation options

        Returns:
            A GenerationResult containing the generated text and metadata

        Raises:
            ConfigError: If configuration is invalid
            ProviderError: If generation fails
        """
        pass

    @abc.abstractmethod
    @_handle_provider_method("generate_stream")
    async def generate_stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text in streaming mode based on input messages.

        Args:
            messages: Input messages or a single string message
            **kwargs: Additional generation options

        Returns:
            An async iterator yielding GenerationChunk objects

        Raises:
            ConfigError: If configuration is invalid
            ProviderError: If generation fails
        """
        pass

    @_handle_provider_method("stream")
    async def stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Alias for generate_stream.

        Args:
            messages: Input messages or a single string message
            **kwargs: Additional generation options

        Returns:
            An async iterator yielding GenerationChunk objects

        Raises:
            ConfigError: If configuration is invalid
            ProviderError: If generation fails
        """
        async for chunk in self.generate_stream(messages, **kwargs):
            yield chunk

    @_handle_provider_method("cleanup")
    async def cleanup(self) -> None:
        """Clean up provider resources.

        The framework will automatically set the initialized flag to False after cleanup.
        Providers should release resources but not manage the initialized state.

        Raises:
            ProviderError: If cleanup fails
        """
        # Base implementation - override in subclasses
        pass

    # Framework-managed property to track initialization state
    def _set_initialized_state(self, state: bool) -> None:
        """Set the initialized state (framework use only)."""
        self._initialized = state

    @property
    def initialized(self) -> bool:
        """Check if the provider is initialized."""
        return getattr(self, "_initialized", False)

    @initialized.setter
    def initialized(self, value: bool) -> None:
        """Set the initialized state."""
        self._set_initialized_state(value)


def create_provider(provider_type: str, **config: Any) -> LLMProvider:
    """Create an LLM provider instance.

    Args:
        provider_type: Type of provider to create
        **config: Provider configuration

    Returns:
        LLM provider instance

    Raises:
        ConfigError: If provider creation fails
    """
    try:
        provider = plugin_manager.create_provider("llm", provider_type, **config)
        return cast(LLMProvider, provider)
    except Exception as e:
        logger.error(f"Failed to create LLM provider {provider_type}: {e}")
        raise ConfigError(f"Failed to create LLM provider {provider_type}: {e}") from e
