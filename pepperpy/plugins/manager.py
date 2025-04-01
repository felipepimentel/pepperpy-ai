"""Plugin manager for PepperPy.

This module provides the plugin manager for PepperPy, which handles plugin
discovery, loading, and management.
"""

import asyncio
import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

import yaml

from pepperpy.core.errors import ProviderError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

T = TypeVar("T", bound=PepperpyPlugin)


class PluginManager:
    """Plugin manager for PepperPy.

    This class implements singleton behavior and is responsible for:
    - Discovering plugins on startup
    - Loading plugin metadata
    - Managing plugin dependencies
    - Installing plugins
    - Providing plugin information
    """

    _instance = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        """Initialize plugin manager."""
        if PluginManager._instance is not None:
            raise RuntimeError("Use PluginManager.get_instance() instead")

        self._plugins: Dict[str, Dict[str, Any]] = {}
        self._plugin_classes: Dict[str, Type[PepperpyPlugin]] = {}
        self._plugin_instances: Dict[str, PepperpyPlugin] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

        # Initialize logger
        self._logger = get_logger(__name__)

    @classmethod
    async def get_instance(cls) -> "PluginManager":
        """Get singleton instance.

        Returns:
            PluginManager instance
        """
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
                    await cls._instance._discover_plugins()
        return cls._instance

    async def _discover_plugins(self) -> None:
        """Discover available plugins.

        This method is called on startup to discover and load plugin metadata.
        """
        if self._initialized:
            return

        try:
            # Get plugins directory relative to this file
            plugins_dir = Path(__file__).parent.parent / "plugins"
            if not plugins_dir.exists():
                self._logger.warning(f"Plugins directory not found: {plugins_dir}")
                return

            # Scan plugins directory
            for item in plugins_dir.iterdir():
                if not item.is_dir():
                    continue

                # Check for plugin metadata
                yaml_path = item.joinpath("plugin.yaml")
                json_path = item.joinpath("plugin.json")

                metadata = None
                if yaml_path.exists():
                    try:
                        with open(yaml_path) as f:
                            metadata = yaml.safe_load(f)
                    except Exception as e:
                        self._logger.warning(
                            f"Error loading plugin.yaml for {item.name}: {e}"
                        )

                if metadata is None and json_path.exists():
                    try:
                        with open(json_path) as f:
                            metadata = json.load(f)
                    except Exception as e:
                        self._logger.warning(
                            f"Error loading plugin.json for {item.name}: {e}"
                        )

                if metadata:
                    self._plugins[item.name] = metadata
                    await self._register_plugin_info(item.name, metadata)

            self._initialized = True

        except Exception as e:
            self._logger.error(f"Error discovering plugins: {e}")
            raise ProviderError(f"Failed to discover plugins: {e}") from e

    async def _register_plugin_info(
        self, plugin_name: str, metadata: Dict[str, Any]
    ) -> None:
        """Register plugin information.

        Args:
            plugin_name: Name of the plugin
            metadata: Plugin metadata
        """
        try:
            # Get plugin directory
            plugins_dir = Path(__file__).parent.parent / "plugins"
            plugin_dir = plugins_dir / plugin_name

            # Check for main module
            main_module = metadata.get("main_module", "plugin.py")
            main_path = plugin_dir / main_module

            if not main_path.exists():
                self._logger.warning(
                    f"Main module not found for plugin {plugin_name}: {main_path}"
                )
                return

            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                f"pepperpy.plugins.{plugin_name}", str(main_path)
            )
            if spec is None or spec.loader is None:
                self._logger.warning(f"Failed to load plugin module for {plugin_name}")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = None
            for item in dir(module):
                if item.startswith("_"):
                    continue

                obj = getattr(module, item)
                if isinstance(obj, type) and issubclass(obj, PepperpyPlugin):
                    plugin_class = obj
                    break

            if plugin_class is None:
                self._logger.warning(f"No plugin class found for {plugin_name}")
                return

            # Register plugin class
            self._plugin_classes[plugin_name] = plugin_class

            # Load plugin configuration
            config_path = plugin_dir / "config.yaml"
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        self._plugin_configs[plugin_name] = yaml.safe_load(f)
                except Exception as e:
                    self._logger.warning(f"Error loading config for {plugin_name}: {e}")

        except Exception as e:
            self._logger.error(f"Error registering plugin {plugin_name}: {e}")

    async def get_plugin(
        self, plugin_name: str, **config: Any
    ) -> Optional[PepperpyPlugin]:
        """Get plugin instance.

        Args:
            plugin_name: Name of the plugin
            **config: Plugin configuration

        Returns:
            Plugin instance or None if not found

        Raises:
            ConfigError: If plugin configuration is invalid
            ProviderError: If plugin initialization fails
        """
        try:
            # Check if plugin exists
            if plugin_name not in self._plugin_classes:
                self._logger.warning(f"Plugin not found: {plugin_name}")
                return None

            # Get plugin class and configuration
            plugin_class = self._plugin_classes[plugin_name]
            plugin_config = self._plugin_configs.get(plugin_name, {})

            # Merge configurations
            merged_config = {**plugin_config, **config}

            # Create plugin instance
            instance = plugin_class(**merged_config)
            await instance.initialize()

            # Store instance
            self._plugin_instances[plugin_name] = instance

            return instance

        except Exception as e:
            self._logger.error(f"Error getting plugin {plugin_name}: {e}")
            raise ProviderError(f"Failed to get plugin {plugin_name}: {e}") from e

    async def install_plugin(
        self, plugin_name: str, source: str
    ) -> Optional[PepperpyPlugin]:
        """Install plugin from source.

        Args:
            plugin_name: Name of the plugin
            source: Plugin source (path or URL)

        Returns:
            Installed plugin instance or None if installation failed

        Raises:
            ConfigError: If plugin configuration is invalid
            ProviderError: If plugin installation fails
        """
        try:
            # Get plugins directory
            plugins_dir = Path(__file__).parent.parent / "plugins"
            plugin_dir = plugins_dir / plugin_name

            # Create plugin directory
            plugin_dir.mkdir(parents=True, exist_ok=True)

            # Clone repository if source is URL
            if source.startswith(("http://", "https://")):
                try:
                    subprocess.run(
                        ["git", "clone", source, str(plugin_dir)],
                        check=True,
                        capture_output=True,
                    )
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr.decode() if e.stderr else str(e)
                    raise ProviderError(
                        f"Failed to clone plugin repository: {error_msg}"
                    ) from e

            # Copy files if source is path
            else:
                source_path = Path(source)
                if not source_path.exists():
                    raise ConfigError(f"Plugin source not found: {source}")

                if source_path.is_dir():
                    # Copy directory contents
                    for item in source_path.iterdir():
                        if item.is_dir():
                            os.system(f"cp -r {item} {plugin_dir}")
                        else:
                            os.system(f"cp {item} {plugin_dir}")
                else:
                    # Copy single file
                    os.system(f"cp {source_path} {plugin_dir}")

            # Check for plugin metadata
            yaml_path = plugin_dir / "plugin.yaml"
            if not yaml_path.exists():
                raise ConfigError(f"Plugin metadata not found: {yaml_path}")

            # Load plugin metadata
            with open(yaml_path) as f:
                metadata = yaml.safe_load(f)

            # Install dependencies
            requirements_path = plugin_dir / "requirements.txt"
            if requirements_path.exists():
                try:
                    # Try to use UV if available
                    try:
                        subprocess.run(
                            ["uv", "pip", "install", "-r", str(requirements_path)],
                            check=True,
                            capture_output=True,
                        )
                    except FileNotFoundError:
                        # Fall back to pip if UV is not available
                        subprocess.run(
                            [
                                sys.executable,
                                "-m",
                                "pip",
                                "install",
                                "-r",
                                str(requirements_path),
                            ],
                            check=True,
                            capture_output=True,
                        )
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr.decode() if e.stderr else str(e)
                    raise ProviderError(
                        f"Failed to install dependencies: {error_msg}"
                    ) from e

            # Register plugin
            await self._register_plugin_info(plugin_name, metadata)

            # Get plugin instance
            return await self.get_plugin(plugin_name)

        except Exception as e:
            self._logger.error(f"Error installing plugin {plugin_name}: {e}")
            raise ProviderError(f"Failed to install plugin {plugin_name}: {e}") from e

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin information.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin metadata or None if not found
        """
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """List available plugins.

        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())

    async def cleanup(self) -> None:
        """Clean up plugin resources."""
        for instance in self._plugin_instances.values():
            try:
                await instance.cleanup()
            except Exception as e:
                self._logger.warning(f"Error cleaning up plugin: {e}")

        self._plugin_instances.clear()
        self._initialized = False

    async def __aenter__(self) -> "PluginManager":
        """Enter async context.

        Returns:
            Self for context management
        """
        return await self.get_instance()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        await self.cleanup()
