"""Core functionality for PepperPy.

This module provides the core functionality for PepperPy, including:
- Base classes and interfaces
- Memory management
- Configuration handling
- Logging and monitoring
- Type definitions
"""

from pepperpy.core.base import BaseProvider
from pepperpy.core.config import Config
from pepperpy.core.logging import Logger
from pepperpy.core.memory import BaseMemory, MemoryManager
from pepperpy.core.monitoring import MetricsCollector
from pepperpy.core.types import Metadata

__all__ = [
    "BaseProvider",
    "Config",
    "Logger",
    "BaseMemory",
    "MemoryManager",
    "MetricsCollector",
    "Metadata",
]
