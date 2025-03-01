"""LLM (Language Model) providers for the Pepperpy framework.

This module provides the core abstractions and interfaces for working with
Language Models in the PepperPy framework. The actual implementations of
these interfaces are located in the `pepperpy.providers.llm` module.

This module serves as a convenient namespace for the core LLM functionality,
while the stable public API is available through `pepperpy.interfaces.llm`.

Core Components:
- LLMProvider: Base class for all LLM providers
- LLMMessage: Standard message format for LLM interactions
- LLMResponse: Standard response format from LLM providers

Provider Implementations:
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Google (Gemini)
- Perplexity
- OpenRouter

Factory Functions:
- create_provider: Create an LLM provider instance based on configuration
- get_default_provider: Get the default LLM provider based on configuration

Utility Functions:
- count_tokens: Count tokens in a text string for a specific model
- format_prompt: Format a prompt template with variables
- create_chat_messages: Create a list of chat messages for LLM providers
- extract_code_blocks: Extract code blocks from markdown text
- extract_json: Extract JSON from a text string

Note: This module follows the pattern of separating interfaces from implementations.
The base interfaces are defined here, while the concrete implementations are in
the providers/llm/ module. This separation allows for cleaner dependency management
and easier testing.
"""

from pepperpy.llm.base import LLMMessage, LLMProvider, LLMResponse
from pepperpy.llm.factory import create_provider, get_default_provider
from pepperpy.llm.utils import (
    count_tokens,
    create_chat_messages,
    extract_code_blocks,
    extract_json,
    format_prompt,
)
from pepperpy.providers.llm.anthropic import AnthropicProvider
from pepperpy.providers.llm.gemini import GeminiProvider
from pepperpy.providers.llm.openai import OpenAIConfig, OpenAIProvider
from pepperpy.providers.llm.openrouter import OpenRouterConfig, OpenRouterProvider
from pepperpy.providers.llm.perplexity import PerplexityConfig, PerplexityProvider

__all__ = [
    # Core interfaces
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    # Provider implementations
    "OpenAIConfig",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "PerplexityConfig",
    "PerplexityProvider",
    "OpenRouterConfig",
    "OpenRouterProvider",
    # Factory functions
    "create_provider",
    "get_default_provider",
    # Utility functions
    "count_tokens",
    "format_prompt",
    "create_chat_messages",
    "extract_code_blocks",
    "extract_json",
]
