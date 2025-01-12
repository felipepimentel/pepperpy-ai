"""Base configuration module."""

from datetime import date
from typing import ClassVar, TypeVar, cast

from ..exceptions import ConfigurationError
from ..types import JsonDict

T = TypeVar("T", bound="BaseConfig")


def _convert_to_date(value: str | date, field_name: str) -> date:
    """Convert value to date.

    Args:
        value: Value to convert.
        field_name: Name of the field being converted.

    Returns:
        date: Converted date value.

    Raises:
        ConfigurationError: If value cannot be converted to date.
    """
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as e:
        raise ConfigurationError(f"Invalid {field_name}: {value}") from e


class BaseConfig:
    """Base class for configuration objects.

    This class provides the foundation for implementing different configuration
    objects. Each configuration class can implement its own validation and
    initialization logic.

    Attributes:
        name: Configuration name
        version: Configuration version
        enabled: Whether the configuration is enabled
        created_at: Creation date
        updated_at: Last update date
    """

    _required_fields: ClassVar[list[str]] = ["name", "version"]

    def __init__(
        self,
        name: str,
        version: str,
        enabled: bool = True,
        created_at: str | date | None = None,
        updated_at: str | date | None = None,
    ) -> None:
        """Initialize configuration.

        Args:
            name: Configuration name.
            version: Configuration version.
            enabled: Whether the configuration is enabled.
            created_at: Creation date.
            updated_at: Last update date.
        """
        self.name = name
        self.version = version
        self.enabled = enabled
        self.created_at = (
            _convert_to_date(created_at, "created_at") if created_at else None
        )
        self.updated_at = (
            _convert_to_date(updated_at, "updated_at") if updated_at else None
        )

    @classmethod
    def from_dict(cls, data: JsonDict) -> "BaseConfig":
        """Create configuration from dictionary.

        Args:
            data: Dictionary containing configuration data.

        Returns:
            BaseConfig: Created configuration object.

        Raises:
            ConfigurationError: If required fields are missing.
        """
        missing_fields = [
            field for field in cls._required_fields if field not in data
        ]
        if missing_fields:
            raise ConfigurationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        name = cast(str, data["name"])
        version = cast(str, data["version"])
        enabled = cast(bool, data.get("enabled", True))
        created_at = cast(str | None, data.get("created_at"))
        updated_at = cast(str | None, data.get("updated_at"))

        return cls(
            name=name,
            version=version,
            enabled=enabled,
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> JsonDict:
        """Convert configuration to dictionary.

        Returns:
            JsonDict: Dictionary representation of configuration.
        """
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
