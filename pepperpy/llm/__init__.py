"""Language Model (LLM) capabilities for PepperPy.

This module provides interfaces and implementations for working with
Language Models, including local and cloud-based providers.

Example:
    >>> from pepperpy.llm import LLMProvider, Message, MessageRole
    >>> provider = LLMProvider.from_config({
    ...     "provider": "openai",
    ...     "model": "gpt-4",
    ...     "api_key": "sk-..."
    ... })
    >>> messages = [
    ...     Message(role=MessageRole.SYSTEM, content="You are helpful."),
    ...     Message(role=MessageRole.USER, content="What's the weather?")
    ... ]
    >>> result = await provider.generate(messages)
    >>> print(result.content)
"""

from pepperpy.llm.base import (
    GenerationChunk,
    GenerationResult,
    LLMError,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.llm.local import LocalProvider
from pepperpy.llm.openai import OpenAIProvider

__all__ = [
    "GenerationChunk",
    "GenerationResult",
    "LLMError",
    "LLMProvider",
    "LocalProvider",
    "Message",
    "MessageRole",
    "OpenAIProvider",
]
