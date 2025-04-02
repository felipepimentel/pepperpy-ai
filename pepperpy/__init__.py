"""PepperPy Framework

This module provides a flexible and extensible framework for AI applications.
"""

# Core components
from pepperpy.core import (
    Config,
    PepperpyError,
    get_logger,
)

# Domain-specific providers
from pepperpy.llm import LLMProvider, Message, MessageRole
from pepperpy.pepperpy import PepperPy, init_framework
from pepperpy.plugins.plugin import PepperpyPlugin

# Initialize singleton
_instance = PepperPy.get_instance()

# Export convenience methods
ask = _instance.ask_query
process = _instance.process_content
create = _instance.create_content
analyze = _instance.analyze_data

__version__ = "0.1.0"

__all__ = [
    # Core components
    "Config",
    "PepperpyError",
    "get_logger",
    # Framework
    "PepperPy",
    "init_framework",
    # Plugin system
    "PepperpyPlugin",
    # LLM components
    "LLMProvider",
    "Message",
    "MessageRole",
    # High-level API
    "ask",
    "process",
    "create",
    "analyze",
]
