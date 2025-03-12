"""Public API for the LLM module.

This module provides the public API for working with Large Language Models
in the PepperPy framework. It offers simplified interfaces for common operations
like generating text and embeddings.
"""

from typing import Any, List, Optional, Union

from pepperpy.llm.core import LLMManager, LLMProvider, LLMResult
from pepperpy.types.common import ModelName, Result
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

# Global LLM manager instance
manager = LLMManager()


async def generate(
    prompt: str,
    provider: Optional[Union[str, LLMProvider]] = None,
    model: Optional[ModelName] = None,
    **kwargs: Any,
) -> LLMResult:
    """Generate text based on the prompt.

    This is the main function for generating text using an LLM provider.

    Args:
        prompt: The prompt to generate text from
        provider: The provider to use (name or instance)
        model: The model to use
        **kwargs: Additional generation parameters

    Returns:
        LLMResult with the generated text

    Example:
        >>> result = await generate("Explain quantum computing in simple terms")
        >>> print(result.data)
        Quantum computing is like regular computing but instead of using bits...
    """
    return await manager.generate(prompt, provider=provider, model=model, **kwargs)


async def embed(
    text: str,
    provider: Optional[Union[str, LLMProvider]] = None,
    model: Optional[ModelName] = None,
    **kwargs: Any,
) -> Result[List[float]]:
    """Generate embeddings for the given text.

    Args:
        text: The text to generate embeddings for
        provider: The provider to use (name or instance)
        model: The model to use
        **kwargs: Additional embedding parameters

    Returns:
        Result with the embedding vector

    Example:
        >>> result = await embed("Quantum computing")
        >>> print(len(result.data))
        1536
    """
    return await manager.embed(text, provider=provider, model=model, **kwargs)


def register_provider(provider: LLMProvider) -> None:
    """Register an LLM provider.

    Args:
        provider: The provider to register

    Example:
        >>> from pepperpy.llm.providers import OpenAIProvider
        >>> provider = OpenAIProvider(api_key="...")
        >>> register_provider(provider)
    """
    manager.register_provider(provider)


def get_provider(name: str) -> LLMProvider:
    """Get a registered LLM provider by name.

    Args:
        name: The name of the provider

    Returns:
        The provider instance

    Raises:
        ValueError: If the provider is not found

    Example:
        >>> provider = get_provider("openai")
        >>> result = await provider.generate("Hello, world!")
    """
    return manager.get_provider(name)


def list_providers() -> List[str]:
    """List all registered LLM providers.

    Returns:
        List of provider names

    Example:
        >>> providers = list_providers()
        >>> print(providers)
        ['openai', 'anthropic']
    """
    return manager.list_providers()
