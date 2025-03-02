"""Provider implementations for LLM capabilities.

This module contains implementations of various LLM (Large Language Model) providers
that integrate with external LLM services and APIs, including:

- OpenAI: Integration with OpenAI's GPT models
- Anthropic: Integration with Anthropic's Claude models
- Google: Integration with Google's Gemini models
- OpenRouter: Integration with OpenRouter's API
- Perplexity: Integration with Perplexity's API

These providers enable text generation, chat completion, and other language model
capabilities for various applications.
"""

from pepperpy.llm.providers.anthropic import AnthropicProvider
from pepperpy.llm.providers.base import (
    BaseLLMProvider,
    ChatMessage,
    CompletionOptions,
    LLMProvider,
    LLMResponse,
    MessageRole,
    ModelParameters,
    get_llm_provider,
    list_llm_providers,
    register_llm_provider,
)
from pepperpy.llm.providers.gemini import GeminiProvider
from pepperpy.llm.providers.openai import OpenAIProvider
from pepperpy.llm.providers.openrouter import OpenRouterProvider
from pepperpy.llm.providers.perplexity import PerplexityProvider

__all__ = [
    "AnthropicProvider",
    "BaseLLMProvider",
    "ChatMessage",
    "CompletionOptions",
    "GeminiProvider",
    "LLMProvider",
    "LLMResponse",
    "MessageRole",
    "ModelParameters",
    "OpenAIProvider",
    "OpenRouterProvider",
    "PerplexityProvider",
    "get_llm_provider",
    "list_llm_providers",
    "register_llm_provider",
]
