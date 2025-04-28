"""
PepperPy LLM Module.

This module provides large language model capabilities for PepperPy.
"""

from typing import Any

from pepperpy.llm.adapter import (
    AnthropicAdapter,
    LLMAdapter,
    LLMAdapterError,
    LLMProviderAdapter,
    Message,
    MessageRole,
    OllamaAdapter,
    OpenAIAdapter,
    create_llm_adapter,
)
from pepperpy.llm.base import LLMProvider, BaseLLMProvider
from pepperpy.llm.provider import create_provider

# Import provider implementations for registration
try:
    from .providers.openai import OpenAIProvider
except ImportError:
    pass

try:
    from .providers.anthropic import AnthropicProvider
except ImportError:
    pass

try:
    from .providers.stackspot import StackSpotAIProvider
except ImportError:
    pass

__all__ = [
    "AnthropicAdapter",
    "LLMAdapter",
    "LLMAdapterError",
    "LLMProvider",
    "LLMProviderAdapter",
    "Message",
    "MessageRole",
    "OllamaAdapter",
    "OpenAIAdapter",
    "create_llm_adapter",
    "create_provider",
]
