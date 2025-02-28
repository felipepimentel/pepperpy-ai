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
    GeminiProvider: Provider for Google Gemini models
    PerplexityProvider: Provider for Perplexity models
    OpenRouterProvider: Provider for OpenRouter models
"""

# Import public classes and functions from the implementation
from pepperpy.llm import (
    AnthropicProvider,
    GeminiProvider,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    OpenAIConfig,
    OpenAIProvider,
    OpenRouterConfig,
    OpenRouterProvider,
    PerplexityConfig,
    PerplexityProvider,
)

__all__ = [
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "OpenAIConfig",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "PerplexityConfig",
    "PerplexityProvider",
    "OpenRouterConfig",
    "OpenRouterProvider",
]
