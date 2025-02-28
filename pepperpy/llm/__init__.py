"""LLM (Language Model) providers for the Pepperpy framework.

This module provides integrations with various LLM providers including:
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Google (Gemini)
- Perplexity
- OpenRouter
"""

from pepperpy.llm.base import LLMMessage, LLMProvider, LLMResponse
from pepperpy.llm.providers.anthropic import AnthropicProvider
from pepperpy.llm.providers.gemini import GeminiProvider
from pepperpy.llm.providers.openai import OpenAIConfig, OpenAIProvider
from pepperpy.llm.providers.openrouter import OpenRouterConfig, OpenRouterProvider
from pepperpy.llm.providers.perplexity import PerplexityConfig, PerplexityProvider

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
