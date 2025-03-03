"""Common utilities and shared components for the PepperPy framework.

This module provides common utilities, types, and shared components that are
used throughout the PepperPy framework. These components provide foundational
functionality that is reused across different parts of the system.

It includes:
- Core types and enumerations
- Utility functions for common operations
- Registry system for component management
- Versioning and compatibility management
"""

from pepperpy.core.common.utils import collections, config, data, dates, files, numbers, serialization
from pepperpy.core.errors import PepperpyError, ValidationError, ConfigError
from pepperpy.core.types import BaseComponent, ComponentType
from pepperpy.core.versioning import Version, VersionInfo

__version__ = "0.1.0"
