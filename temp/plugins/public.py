"""Public interfaces for PepperPy Plugins module.

This module provides a stable public interface for the plugins functionality.
It exposes the core plugin abstractions and functions that are considered part
of the public API.
"""

from pepperpy.plugins.core import (
    Plugin,
    PluginEvent,
    PluginInfo,
    PluginManager,
    PluginState,
    get_plugin_manager,
)

# Re-export everything
__all__ = [
    # Classes
    "Plugin",
    "PluginEvent",
    "PluginInfo",
    "PluginManager",
    "PluginState",
    # Functions
    "get_plugin_manager",
]
