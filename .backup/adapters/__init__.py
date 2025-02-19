"""Framework adapters for Pepperpy.

This module provides adapters for integrating Pepperpy with various
AI agent frameworks like LangChain, AutoGen, Semantic Kernel, and CrewAI.
"""

from pepperpy.adapters.autogen import AutoGenAdapter
from pepperpy.adapters.base import BaseFrameworkAdapter
from pepperpy.adapters.crewai import CrewAIAdapter
from pepperpy.adapters.errors import (
    AdapterError,
    ConfigurationError,
    ConversionError,
    ValidationError,
)
from pepperpy.adapters.langchain import LangChainAdapter
from pepperpy.adapters.semantic_kernel import SemanticKernelAdapter

__all__ = [
    "AdapterError",
    "AutoGenAdapter",
    "BaseFrameworkAdapter",
    "ConfigurationError",
    "ConversionError",
    "CrewAIAdapter",
    "LangChainAdapter",
    "SemanticKernelAdapter",
    "ValidationError",
]
