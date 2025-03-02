"""
Public Interface for llm

This module provides a stable public interface for the llm functionality.
It exposes the core LLM abstractions and implementations that are
considered part of the public API.

Classes:
    LLMProvider: Base class for language model providers
    LLMMessage: Message format for LLM interactions
    LLMResponse: Response format from LLM providers
"""

# Import core interfaces from the base module
from pepperpy.llm.base import LLMMessage, LLMProvider, LLMResponse

__all__ = [
    # Core interfaces
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
]
