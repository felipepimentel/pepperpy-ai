"""Plugin loader for Pepperpy CLI.

This module provides functionality to discover, load, and manage CLI plugins.
"""

import importlib
import importlib.util
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type

import click

from pepperpy.core.common.logging import get_logger

logger = get_logger(__name__)

# Type definitions
PluginCommand = click.Command
PluginCommandGroup = click.Group
PluginCommandType = PluginCommand | PluginCommandGroup
PluginInfo = Dict[str, Any]


class PluginRegistry:
    """Registry for CLI plugins."""

    _instance = None
    _plugins: Dict[str, PluginInfo] = {}
    _commands: Dict[str, List[PluginCommandType]] = {}

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
        return cls._instance

    def register_plugin(self, plugin_id: str, plugin_info: PluginInfo) -> None:
        """Register a plugin with the registry.

        Args:
            plugin_id: Unique identifier for the plugin
            plugin_info: Plugin metadata and configuration
        """
        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} already registered, overwriting")
        
        self._plugins[plugin_id] = plugin_info
        self._commands[plugin_id] = []
        logger.debug(f"Registered plugin: {plugin_id}")

    def register_command(self, plugin_id: str, command: PluginCommandType) -> None:
        """Register a command from a plugin.

        Args:
            plugin_id: Plugin identifier
            command: Click command or group
        """
        if plugin_id not in self._plugins:
            raise ValueError(f"Plugin {plugin_id} not registered")
        
        self._commands[plugin_id].append(command)
        logger.debug(f"Registered command {command.name} from plugin {plugin_id}")

    def get_plugins(self) -> Dict[str, PluginInfo]:
        """Get all registered plugins.

        Returns:
            Dictionary of plugin_id to plugin_info
        """
        return self._plugins.copy()

    def get_commands(self) -> Dict[str, List[PluginCommandType]]:
        """Get all registered commands.

        Returns:
            Dictionary of plugin_id to list of commands
        """
        return self._commands.copy()

    def get_plugin_commands(self, plugin_id: str) -> List[PluginCommandType]:
        """Get commands for a specific plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            List of commands for the plugin
        """
        return self._commands.get(plugin_id, [])


def discover_plugins() -> List[Tuple[str, Path]]:
    """Discover available plugins.

    Returns:
        List of (plugin_id, plugin_path) tuples
    """
    plugin_dirs = [
        # User plugins
        Path.home() / ".pepperpy" / "plugins",
        # System plugins
        Path(sys.prefix) / "share" / "pepperpy" / "plugins",
        # Development plugins
        Path(__file__).parent.parent.parent.parent / "plugins",
    ]

    plugins = []
    for plugin_dir in plugin_dirs:
        if not plugin_dir.exists():
            continue

        for item in plugin_dir.iterdir():
            if not item.is_dir():
                continue
                
            # Check if this is a valid plugin directory
            if (item / "cli.py").exists() or (item / "cli" / "__init__.py").exists():
                plugin_id = item.name
                plugins.append((plugin_id, item))
                logger.debug(f"Discovered plugin: {plugin_id} at {item}")

    return plugins


def load_plugin(plugin_id: str, plugin_path: Path) -> Optional[PluginInfo]:
    """Load a plugin from the given path.

    Args:
        plugin_id: Plugin identifier
        plugin_path: Path to the plugin directory

    Returns:
        Plugin info dictionary or None if loading failed
    """
    try:
        # Try loading as a module
        if (plugin_path / "cli.py").exists():
            spec = importlib.util.spec_from_file_location(
                f"pepperpy_plugin_{plugin_id}", 
                plugin_path / "cli.py"
            )
            if spec is None or spec.loader is None:
                logger.error(f"Failed to load plugin {plugin_id}: invalid spec")
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            # Try loading as a package
            sys.path.insert(0, str(plugin_path.parent))
            module = importlib.import_module(f"{plugin_path.name}.cli")
            sys.path.pop(0)

        # Extract plugin info
        plugin_info = getattr(module, "PLUGIN_INFO", {})
        if not plugin_info:
            plugin_info = {
                "name": plugin_id,
                "version": "0.1.0",
                "description": f"Plugin {plugin_id}",
            }

        # Register plugin
        registry = PluginRegistry()
        registry.register_plugin(plugin_id, plugin_info)

        # Register commands
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, (click.Command, click.Group)) and not name.startswith("_"):
                registry.register_command(plugin_id, obj)

        return plugin_info

    except Exception as e:
        logger.error(f"Failed to load plugin {plugin_id}: {e}")
        return None


def load_all_plugins() -> Dict[str, PluginInfo]:
    """Discover and load all available plugins.

    Returns:
        Dictionary of plugin_id to plugin_info for successfully loaded plugins
    """
    plugins = discover_plugins()
    loaded_plugins = {}

    for plugin_id, plugin_path in plugins:
        plugin_info = load_plugin(plugin_id, plugin_path)
        if plugin_info:
            loaded_plugins[plugin_id] = plugin_info

    return loaded_plugins


def get_plugin_commands() -> Dict[str, List[PluginCommandType]]:
    """Get all commands from loaded plugins.

    Returns:
        Dictionary of plugin_id to list of commands
    """
    registry = PluginRegistry()
    return registry.get_commands() 