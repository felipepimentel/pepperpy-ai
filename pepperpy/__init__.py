"""PepperPy Framework.

A modular framework for building AI applications.
"""

from pepperpy.core import BaseProvider, ConfigError, ProviderError
from pepperpy.core.logging import get_logger
from pepperpy.llm import LLMProvider, Message, MessageRole
from pepperpy.plugin import ProviderPlugin

__version__ = "0.1.0"

__all__ = [
    "BaseProvider",
    "ConfigError",
    "LLMProvider",
    "Message",
    "MessageRole",
    "ProviderError",
    "ProviderPlugin",
    "get_logger",
]
