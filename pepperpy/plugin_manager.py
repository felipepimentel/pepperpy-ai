"""Plugin manager for PepperPy.

This module handles provider discovery, loading, and management.
"""

import importlib
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Type, cast

from pepperpy.core import BaseProvider, ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugin import PepperpyPlugin, discover_plugins

# Initialize logger
logger = get_logger(__name__)


class PluginManager:
    """Plugin manager for the PepperPy framework.

    This class manages plugin discovery, registration, loading, and instantiation.
    It provides utilities for working with plugins and registering custom providers.
    """

    _instance = None

    def __new__(cls) -> "PluginManager":
        """Create a new PluginManager instance or return the existing one.

        Returns:
            Singleton instance of PluginManager
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the plugin manager."""
        if not getattr(self, "_initialized", False):
            # Dictionary of provider types and their registration info
            self._providers: Dict[str, Dict[str, Dict[str, Any]]] = {}

            # Dictionary of provider classes
            self._plugin_classes: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {}

            # Force discovery of plugins on startup
            self._discover_plugins()
            self._initialized = True

    def _discover_plugins(self) -> None:
        """Discover available plugins."""
        logger = get_logger(__name__)

        # Initialize empty dictionaries for providers and plugin classes
        categories = [
            "llm",
            "rag",
            "tts",
            "workflow",
            "agents",
            "content_processing",
            "cache",
            "cli",
            "embeddings",
            "hub",
            "storage",
            "tools",
        ]

        # Limpar e reinicializar os dicionários de providers e classes
        self._providers = {category: {} for category in categories}
        self._plugin_classes = {category: {} for category in categories}

        # Discover plugins
        plugins = discover_plugins()
        logger.info(f"Discovered {len(plugins)} plugins")

        # Processar cada plugin e registrá-lo
        for plugin_name, metadata in plugins.items():
            logger.debug(f"Processing plugin: {plugin_name} with metadata: {metadata}")

            # Obter campos críticos
            category = metadata.get("category")
            provider_name = metadata.get("provider_name")
            entry_point = metadata.get("entry_point")

            # Verificar se os campos obrigatórios existem
            if not category:
                logger.warning(f"Plugin {plugin_name} missing category in metadata")
                continue

            if not provider_name:
                logger.warning(
                    f"Plugin {plugin_name} missing provider_name in metadata"
                )
                continue

            if not entry_point:
                logger.warning(f"Plugin {plugin_name} missing entry_point in metadata")
                continue

            # Garantir que a categoria exista nos dicionários
            if category not in self._providers:
                logger.debug(f"Creating new category: {category}")
                self._providers[category] = {}
                self._plugin_classes[category] = {}

            # Registrar o plugin
            plugin_path = f"{plugin_name}.{entry_point}"
            self._providers[category][provider_name] = {
                "path": plugin_path,
                "metadata": metadata,
            }

            logger.debug(
                f"Registered plugin: {plugin_name} ({category}/{provider_name})"
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
        debug_logger = get_logger("pepperpy.config.debug")

        # Log environment variables
        print(
            f"DEBUG: Checking for env var PEPPERPY_{module.upper()}__{provider_type.upper()}_API_KEY"
        )
        env_key = f"PEPPERPY_{module.upper()}__{provider_type.upper()}_API_KEY"
        if env_key in os.environ:
            value = os.environ[env_key]
            masked = f"{value[:5]}...{value[-5:]}" if len(value) > 10 else "***"
            print(f"DEBUG: Found env var {env_key} = {masked}")

        debug_logger.debug(f"Creating provider: {module}/{provider_type}")
        debug_logger.debug(f"Provider configuration: {config}")

        # Check for environment variables prefixed with PEPPERPY_{module}__{provider_type} e.g., PEPPERPY_LLM__OPENROUTER_API_KEY
        added_from_env = {}
        debug_logger.debug(f"Checking for env vars for {module}/{provider_type}")
        for env_var, env_value in os.environ.items():
            debug_logger.debug(f"Checking env var: {env_var}")
            if env_var.startswith(
                f"PEPPERPY_{module.upper()}__{provider_type.upper()}_"
            ):
                # Extract the key suffix (e.g., API_KEY from PEPPERPY_LLM__OPENROUTER_API_KEY)
                key_suffix = env_var.split(
                    f"PEPPERPY_{module.upper()}__{provider_type.upper()}_"
                )[1].lower()
                debug_logger.debug(
                    f"Found matching env var: {env_var}, key_suffix: {key_suffix}"
                )

                # Create provider-prefixed key (e.g., openrouter_api_key)
                provider_prefixed_key = f"{provider_type.lower()}_{key_suffix}"
                debug_logger.debug(f"Provider prefixed key: {provider_prefixed_key}")
                if provider_prefixed_key not in config:
                    config[provider_prefixed_key] = env_value
                    added_from_env[provider_prefixed_key] = env_value
                    debug_logger.debug(f"Added key to config: {provider_prefixed_key}")
                else:
                    debug_logger.debug(
                        f"Key already in config: {provider_prefixed_key}"
                    )

        # Only log if environment variables were actually found
        if added_from_env:
            # Create a masked version for sensitive values in debug logs
            masked_added = {}
            for k, v in added_from_env.items():
                if any(
                    sensitive in k.lower()
                    for sensitive in ["key", "secret", "password", "token"]
                ):
                    masked_added[k] = f"{v[:5]}...{v[-5:]}" if len(v) > 10 else "***"
                else:
                    masked_added[k] = v

            debug_logger.debug(f"Added to config from environment: {masked_added}")

        try:
            # First check if we have a registered class
            if (
                module in self._plugin_classes
                and provider_type in self._plugin_classes[module]
            ):
                provider_class = self._plugin_classes[module][provider_type]
                debug_logger.debug(
                    f"Creating provider from registered class: {provider_class.__name__}"
                )

                # Create provider instance
                try:
                    debug_logger.debug("Creating instance using from_config method")
                    provider = provider_class.from_config(**config)
                except (AttributeError, TypeError) as e:
                    debug_logger.warning(
                        f"Could not use from_config method: {e}, trying direct instantiation"
                    )
                    # Try direct instantiation if from_config is not available
                    provider = provider_class(**config)

                # Ensure plugin is initialized from YAML if it's a ProviderPlugin
                if hasattr(provider, "initialize_from_yaml"):
                    # Find and initialize from plugin.yaml
                    plugin_dir = f"plugins/{module}_{provider_type}"
                    yaml_path = f"{plugin_dir}/plugin.yaml"
                    try:
                        debug_logger.debug(
                            f"Initializing plugin from YAML: {yaml_path}"
                        )
                        provider.initialize_from_yaml(yaml_path)
                    except Exception as yaml_error:
                        debug_logger.warning(
                            f"Error initializing from YAML: {yaml_error}"
                        )

                return cast(BaseProvider, provider)

            # Otherwise, load from registered path
            if module not in self._providers:
                available_modules = list(self._providers.keys())
                logger.error(
                    f"Unknown module: {module}. Available modules: {available_modules}"
                )
                raise ValidationError(
                    f"Unknown module: {module}. Available modules: {available_modules}"
                )

            providers = self._providers[module]
            if provider_type not in providers:
                available = ", ".join(providers.keys()) if providers else "none"
                logger.error(
                    f"Unknown provider '{provider_type}' for module '{module}'. "
                    f"Available providers: {available}"
                )
                raise ValidationError(
                    f"Unknown provider '{provider_type}' for module '{module}'. "
                    f"Available providers: {available}"
                )

            provider_info = providers[provider_type]
            provider_path = provider_info["path"]
            debug_logger.debug(f"Loading provider from path: {provider_path}")

            if ":" in provider_path:
                # Format is plugin_name.provider:Provider
                parts = provider_path.split(":")
                plugin_name = parts[0].split(".")[
                    0
                ]  # Pegar apenas o nome do plugin sem o .provider
                class_name = parts[1]
                # Usar o diretório real do plugin
                module_path = f"plugins.{plugin_name}.provider"
                debug_logger.debug(
                    f"Importing from module: {module_path}, class: {class_name}"
                )
            else:
                # Assume default format - diretório do plugin é llm_openrouter
                module_path = f"plugins.{module}_{provider_type}.provider"
                # Preservar capitalização especial para certos providers
                if provider_type == "openrouter":
                    class_name = "OpenRouterProvider"
                elif provider_type == "openai":
                    class_name = "OpenAIProvider"
                else:
                    # Capitalizar apenas a primeira letra e manter o resto como está
                    class_name = (
                        f"{provider_type[0].upper()}{provider_type[1:]}Provider"
                    )
                debug_logger.debug(f"Using default format: {module_path}.{class_name}")

            try:
                # Try to import module
                try:
                    provider_module = importlib.import_module(module_path)
                    debug_logger.debug(f"Successfully imported module: {module_path}")
                except ModuleNotFoundError:
                    logger.error(f"Module not found: {module_path}")
                    raise ImportError(f"Module not found: {module_path}")

                # Try to get class from module
                try:
                    provider_class = getattr(provider_module, class_name)
                    debug_logger.debug(f"Provider class found: {class_name}")
                except AttributeError:
                    logger.error(
                        f"Class {class_name} not found in module {module_path}"
                    )
                    raise AttributeError(
                        f"Class {class_name} not found in module {module_path}"
                    )

                # Register provider class for future use
                if module not in self._plugin_classes:
                    self._plugin_classes[module] = {}
                self._plugin_classes[module][provider_type] = provider_class

                # Create provider instance
                try:
                    debug_logger.debug(
                        f"Creating instance using from_config method with config: {config}"
                    )
                    provider = provider_class.from_config(**config)
                except (AttributeError, TypeError) as e:
                    debug_logger.warning(
                        f"Could not use from_config method: {e}, trying direct instantiation"
                    )
                    # Try direct instantiation if from_config is not available
                    provider = provider_class(**config)

                # Ensure plugin is initialized from YAML if it's a ProviderPlugin
                if hasattr(provider, "initialize_from_yaml"):
                    # Find and initialize from plugin.yaml
                    plugin_dir = f"plugins/{module}_{provider_type}"
                    yaml_path = f"{plugin_dir}/plugin.yaml"
                    try:
                        debug_logger.debug(
                            f"Initializing plugin from YAML: {yaml_path}"
                        )
                        provider.initialize_from_yaml(yaml_path)
                    except Exception as yaml_error:
                        debug_logger.warning(
                            f"Error initializing from YAML: {yaml_error}"
                        )

                return cast(BaseProvider, provider)
            except Exception as e:
                logger.exception(f"Error loading provider: {e}")
                raise ValidationError(f"Error loading provider '{provider_type}': {e}")

        except Exception as e:
            logger.error(f"Failed to create provider: {e}")
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


# Criar a instância global do plugin_manager
plugin_manager = PluginManager()
