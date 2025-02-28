"""LLM (Language Model) providers for the Pepperpy framework.

This module provides integrations with various LLM providers including:
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Google (Gemini)
- Perplexity
- OpenRouter
"""

from pepperpy.llm.base import LLMMessage, LLMProvider, LLMResponse
from pepperpy.providers.llm.anthropic import AnthropicProvider
from pepperpy.providers.llm.gemini import GeminiProvider
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
    "GeminiProvider",
    "PerplexityConfig",
    "PerplexityProvider",
    "OpenRouterConfig",
    "OpenRouterProvider",
]
