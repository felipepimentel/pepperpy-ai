"""
Core configuration module for Pepperpy framework.
Handles dynamic loading of providers and configuration management.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar

import yaml
from pydantic import BaseModel, Field

from pepperpy.core.errors import ConfigError

T = TypeVar("T")


class ProviderConfig(BaseModel):
    """Base model for provider configuration."""

    type: str = Field(..., description="Provider type")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Provider configuration"
    )


class CapabilityConfig(BaseModel):
    """Base model for capability configuration."""

    default: ProviderConfig = Field(..., description="Default provider configuration")
    providers: Dict[str, ProviderConfig] = Field(
        default_factory=dict, description="Additional provider configurations"
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapabilityConfig":
        """Create CapabilityConfig from raw dictionary.

        Args:
            data: Raw configuration dictionary

        Returns:
            CapabilityConfig instance
        """
        default = data.get("default", {"type": "default", "config": {}})
        providers = {k: v for k, v in data.items() if k != "default"}
        return cls(default=default, providers=providers)


class PepperpyConfig(BaseModel):
    """Root configuration model."""

    llm: CapabilityConfig = Field(..., description="LLM capability configuration")
    content: CapabilityConfig = Field(
        ..., description="Content capability configuration"
    )
    synthesis: CapabilityConfig = Field(
        ..., description="Synthesis capability configuration"
    )
    memory: CapabilityConfig = Field(..., description="Memory capability configuration")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PepperpyConfig":
        """Create PepperpyConfig from raw dictionary.

        Args:
            data: Raw configuration dictionary

        Returns:
            PepperpyConfig instance
        """
        return cls(
            llm=CapabilityConfig.from_dict(data.get("llm", {})),
            content=CapabilityConfig.from_dict(data.get("content", {})),
            synthesis=CapabilityConfig.from_dict(data.get("synthesis", {})),
            memory=CapabilityConfig.from_dict(data.get("memory", {})),
        )


class Configuration:
    """Central configuration management for Pepperpy framework."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional path to configuration file. Defaults to ~/.pepperpy/config.yml
        """
        self.config_path = config_path or Path.home() / ".pepperpy" / "config.yml"
        self.config: Optional[PepperpyConfig] = None
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file, environment variables, or use defaults."""
        config_dict = {}

        # Load from file if exists
        if self.config_path.exists():
            with open(self.config_path) as f:
                config_dict = yaml.safe_load(f) or {}

        # Load from environment variables
        config_dict = self._load_env_vars(config_dict)

        # Use defaults if empty
        if not config_dict:
            config_dict = self._get_default_config()

        # Validate configuration
        try:
            self.config = PepperpyConfig.from_dict(config_dict)
        except Exception as e:
            raise ConfigError(f"Invalid configuration: {str(e)}")

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
        if not self.config:
            raise ConfigError("Configuration not loaded")

        capability_config = getattr(self.config, capability, None)
        if not capability_config:
            raise ConfigError(f"Capability {capability} not found in configuration")

        if name == "default":
            return capability_config.default.dict()

        provider_config = capability_config.providers.get(name)
        if not provider_config:
            raise ConfigError(
                f"Provider {capability}.{name} not found in configuration"
            )

        return provider_config.dict()

    def _load_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Environment variables take precedence over file configuration.
        Variables should be in the format: PEPPERPY_{CAPABILITY}_{PROVIDER}_{KEY}
        Example: PEPPERPY_LLM_DEFAULT_MODEL=gpt-4

        Args:
            config: Existing configuration dictionary

        Returns:
            Updated configuration dictionary
        """
        for key in os.environ:
            if not key.startswith("PEPPERPY_"):
                continue

            parts = key.lower().split("_")[1:]  # Remove PEPPERPY_ prefix
            if len(parts) < 3:
                continue

            capability, provider, *config_parts = parts
            config_key = "_".join(config_parts)
            value = os.environ[key]

            # Initialize nested dictionaries if they don't exist
            if capability not in config:
                config[capability] = {"default": {"type": provider, "config": {}}}
            if provider not in config[capability]:
                config[capability][provider] = {"type": provider, "config": {}}

            # Set configuration value
            config[capability][provider]["config"][config_key] = value

        return config

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
