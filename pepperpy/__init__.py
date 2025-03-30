"""PepperPy Framework.

A modular framework for building AI applications.
"""

from pepperpy.core import BaseProvider, ConfigError, ProviderError
from pepperpy.core.logging import get_logger
from pepperpy.llm import LLMProvider, Message, MessageRole
from pepperpy.pepperpy import PepperPy
from pepperpy.plugin import ProviderPlugin, install_plugin_dependencies
from pepperpy.plugin_manager import plugin_manager
from pepperpy.rag.base import create_provider as create_rag_provider

__version__ = "0.1.0"

__all__ = [
    "BaseProvider",
    "ConfigError",
    "LLMProvider",
    "Message",
    "MessageRole",
    "PepperPy",
    "ProviderError",
    "ProviderPlugin",
    "create_rag_provider",
    "get_logger",
    "install_plugin_dependencies",
    "plugin_manager",
]
