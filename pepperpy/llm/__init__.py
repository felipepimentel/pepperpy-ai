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
