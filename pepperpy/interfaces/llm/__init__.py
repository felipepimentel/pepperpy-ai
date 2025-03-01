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

Factory Functions:
    create_provider: Create an LLM provider instance based on configuration
    get_default_provider: Get the default LLM provider based on configuration

Utility Functions:
    count_tokens: Count tokens in a text string for a specific model
    format_prompt: Format a prompt template with variables
    create_chat_messages: Create a list of chat messages for LLM providers
    extract_code_blocks: Extract code blocks from markdown text
    extract_json: Extract JSON from a text string
"""

# Import public classes and functions from the implementation
from pepperpy.llm import (
    AnthropicProvider,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    OpenAIConfig,
    OpenAIProvider,
    OpenRouterConfig,
    OpenRouterProvider,
    PerplexityConfig,
    PerplexityProvider,
    count_tokens,
    create_chat_messages,
    create_provider,
    extract_code_blocks,
    extract_json,
    format_prompt,
    get_default_provider,
)

__all__ = [
    # Core interfaces
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    # Provider implementations
    "OpenAIConfig",
    "OpenAIProvider",
    "AnthropicProvider",
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
