"""Plugin system for PepperPy.

This package provides the plugin system infrastructure for PepperPy,
allowing dynamic discovery and loading of providers.
"""

from pepperpy.plugins.discovery import (
    discover_plugins,
    get_plugin,
    get_plugin_by_provider,
)
from pepperpy.plugins.manager import (
    PluginManager,
    create_provider_instance,
    get_plugin_manager,
)
from pepperpy.plugins.plugin import PepperpyPlugin

__all__ = [
    "PepperpyPlugin",
    "PluginManager",
    "discover_plugins",
    "get_plugin",
    "get_plugin_by_provider",
    "create_provider_instance",
    "get_plugin_manager",
]
