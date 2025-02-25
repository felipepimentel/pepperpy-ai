"""Plugin management system.

This module provides plugin management functionality:
- Plugin discovery and loading
- Plugin lifecycle management
- Plugin dependency resolution
- Plugin configuration and state
"""

from pepperpy.core.plugins.manager import Plugin, PluginManager, PluginMetadata

# Export public API
__all__ = [
    "Plugin",
    "PluginManager",
    "PluginMetadata",
]
