"""Configuration module for PepperPy.

This module provides configuration management functionality.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from pepperpy.core.utils import merge_configs, unflatten_dict, validate_type
from pepperpy.embeddings.base import EmbeddingProvider
from pepperpy.github import GitHubClient
from pepperpy.llm.base import LLMProvider
from pepperpy.rag.base import BaseProvider as RAGProvider

from .validation import ValidationError

logger = logging.getLogger(__name__)


class Config:
    """Configuration management class.

    This class handles loading, validating, and accessing configuration values
    from various sources including files, environment variables, and defaults.

    Args:
        config_path: Optional path to config file
        env_prefix: Optional prefix for environment variables
        defaults: Optional default configuration values
        **kwargs: Additional configuration values

    Example:
        >>> config = Config(
        ...     config_path="config.yaml",
        ...     env_prefix="APP_",
        ...     defaults={"debug": False},
        ...     api_key="abc123"
        ... )
        >>> print(config.get("api_key"))
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path, Dict[str, Any]]] = None,
        env_prefix: str = "PEPPERPY_",
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize configuration.

        Args:
            config_path: Optional path to config file or config dictionary
            env_prefix: Optional prefix for environment variables
            defaults: Optional default configuration values
            **kwargs: Additional configuration values

        Raises:
            ValidationError: If config file is invalid
        """
        self._config: Dict[str, Any] = {}
        self._env_prefix = env_prefix

        # Load defaults
        if defaults:
            validate_type(defaults, dict)
            self._config.update(defaults)

        # Load from file or dictionary
        if config_path:
            if isinstance(config_path, (str, Path)):
                self._load_file(config_path)
            elif isinstance(config_path, dict):
                self._config.update(config_path)
            else:
                raise ValidationError(f"Invalid config_path type: {type(config_path)}")

        # Load from environment
        self._load_env()

        # Load from kwargs
        self._config.update(kwargs)

    def _load_file(self, path: Union[str, Path]) -> None:
        """Load configuration from file.

        Args:
            path: Path to configuration file

        Raises:
            ValidationError: If file is invalid or cannot be read
        """
        try:
            path = Path(path)
            if not path.exists():
                raise ValidationError(f"Config file not found: {path}")

            with open(path) as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ValidationError("Config file must contain a dictionary")

            self._config.update(config)

        except Exception as e:
            raise ValidationError(f"Failed to load config file: {e}")

    def _load_env(self) -> None:
        """Load configuration from environment variables.

        Environment variables are converted from uppercase with underscores
        to lowercase with dots. For example:
            APP_DATABASE_URL -> database.url
        """
        if not self._env_prefix:
            return

        prefix = self._env_prefix.rstrip("_").upper() + "_"
        env_config = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert APP_DATABASE_URL to database.url
                config_key = key[len(prefix) :].lower().replace("_", ".")
                env_config[config_key] = value

        # Update config with flattened env vars
        if env_config:
            self._config.update(unflatten_dict(env_config))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config.get("database.url", "sqlite:///db.sqlite3")
        """
        try:
            current = self._config
            for part in key.split("."):
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set

        Example:
            >>> config.set("database.url", "postgres://localhost/db")
        """
        config = unflatten_dict({key: value})
        self._config = merge_configs(self._config, config)

    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with dictionary.

        Args:
            config: Configuration dictionary to merge

        Example:
            >>> config.update({"debug": True, "api": {"timeout": 30}})
        """
        validate_type(config, dict)
        self._config = merge_configs(self._config, config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration dictionary

        Example:
            >>> config_dict = config.to_dict()
            >>> print(config_dict["database"]["url"])
        """
        return dict(self._config)

    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dictionary syntax.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            KeyError: If key not found

        Example:
            >>> api_key = config["api_key"]
        """
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value using dictionary syntax.

        Args:
            key: Configuration key
            value: Value to set

        Example:
            >>> config["api_key"] = "new_key"
        """
        self.set(key, value)

    def load_llm_provider(self) -> LLMProvider:
        """Load LLM provider from configuration.

        Returns:
            Configured LLM provider instance
        """
        provider_type = self.get("llm.provider", "openrouter")
        provider_config = self.get("llm.config", {})
        provider = self._create_provider(LLMProvider, provider_type, **provider_config)
        return provider

    def load_embedding_provider(self) -> EmbeddingProvider:
        """Load embedding provider from configuration.

        Returns:
            Configured embedding provider instance
        """
        provider_type = self.get("embeddings.provider", "openai")
        provider_config = self.get("embeddings.config", {})
        provider = self._create_provider(
            EmbeddingProvider, provider_type, **provider_config
        )
        return provider

    def load_rag_provider(
        self, collection_name: str, persist_directory: str
    ) -> RAGProvider:
        """Load RAG provider from configuration.

        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist data

        Returns:
            Configured RAG provider instance
        """
        provider_type = self.get("rag.provider", "chroma")
        provider_config = self.get("rag.config", {})
        provider = self._create_provider(
            RAGProvider,
            provider_type,
            collection_name=collection_name,
            persist_directory=persist_directory,
            **provider_config,
        )
        return provider

    def load_github_client(self) -> GitHubClient:
        """Load GitHub client from configuration.

        Returns:
            Configured GitHub client instance
        """
        token = self.get("tools.github.api_key")
        if not token:
            token = os.environ.get("PEPPERPY_TOOLS__GITHUB_API_KEY")
        if not token:
            raise ValidationError("GitHub API token is required")
        return GitHubClient(api_key=token)

    def _create_provider(
        self, provider_class: Any, provider_type: str, **kwargs: Any
    ) -> Any:
        """Create a provider instance.

        Args:
            provider_class: Provider class to instantiate
            provider_type: Type of provider to create
            **kwargs: Additional configuration options

        Returns:
            Provider instance
        """
        try:
            # Import provider module
            module_name = f"pepperpy.{provider_class.__module__.split('.')[-2]}.providers.{provider_type}"
            module = __import__(module_name, fromlist=[""])

            # Get provider class
            provider_class_name = f"{provider_type.title()}Provider"
            provider_class = getattr(module, provider_class_name)

            # Create instance
            return provider_class(**kwargs)
        except (ImportError, AttributeError) as e:
            raise ValidationError(f"Failed to load provider {provider_type}: {e}")
