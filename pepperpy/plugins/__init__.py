"""PepperPy plugin system.

This package provides the plugin system for PepperPy, including:
- Base plugin classes
- Plugin manager
- Plugin discovery and loading
- Plugin installation and management
"""

from pepperpy.plugins.manager import PluginManager
from pepperpy.plugins.plugin import (
    PepperpyPlugin,
    ProviderPlugin,
    discover_plugins,
    install_plugin_dependencies,
)
from pepperpy.plugins.providers import (
    BaseProvider,
    FileProvider,
    HTTPProvider,
    LocalProvider,
    RemoteProvider,
    RestProvider,
)

__all__ = [
    # Base plugin classes
    "PepperpyPlugin",
    "ProviderPlugin",
    # Plugin manager
    "PluginManager",
    # Plugin utilities
    "discover_plugins",
    "install_plugin_dependencies",
    # Provider classes
    "BaseProvider",
    "RemoteProvider",
    "LocalProvider",
    "RestProvider",
    "FileProvider",
    "HTTPProvider",
]
