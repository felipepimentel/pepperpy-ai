"""LLM (Language Model) providers for the Pepperpy framework.

This module provides the core abstractions and interfaces for working with
Language Models in the PepperPy framework.

Core Components:
- LLMProvider: Base class for all LLM providers
- LLMMessage: Standard message format for LLM interactions
- LLMResponse: Standard response format from LLM providers
- ChatSession: Manages a conversation session with an LLM
- ChatMessage: Represents a message in a chat conversation
- ChatOptions: Configuration options for chat sessions
- ModelInfo: Information about an LLM model
- ModelCapability: Enumeration of model capabilities
- ModelRegistry: Registry of available models

Utility Functions:
- count_tokens: Count tokens in a text string for a specific model
- format_prompt: Format a prompt template with variables
- create_chat_messages: Create a list of chat messages for LLM providers
- extract_code_blocks: Extract code blocks from markdown text
- extract_json: Extract JSON from a text string
"""

# Re-export public interfaces
# Internal implementations
from pepperpy.llm.base import LLMMessage, LLMProvider, LLMResponse
from pepperpy.llm.public import (
    ChatMessage,
    ChatOptions,
    ChatSession,
    ModelCapability,
    ModelInfo,
    ModelRegistry,
)

__all__ = [
    # Public interfaces
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "ChatMessage",
    "ChatOptions",
    "ChatSession",
    "ModelCapability",
    "ModelInfo",
    "ModelRegistry",
]
