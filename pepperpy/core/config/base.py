"""Base configuration module for PepperPy.

This module provides the core configuration functionality for PepperPy,
including configuration providers, validation, and management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


@dataclass
class ConfigValidationError:
    """Configuration validation error."""

    field: str
    message: str
    value: Any


class ConfigProvider(ABC):
    """Abstract base class for configuration providers."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get configuration value by key.

        Args:
            key: Configuration key.

        Returns:
            Configuration value or None if not found.
        """

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key.
        """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if configuration key exists.

        Args:
            key: Configuration key.

        Returns:
            True if key exists, False otherwise.
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear all configuration values."""


class DictConfigProvider(ConfigProvider):
    """Dictionary-based configuration provider."""

    def __init__(self) -> None:
        """Initialize provider."""
        self._config: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get configuration value by key.

        Args:
            key: Configuration key.

        Returns:
            Configuration value or None if not found.
        """
        return self._config.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        self._config[key] = value

    def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key.
        """
        self._config.pop(key, None)

    def exists(self, key: str) -> bool:
        """Check if configuration key exists.

        Args:
            key: Configuration key.

        Returns:
            True if key exists, False otherwise.
        """
        return key in self._config

    def clear(self) -> None:
        """Clear all configuration values."""
        self._config.clear()


class ConfigValidator:
    """Configuration validator."""

    def __init__(self, model_type: Type[T]) -> None:
        """Initialize validator.

        Args:
            model_type: Pydantic model type for validation.
        """
        self._model_type = model_type

    def validate(self, config: Dict[str, Any]) -> List[ConfigValidationError]:
        """Validate configuration.

        Args:
            config: Configuration dictionary.

        Returns:
            List of validation errors.
        """
        try:
            self._model_type(**config)
            return []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(
                    ConfigValidationError(
                        field=field,
                        message=error["msg"],
                        value=error.get("input"),
                    )
                )
            return errors


class ConfigManager:
    """Configuration manager."""

    def __init__(self, provider: ConfigProvider) -> None:
        """Initialize manager.

        Args:
            provider: Configuration provider.
        """
        self._provider = provider
        self._validators: Dict[str, ConfigValidator] = {}

    def register_validator(self, prefix: str, validator: ConfigValidator) -> None:
        """Register configuration validator.

        Args:
            prefix: Configuration prefix.
            validator: Configuration validator.
        """
        self._validators[prefix] = validator

    def unregister_validator(self, prefix: str) -> None:
        """Unregister configuration validator.

        Args:
            prefix: Configuration prefix.
        """
        self._validators.pop(prefix, None)

    def validate(self) -> List[ConfigValidationError]:
        """Validate all configuration.

        Returns:
            List of validation errors.
        """
        errors = []
        for prefix, validator in self._validators.items():
            config = {}
            for key, value in self._get_config_by_prefix(prefix).items():
                config[key[len(prefix) + 1 :]] = value
            errors.extend(validator.validate(config))
        return errors

    def get(self, key: str) -> Optional[Any]:
        """Get configuration value by key.

        Args:
            key: Configuration key.

        Returns:
            Configuration value or None if not found.
        """
        return self._provider.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        self._provider.set(key, value)

    def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key.
        """
        self._provider.delete(key)

    def exists(self, key: str) -> bool:
        """Check if configuration key exists.

        Args:
            key: Configuration key.

        Returns:
            True if key exists, False otherwise.
        """
        return self._provider.exists(key)

    def clear(self) -> None:
        """Clear all configuration values."""
        self._provider.clear()

    def _get_config_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """Get configuration values by prefix.

        Args:
            prefix: Configuration prefix.

        Returns:
            Dictionary of configuration values.
        """
        result = {}
        for key, value in self._provider._config.items():  # type: ignore
            if key.startswith(f"{prefix}."):
                result[key] = value
        return result
