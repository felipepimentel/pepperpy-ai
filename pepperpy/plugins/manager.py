"""Plugin manager for PepperPy."""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Type

from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.discovery import (
    get_plugin_by_provider,
)
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)

# Track if dotenv has been loaded
_dotenv_loaded = False


def _ensure_dotenv_loaded() -> None:
    """Ensure dotenv is loaded.

    This function tries to load environment variables from .env files
    at different locations. It's a no-op if dotenv has been loaded before.
    """
    global _dotenv_loaded
    if _dotenv_loaded:
        return

    try:
        # Try to import dotenv
        try:
            from dotenv import load_dotenv
        except ImportError:
            logger.debug("python-dotenv not installed, will not load .env files")
            _dotenv_loaded = True
            return

        # List of potential .env file locations to try
        env_files = [
            os.path.join(os.getcwd(), ".env"),  # Current directory
            os.path.join(os.path.expanduser("~"), ".pepperpy", ".env"),  # User config
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), ".env"
            ),  # Project root
        ]

        # Try to load from each location
        for env_file in env_files:
            if os.path.exists(env_file):
                logger.debug(f"Loading environment from {env_file}")
                load_dotenv(env_file)

        # Also check for .env file in parent directories up to 3 levels
        current_dir = Path.cwd()
        for _ in range(3):
            parent_dir = current_dir.parent
            if parent_dir == current_dir:  # Reached filesystem root
                break

            env_file = parent_dir / ".env"
            if env_file.exists():
                logger.debug(f"Loading environment from {env_file}")
                load_dotenv(str(env_file))

            current_dir = parent_dir

        _dotenv_loaded = True
    except Exception as e:
        logger.warning(f"Failed to load environment variables from .env files: {e}")
        _dotenv_loaded = True  # Prevent further attempts


@dataclass
class PluginInfo:
    """Information about a plugin."""

    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    documentation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginManager:
    """Manager for PepperPy plugins."""

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self._plugins: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {}
        self._instances: Dict[str, Dict[str, PepperpyPlugin]] = {}
        self._initialized = False

    def register_plugin(
        self, plugin_type: str, provider_type: str, plugin_class: Type[PepperpyPlugin]
    ) -> None:
        """Register a plugin.

        Args:
            plugin_type: Type of plugin (e.g., "llm", "rag")
            provider_type: Type of provider (e.g., "openai", "local")
            plugin_class: Plugin class to register
        """
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}
        self._plugins[plugin_type][provider_type] = plugin_class
        logger.debug(f"Registered plugin: {plugin_type}/{provider_type}")

    def get_plugin(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Type[PepperpyPlugin]]:
        """Get a plugin class.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin class if found, None otherwise
        """
        return self._plugins.get(plugin_type, {}).get(provider_type)

    def create_instance(
        self, plugin_type: str, provider_type: str, **config: Any
    ) -> PepperpyPlugin:
        """Create a plugin instance.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            **config: Plugin configuration

        Returns:
            Plugin instance

        Raises:
            ValidationError: If plugin not found or creation fails
        """
        # Get plugin class
        plugin_class = self.get_plugin(plugin_type, provider_type)
        if not plugin_class:
            raise ValidationError(f"Plugin not found: {plugin_type}/{provider_type}")

        # Create instance
        try:
            instance = plugin_class(**config)
            if plugin_type not in self._instances:
                self._instances[plugin_type] = {}
            self._instances[plugin_type][provider_type] = instance
            return instance
        except Exception as e:
            raise ValidationError(f"Failed to create plugin instance: {e}") from e

    def get_instance(
        self, plugin_type: str, provider_type: str
    ) -> Optional[PepperpyPlugin]:
        """Get a plugin instance.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin instance if found, None otherwise
        """
        return self._instances.get(plugin_type, {}).get(provider_type)

    async def initialize(self) -> None:
        """Initialize plugin manager."""
        if self._initialized:
            return

        # Initialize all instances
        for instances in self._instances.values():
            for instance in instances.values():
                await instance.initialize()

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up plugin manager."""
        # Clean up all instances
        for instances in self._instances.values():
            for instance in instances.values():
                await instance.cleanup()

        self._instances.clear()
        self._initialized = False


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager.

    Returns:
        Plugin manager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def create_provider_instance(
    plugin_type: str,
    provider_type: str,
    require_api_key: bool = False,
    **kwargs: Any,
) -> Any:
    """Create a provider instance from plugin and provider types.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider
        require_api_key: Whether the provider requires an API key
        **kwargs: Additional arguments to pass to the provider

    Returns:
        Provider instance

    Raises:
        ValidationError: If plugin or provider is not found, or if API key is required but not provided
    """
    logger.debug(f"Creating provider instance: {plugin_type}/{provider_type}")

    # Ensure .env files are loaded to get configuration
    _ensure_dotenv_loaded()

    # Check if API key is required and not provided in kwargs
    if require_api_key:
        # Build standardized API key parameter name: {provider_type}_api_key
        api_key_param = f"{provider_type}_api_key"

        # Check if API key is provided in kwargs with the standardized name
        if api_key_param not in kwargs or not kwargs[api_key_param]:
            # Try alternative parameter name format: api_key
            if "api_key" not in kwargs or not kwargs["api_key"]:
                # Try to get from environment variables in order of preference
                # 1. PEPPERPY_{PLUGIN_TYPE}_{PROVIDER_TYPE}_API_KEY (e.g., PEPPERPY_LLM_OPENROUTER_API_KEY)
                # 2. PEPPERPY_{PLUGIN_TYPE}__API_KEY (e.g., PEPPERPY_LLM__API_KEY)
                # 3. {PROVIDER_TYPE}_API_KEY (e.g., OPENROUTER_API_KEY)
                plugin_type_upper = plugin_type.upper()
                provider_type_upper = provider_type.upper()

                env_var_specific = (
                    f"PEPPERPY_{plugin_type_upper}_{provider_type_upper}_API_KEY"
                )
                env_var_generic = f"PEPPERPY_{plugin_type_upper}__API_KEY"
                env_var_direct = f"{provider_type_upper}_API_KEY"

                api_key = (
                    os.environ.get(env_var_specific)
                    or os.environ.get(env_var_generic)
                    or os.environ.get(env_var_direct)
                )

                if not api_key:
                    error_msg = (
                        f"API key required for {plugin_type}/{provider_type}. "
                        f"Set either in config or via one of these environment variables: "
                        f"{env_var_specific}, {env_var_generic}, {env_var_direct}"
                    )
                    raise ValidationError(error_msg)

                # Use the standardized parameter name for the API key
                kwargs[api_key_param] = api_key

        # Ensure the traditional api_key parameter is also set for backward compatibility
        if "api_key" not in kwargs:
            kwargs["api_key"] = kwargs[api_key_param]

    # Get plugin class
    plugin_class = get_plugin_by_provider(plugin_type, provider_type)
    if not plugin_class:
        raise ValidationError(f"Provider not found: {plugin_type}/{provider_type}")

    try:
        # Create instance
        provider_instance = plugin_class(**kwargs)
        return provider_instance
    except Exception as e:
        raise ValidationError(f"Failed to create provider instance: {e}") from e


def install_plugin_dependencies(plugin_path: str) -> None:
    """Install plugin dependencies from requirements.txt.

    Args:
        plugin_path: Path to plugin directory

    Raises:
        ValidationError: If installation fails
    """
    requirements_file = os.path.join(plugin_path, "requirements.txt")
    if not os.path.exists(requirements_file):
        logger.debug(f"No requirements.txt found in {plugin_path}")
        return

    try:
        subprocess.check_call(
            ["pip", "install", "-r", requirements_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Installed dependencies for plugin at {plugin_path}")
    except subprocess.CalledProcessError as e:
        raise ValidationError(
            f"Failed to install plugin dependencies: {e.stderr.decode()}"
        ) from e
