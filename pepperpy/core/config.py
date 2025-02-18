"""
Core configuration module for Pepperpy framework.
Handles dynamic loading of providers and configuration management.
"""

import importlib
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

import yaml

from pepperpy.core.errors import ConfigError

T = TypeVar("T")


class Configuration:
    """Central configuration management for Pepperpy framework."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional path to configuration file. Defaults to ~/.pepperpy/config.yml
        """
        self.config_path = config_path or Path.home() / ".pepperpy" / "config.yml"
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file or use defaults."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.providers = yaml.safe_load(f) or {}
        else:
            self.providers = self._get_default_config()

    def get_provider(self, capability: str, name: str = "default") -> Dict[str, Any]:
        """Get provider configuration.

        Args:
            capability: Capability name (e.g. 'llm', 'content')
            name: Provider name within capability. Defaults to 'default'

        Returns:
            Provider configuration dictionary

        Raises:
            ConfigError: If provider configuration is not found
        """
        capability_config = self.providers.get(capability, {})
        provider_config = capability_config.get(name)

        if not provider_config:
            raise ConfigError(
                f"Provider {capability}.{name} not found in configuration"
            )

        return provider_config

    def load_provider(self, capability: str, name: str, base_class: Type[T]) -> T:
        """Dynamically load and instantiate a provider.

        Args:
            capability: Capability name (e.g. 'llm', 'content')
            name: Provider name within capability
            base_class: Base class that provider must implement

        Returns:
            Instantiated provider

        Raises:
            ConfigError: If provider cannot be loaded or instantiated
        """
        config = self.get_provider(capability, name)
        provider_type = config["type"]
        provider_config = config.get("config", {})

        try:
            # Load provider module
            module_path = f"pepperpy.{capability}.providers.{provider_type}"
            module = importlib.import_module(module_path)

            # Get provider class
            provider_class = getattr(module, f"{provider_type.title()}Provider")

            # Validate provider class
            if not issubclass(provider_class, base_class):
                raise ConfigError(
                    f"Provider class {provider_class.__name__} does not implement {base_class.__name__}"
                )

            # Instantiate provider
            return provider_class(**provider_config)

        except (ImportError, AttributeError) as e:
            raise ConfigError(f"Failed to load provider {capability}.{name}: {str(e)}")

    def _get_default_config(self) -> Dict[str, Dict[str, Any]]:
        """Get default configuration when no config file exists."""
        return {
            "llm": {
                "default": {
                    "type": "openai",
                    "config": {"model": "gpt-3.5-turbo", "temperature": 0.7},
                }
            },
            "content": {
                "default": {
                    "type": "rss",
                    "config": {
                        "sources": ["https://news.google.com/rss"],
                        "language": "pt-BR",
                    },
                }
            },
            "synthesis": {
                "default": {
                    "type": "openai",
                    "config": {"voice": "alloy", "model": "tts-1"},
                }
            },
            "memory": {
                "default": {"type": "local", "config": {"path": "~/.pepperpy/memory"}}
            },
        }
