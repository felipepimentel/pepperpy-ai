"""
PepperPy Core Module.

Main module for the PepperPy framework.
"""

from pepperpy.agent import AgentProvider
from pepperpy.cache import CacheProvider
from pepperpy.core import configure_logging, get_logger
from pepperpy.llm import LLMProvider
from pepperpy.pepperpy import PepperPy
from pepperpy.plugin.base.discovery import BaseDiscoveryProvider
from pepperpy.storage import StorageProvider
from pepperpy.tool import ToolProvider
from pepperpy.tts import TTSProvider

__version__ = "0.1.0"

__all__ = [
    # Main framework entry point
    "PepperPy",
    # Base provider interfaces
    "AgentProvider",
    "BaseDiscoveryProvider",
    "CacheProvider",
    "LLMProvider",
    "StorageProvider",
    "ToolProvider",
    "TTSProvider",
    # Logging utilities
    "configure_logging",
    "get_logger",
]
