"""Plugin manager for PepperPy.

This module handles provider discovery, loading, and management.
"""

import importlib
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Type, cast

from loguru import logger

from pepperpy.core import BaseProvider, ValidationError
from pepperpy.plugin import PepperpyPlugin, discover_plugins


class PluginManager:
    """Manager for PepperPy plugins."""

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self._providers: Dict[str, Dict[str, Dict[str, Any]]] = {
            "llm": {},
            "rag": {},
            "tts": {},
            "workflow": {},
        }
        self._plugin_classes: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {
            "llm": {},
            "rag": {},
            "tts": {},
            "workflow": {},
        }
        self._discover_plugins()

    def _discover_plugins(self) -> None:
        """Discover available plugins from the plugins directory."""
        plugins = discover_plugins()
        for plugin_name, metadata in plugins.items():
            category = metadata.get("category")
            provider_type = metadata.get("provider_name")
            if not category or not provider_type:
                logger.warning(
                    f"Plugin {plugin_name} missing category or provider_name in metadata"
                )
                continue

            if category not in self._providers:
                self._providers[category] = {}

            entry_point = metadata.get("entry_point")
            if not entry_point:
                logger.warning(f"Plugin {plugin_name} missing entry_point in metadata")
                continue

            # Store as plugin_dir:entry_point
            plugin_path = f"{plugin_name}.{entry_point}"
            self._providers[category][provider_type] = {
                "path": plugin_path,
                "metadata": metadata,
            }

            logger.debug(
                f"Discovered plugin: {plugin_name} ({category}/{provider_type})"
            )

    def install_plugin(self, plugin_path: str) -> bool:
        """Install a plugin and its dependencies using UV.

        Args:
            plugin_path: Path to the plugin directory

        Returns:
            True if installation was successful, False otherwise
        """
        requirements_path = Path(plugin_path) / "requirements.txt"
        if not requirements_path.exists():
            logger.warning(f"No requirements.txt found for plugin: {plugin_path}")
            return False

        try:
            # Use UV to install requirements
            logger.info(f"Installing plugin dependencies from {requirements_path}")
            subprocess.run(
                ["uv", "pip", "install", "-r", str(requirements_path)],
                check=True,
                capture_output=True,
            )
            logger.info(f"Successfully installed plugin: {plugin_path}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Failed to install plugin {plugin_path}: {error_msg}")
            return False
        except FileNotFoundError:
            logger.error("UV is not installed. Please install UV: pip install uv")
            return False

    def install_all_plugins(self, plugins_dir: Optional[str] = None) -> Dict[str, bool]:
        """Install all plugins from the plugins directory.

        Args:
            plugins_dir: Optional path to plugins directory

        Returns:
            Dictionary mapping plugin names to installation success
        """
        if plugins_dir is None:
            # Try to find plugins directory relative to this file
            current_dir = Path(__file__).parent
            plugins_dir = str(current_dir.parent / "plugins")

        results = {}
        plugins_path = Path(plugins_dir)
        if not plugins_path.exists():
            logger.warning(f"Plugins directory not found: {plugins_dir}")
            return results

        for plugin_dir in plugins_path.iterdir():
            if not plugin_dir.is_dir():
                continue

            plugin_name = plugin_dir.name
            success = self.install_plugin(str(plugin_dir))
            results[plugin_name] = success

        return results

    def register_provider(
        self,
        module: str,
        provider_type: str,
        provider_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a provider.

        Args:
            module: Module name (e.g., "llm", "rag")
            provider_type: Provider type (e.g., "openai", "anthropic")
            provider_path: Import path to provider class
            metadata: Optional metadata for the provider
        """
        if module not in self._providers:
            self._providers[module] = {}

        self._providers[module][provider_type] = {
            "path": provider_path,
            "metadata": metadata or {},
        }
        logger.debug(
            f"Registered provider: {module}/{provider_type} at {provider_path}"
        )

    def register_provider_class(
        self,
        module: str,
        provider_type: str,
        provider_class: Type[PepperpyPlugin],
    ) -> None:
        """Register a provider class directly.

        Args:
            module: Module name (e.g., "llm", "rag")
            provider_type: Provider type (e.g., "openai", "anthropic")
            provider_class: Provider class
        """
        if module not in self._plugin_classes:
            self._plugin_classes[module] = {}

        self._plugin_classes[module][provider_type] = provider_class
        logger.debug(f"Registered provider class: {module}/{provider_type}")

    def create_provider(
        self,
        module: str,
        provider_type: str,
        **config: Any,
    ) -> BaseProvider:
        """Create a provider instance.

        Args:
            module: Module name (e.g., "llm", "rag")
            provider_type: Provider type (e.g., "openai", "anthropic")
            **config: Provider configuration

        Returns:
            Provider instance

        Raises:
            ValidationError: If provider creation fails
        """
        try:
            # First check if we have a registered class
            if (
                module in self._plugin_classes
                and provider_type in self._plugin_classes[module]
            ):
                provider_class = self._plugin_classes[module][provider_type]
                return cast(BaseProvider, provider_class.from_config(**config))

            # Otherwise, load from registered path
            if module not in self._providers:
                raise ValidationError(f"Unknown module: {module}")

            providers = self._providers[module]
            if provider_type not in providers:
                available = ", ".join(providers.keys()) if providers else "none"
                raise ValidationError(
                    f"Unknown provider '{provider_type}' for module '{module}'. "
                    f"Available providers: {available}"
                )

            provider_info = providers[provider_type]
            provider_path = provider_info["path"]

            if ":" in provider_path:
                # Format is package.module:ClassName
                module_path, class_name = provider_path.split(":")
            else:
                # Assume default format
                module_path = f"{provider_type}_provider.provider"
                class_name = f"{provider_type.capitalize()}Provider"

            try:
                module_obj = importlib.import_module(module_path)
            except ImportError as e:
                # Try to get package name from module path
                package = module_path.split(".")[0]

                # Try to install the plugin using UV
                plugin_dir = Path("plugins") / f"{module}_{provider_type}"
                if plugin_dir.exists():
                    if self.install_plugin(str(plugin_dir)):
                        # Retry import after installation
                        try:
                            module_obj = importlib.import_module(module_path)
                        except ImportError:
                            pass

                raise ValidationError(
                    f"Failed to import provider '{provider_type}'. "
                    f"Make sure you have installed the plugin: {module}_{provider_type}"
                ) from e

            provider_class = getattr(module_obj, class_name)
            return cast(BaseProvider, provider_class(**config))

        except Exception as e:
            logger.error(f"Failed to create provider: {e}")
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to create provider: {e}")

    def get_provider_info(
        self,
        module: str,
        provider_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get information about available providers.

        Args:
            module: Module name
            provider_type: Optional provider type to get specific info

        Returns:
            Provider information
        """
        if module not in self._providers:
            return {}

        if provider_type:
            if provider_type not in self._providers[module]:
                return {}
            return {"type": provider_type, **self._providers[module][provider_type]}

        return {
            type_: {"type": type_, **info}
            for type_, info in self._providers[module].items()
        }

    def list_plugins(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """List all available plugins.

        Returns:
            Dictionary with plugin information by category and type
        """
        return self._providers


# Global plugin manager instance
plugin_manager = PluginManager()
