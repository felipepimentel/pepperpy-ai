"""Base configuration module."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Optional, cast

from ..exceptions import ConfigurationError
from ..types import JsonDict


def _convert_to_date(value: Any, field_name: str) -> date:
    """Convert value to date.

    Args:
        value: Value to convert
        field_name: Name of the field being converted

    Returns:
        Converted date

    Raises:
        ConfigurationError: If value cannot be converted to date
    """
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ConfigurationError(f"Invalid date format for {field_name}", field=field_name)


@dataclass
class BaseConfig:
    """Base configuration class."""

    name: str
    version: str
    enabled: bool = True
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)
    created_at: date = field(default_factory=date.today)
    updated_at: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Validate configuration."""
        # Validate required fields
        required_fields = ["name", "version"]
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not value:
                raise ConfigurationError(
                    f"Missing required field: {field_name}",
                    field=field_name,
                )

        # Validate field types
        if not isinstance(self.name, str):
            raise ConfigurationError(
                f"Invalid type for name: {type(self.name)}, expected str",
                field="name",
            )

        if not isinstance(self.version, str):
            raise ConfigurationError(
                f"Invalid type for version: {type(self.version)}, expected str",
                field="version",
            )

        if not isinstance(self.enabled, bool):
            raise ConfigurationError(
                f"Invalid type for enabled: {type(self.enabled)}, expected bool",
                field="enabled",
            )

        if not isinstance(self.metadata, dict):
            raise ConfigurationError(
                f"Invalid type for metadata: {type(self.metadata)}, expected dict",
                field="metadata",
            )

        if not isinstance(self.settings, dict):
            raise ConfigurationError(
                f"Invalid type for settings: {type(self.settings)}, expected dict",
                field="settings",
            )

        # Convert dates
        self.created_at = _convert_to_date(self.created_at, "created_at")
        self.updated_at = _convert_to_date(self.updated_at, "updated_at")

    def to_dict(self) -> JsonDict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "BaseConfig":
        """Create configuration from dictionary.

        Args:
            data: Dictionary containing configuration values.

        Returns:
            New configuration instance.

        Raises:
            ConfigurationError: If required fields are missing or invalid.
        """
        required_fields = ["name", "version"]
        for field in required_fields:
            if field not in data:
                raise ConfigurationError(
                    f"Missing required field: {field}",
                    field=field,
                )

        return cls(
            name=str(data["name"]),
            version=str(data["version"]),
            enabled=bool(data.get("enabled", True)),
            metadata=cast(JsonDict, data.get("metadata", {})),
            settings=cast(JsonDict, data.get("settings", {})),
            created_at=date.fromisoformat(str(data.get("created_at", date.today().isoformat()))),
            updated_at=date.fromisoformat(str(data.get("updated_at", date.today().isoformat()))),
        )
