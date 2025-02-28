"""Plugin system for Pepperpy CLI.

This package provides functionality for loading and managing CLI plugins.
"""

from pepperpy.cli.plugins.config import (
    disable_plugin,
    enable_plugin,
    get_enabled_plugins,
    is_plugin_enabled,
    load_plugin_config,
    save_plugin_config,
)
from pepperpy.cli.plugins.loader import (
    PluginRegistry,
    discover_plugins,
    get_plugin_commands,
    load_all_plugins,
    load_plugin,
)

__all__ = [
    "PluginRegistry",
    "discover_plugins",
    "get_plugin_commands",
    "load_all_plugins",
    "load_plugin",
    "disable_plugin",
    "enable_plugin",
    "get_enabled_plugins",
    "is_plugin_enabled",
    "load_plugin_config",
    "save_plugin_config",
] 