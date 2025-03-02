"""Adapters for integration with third-party frameworks and libraries.

This module provides a plugin-based architecture for integrating with external frameworks:
- Adapter discovery: Automatically discover and load adapter plugins
- Extension points: Define extension points for adapters to hook into
- Adapter management: Register, enable, disable, and configure adapters
- Adapter isolation: Isolate adapters to prevent conflicts

The adapter system enables the framework to be extended with new integrations
without modifying the core codebase, facilitating modularity and customization.
"""

from pepperpy.adapters.base import BaseAdapter
from pepperpy.adapters.plugin import AdapterPlugin, load_adapter_plugins
from pepperpy.adapters.registry import AdapterRegistry

__all__ = [
    "BaseAdapter",
    "AdapterRegistry",
    "AdapterPlugin",
    "load_adapter_plugins",
]
