"""
Public Interface for llm

This module provides a stable public interface for the llm functionality.
It exposes the core LLM abstractions and implementations that are
considered part of the public API.

Classes:
    LLMProvider: Base class for language model providers
    LLMMessage: Message format for LLM interactions
    LLMResponse: Response format from LLM providers
    ChatSession: Manages a conversation session with an LLM
    ChatMessage: Represents a message in a chat conversation
    ChatOptions: Configuration options for chat sessions
    ModelInfo: Information about an LLM model
    ModelCapability: Enumeration of model capabilities
    ModelRegistry: Registry of available models
"""

# Import core interfaces from the base module
from pepperpy.llm.base import LLMMessage, LLMProvider, LLMResponse

# Import chat interfaces
from .chat import ChatMessage, ChatOptions, ChatSession

# Import model interfaces
from .models import ModelCapability, ModelInfo, ModelRegistry

__all__ = [
    # Core interfaces
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    # Chat interfaces
    "ChatMessage",
    "ChatOptions",
    "ChatSession",
    # Model interfaces
    "ModelCapability",
    "ModelInfo",
    "ModelRegistry",
]
