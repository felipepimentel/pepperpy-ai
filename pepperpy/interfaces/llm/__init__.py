"""
Public Interface for llm

This module provides a stable public interface for the llm functionality.
It exposes the core LLM abstractions and implementations that are
considered part of the public API.

Classes:
    LLMProvider: Base class for language model providers
    LLMMessage: Message format for LLM interactions
    LLMResponse: Response format from LLM providers

Implementations:
    OpenAIProvider: Provider for OpenAI models
    AnthropicProvider: Provider for Anthropic Claude models
    PerplexityProvider: Provider for Perplexity models
    OpenRouterProvider: Provider for OpenRouter models
"""

# Import public classes and functions from the implementation
from pepperpy.llm.base import LLMMessage, LLMProvider, LLMResponse
from pepperpy.providers.llm.anthropic import AnthropicProvider

# Comentando importação que não existe
# from pepperpy.providers.llm.gemini import GeminiProvider
from pepperpy.providers.llm.openai import OpenAIConfig, OpenAIProvider
from pepperpy.providers.llm.openrouter import OpenRouterConfig, OpenRouterProvider
from pepperpy.providers.llm.perplexity import PerplexityConfig, PerplexityProvider

__all__ = [
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "OpenAIConfig",
    "OpenAIProvider",
    "AnthropicProvider",
    # "GeminiProvider",  # Comentando classe que não existe
    "PerplexityConfig",
    "PerplexityProvider",
    "OpenRouterConfig",
    "OpenRouterProvider",
]
