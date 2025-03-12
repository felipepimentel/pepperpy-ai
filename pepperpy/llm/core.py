"""Core functionality for the LLM module.

This module provides the core functionality for working with Large Language Models
in the PepperPy framework. It defines the base classes and interfaces that are used
throughout the LLM module.
"""

from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.core.base_provider import BaseProvider
from pepperpy.types.common import ModelName, Result
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


class LLMResult(Result[str]):
    """Result of an LLM operation.

    This class extends the generic Result class to provide LLM-specific
    result information.

    Attributes:
        success: Whether the operation was successful
        data: The generated text (if successful)
        error: Error message (if unsuccessful)
        metadata: Additional metadata about the operation
        model: The model used for generation
        usage: Token usage information
    """

    def __init__(
        self,
        success: bool = True,
        data: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
    ) -> None:
        """Initialize a new LLM result.

        Args:
            success: Whether the operation was successful
            data: The generated text (if successful)
            error: Error message (if unsuccessful)
            metadata: Additional metadata about the operation
            model: The model used for generation
            usage: Token usage information
        """
        super().__init__(
            success=success, data=data, error=error, metadata=metadata or {}
        )
        self.model = model
        self.usage = usage or {}

        if model:
            self.metadata["model"] = model
        if usage:
            self.metadata["usage"] = usage


class LLMProvider(BaseProvider):
    """Base class for LLM providers.

    This class defines the interface that all LLM providers must implement.
    It extends the BaseProvider class to provide LLM-specific functionality.
    """

    def __init__(
        self,
        name: str,
        default_model: ModelName,
        **kwargs: Any,
    ) -> None:
        """Initialize a new LLM provider.

        Args:
            name: Provider name
            default_model: Default model to use
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(name=name, **kwargs)
        self.default_model = default_model

    async def generate(
        self,
        prompt: str,
        model: Optional[ModelName] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate text based on the prompt.

        This is the main method for generating text using the LLM provider.

        Args:
            prompt: The prompt to generate text from
            model: The model to use (defaults to the provider's default model)
            **kwargs: Additional generation parameters

        Returns:
            LLMResult with the generated text

        Raises:
            ProviderError: If generation fails
        """
        raise NotImplementedError("Subclasses must implement generate")

    async def embed(
        self,
        text: str,
        model: Optional[ModelName] = None,
        **kwargs: Any,
    ) -> Result[List[float]]:
        """Generate embeddings for the given text.

        Args:
            text: The text to generate embeddings for
            model: The model to use (defaults to the provider's default model)
            **kwargs: Additional embedding parameters

        Returns:
            Result with the embedding vector

        Raises:
            ProviderError: If embedding generation fails
        """
        raise NotImplementedError("Subclasses must implement embed")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Dict with provider capabilities
        """
        return {
            "supports_generation": True,
            "supports_embeddings": False,  # Override in subclasses
            "supports_streaming": False,  # Override in subclasses
            "default_model": self.default_model,
        }


class LLMManager:
    """Manager for LLM providers.

    The LLM manager provides a unified interface for working with different LLM
    providers, including model management, provider registration, and generating
    completions and embeddings.
    """

    def __init__(self):
        """Initialize the LLM manager."""
        self._providers: Dict[str, LLMProvider] = {}
        self._default_provider: Optional[str] = None

    async def close(self) -> None:
        """Close all providers and release resources."""
        for provider_name, provider in self._providers.items():
            try:
                await provider.close()
            except Exception as e:
                logger.warning(f"Error closing provider '{provider_name}': {e}")

        self._providers.clear()
        self._default_provider = None

    def register_provider(
        self, name: str, provider: LLMProvider, default: bool = False
    ) -> None:
        """Register a provider.

        Args:
            name: The name of the provider
            provider: The provider to register
            default: Whether to set this provider as the default

        Raises:
            LLMError: If a provider with the same name is already registered
        """
        if name in self._providers:
            raise LLMError(f"Provider '{name}' is already registered")

        self._providers[name] = provider

        if default or self._default_provider is None:
            self._default_provider = name

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider.

        Args:
            name: The name of the provider to unregister

        Raises:
            LLMError: If the provider is not registered
        """
        if name not in self._providers:
            raise LLMError(f"Provider '{name}' is not registered")

        del self._providers[name]

        if self._default_provider == name:
            self._default_provider = (
                next(iter(self._providers)) if self._providers else None
            )

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """Get a provider.

        Args:
            name: The name of the provider to get, or None to get the default provider

        Returns:
            The provider

        Raises:
            LLMError: If the provider is not registered or no default provider is set
        """
        if name is None:
            if self._default_provider is None:
                raise LLMError("No default provider is set")

            name = self._default_provider

        if name not in self._providers:
            raise LLMError(f"Provider '{name}' is not registered")

        return self._providers[name]

    def set_default_provider(self, name: str) -> None:
        """Set the default provider.

        Args:
            name: The name of the provider to set as the default

        Raises:
            LLMError: If the provider is not registered
        """
        if name not in self._providers:
            raise LLMError(f"Provider '{name}' is not registered")

        self._default_provider = name

    def get_default_provider(self) -> Optional[str]:
        """Get the name of the default provider.

        Returns:
            The name of the default provider, or None if no default provider is set
        """
        return self._default_provider

    def get_providers(self) -> Dict[str, LLMProvider]:
        """Get all registered providers.

        Returns:
            A dictionary of provider names to providers
        """
        return self._providers.copy()

    async def complete(
        self,
        prompt: Union[str, Prompt],
        provider: Optional[str] = None,
    ) -> Response:
        """Generate a completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for
            provider: The name of the provider to use, or None to use the default provider

        Returns:
            The generated completion

        Raises:
            LLMError: If there is an error generating the completion
        """
        # Get the provider
        provider_instance = self.get_provider(provider)

        # Generate the completion
        return await provider_instance.complete(prompt)

    async def stream_complete(
        self,
        prompt: Union[str, Prompt],
        provider: Optional[str] = None,
    ) -> AsyncIterator[StreamingResponse]:
        """Generate a streaming completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for
            provider: The name of the provider to use, or None to use the default provider

        Returns:
            An async iterator of response chunks

        Raises:
            LLMError: If there is an error generating the completion
        """
        # Get the provider
        provider_instance = self.get_provider(provider)

        # Generate the streaming completion
        async for chunk in provider_instance.stream_complete(prompt):
            yield chunk

    async def embed(
        self,
        text: str,
        provider: Optional[str] = None,
    ) -> List[float]:
        """Generate embeddings for the given text.

        Args:
            text: The text to generate embeddings for
            provider: The name of the provider to use, or None to use the default provider

        Returns:
            The generated embeddings

        Raises:
            LLMError: If there is an error generating the embeddings
        """
        # Get the provider
        provider_instance = self.get_provider(provider)

        # Generate the embeddings
        return await provider_instance.embed(text)

    async def tokenize(
        self,
        text: str,
        provider: Optional[str] = None,
    ) -> List[str]:
        """Tokenize the given text.

        Args:
            text: The text to tokenize
            provider: The name of the provider to use, or None to use the default provider

        Returns:
            The list of tokens

        Raises:
            LLMError: If there is an error tokenizing the text
        """
        # Get the provider
        provider_instance = self.get_provider(provider)

        # Tokenize the text
        return await provider_instance.tokenize(text)

    async def count_tokens(
        self,
        text: str,
        provider: Optional[str] = None,
    ) -> int:
        """Count the number of tokens in the given text.

        Args:
            text: The text to count tokens in
            provider: The name of the provider to use, or None to use the default provider

        Returns:
            The number of tokens

        Raises:
            LLMError: If there is an error counting tokens
        """
        # Get the provider
        provider_instance = self.get_provider(provider)

        # Count the tokens
        return await provider_instance.count_tokens(text)


# Global LLM manager
_llm_manager = LLMManager()


def get_llm_manager() -> LLMManager:
    """Get the global LLM manager.

    Returns:
        The global LLM manager
    """
    return _llm_manager


async def complete(
    prompt: Union[str, Prompt],
    provider: Optional[str] = None,
) -> Response:
    """Generate a completion for the given prompt.

    Args:
        prompt: The prompt to generate a completion for
        provider: The name of the provider to use, or None to use the default provider

    Returns:
        The generated completion

    Raises:
        LLMError: If there is an error generating the completion
    """
    return await get_llm_manager().complete(prompt, provider)


async def stream_complete(
    prompt: Union[str, Prompt],
    provider: Optional[str] = None,
) -> AsyncIterator[StreamingResponse]:
    """Generate a streaming completion for the given prompt.

    Args:
        prompt: The prompt to generate a completion for
        provider: The name of the provider to use, or None to use the default provider

    Returns:
        An async iterator of response chunks

    Raises:
        LLMError: If there is an error generating the completion
    """
    async for chunk in get_llm_manager().stream_complete(prompt, provider):
        yield chunk


async def embed(
    text: str,
    provider: Optional[str] = None,
) -> List[float]:
    """Generate embeddings for the given text.

    Args:
        text: The text to generate embeddings for
        provider: The name of the provider to use, or None to use the default provider

    Returns:
        The generated embeddings

    Raises:
        LLMError: If there is an error generating the embeddings
    """
    return await get_llm_manager().embed(text, provider)


async def tokenize(
    text: str,
    provider: Optional[str] = None,
) -> List[str]:
    """Tokenize the given text.

    Args:
        text: The text to tokenize
        provider: The name of the provider to use, or None to use the default provider

    Returns:
        The list of tokens

    Raises:
        LLMError: If there is an error tokenizing the text
    """
    return await get_llm_manager().tokenize(text, provider)


async def count_tokens(
    text: str,
    provider: Optional[str] = None,
) -> int:
    """Count the number of tokens in the given text.

    Args:
        text: The text to count tokens in
        provider: The name of the provider to use, or None to use the default provider

    Returns:
        The number of tokens

    Raises:
        LLMError: If there is an error counting tokens
    """
    return await get_llm_manager().count_tokens(text, provider)
